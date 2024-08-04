import os
import json
import logging
import traceback
import typing as t

import boto3


logger = logging.getLogger()
logger.setLevel("INFO")

bedrock_client = boto3.client('bedrock-agent', region_name=os.getenv('AWS_REGION', 'eu-west-2'))
dynamodb_client = boto3.resource('dynamodb', region_name=os.getenv('AWS_REGION', 'eu-west-2'))
table = dynamodb_client.Table('user')


class UserError(Exception):
    pass


def lambda_handler(event, context):
    user_id = event['requestContext']['authorizer']['claims']['sub']

    body = event['body']
    if not body:
        return {
            'statusCode': 400,
            'body': json.dumps({'message': 'Bad request - no payload'})
        }
    body = json.loads(body)
    urls = body.get('urls') or []
    create_data_source_if_not_exists = body.get('createDataSourceIfNotExists', True)
    if not (urls and isinstance(urls, list) and len(urls) <= 10 and all([u and isinstance(u, str) for u in urls])):
        return {
            'statusCode': 400,
            'body': json.dumps({'message': 'Bad request - urls must be provided and it should be '
                                           'no longer than 10 elements'})
        }

    response = table.get_item(
        Key={
            'id': user_id
        }
    )
    user_data = response['Item']

    kb_id = user_data['knowledge_base']
    data_source_id = user_data['data_source_web_crawler']
    try:
        if not user_data['data_source_web_crawler']:
            if not create_data_source_if_not_exists:
                return {
                    'statusCode': 404,
                    'body': json.dumps(
                        {'message': 'Web data source not found'})
                }
            data_source_id = create_data_source(user_id, kb_id, urls)
            store_data_source_info(user_id, data_source_id)
        else:
            add_urls_to_data_source(user_id, kb_id, data_source_id, urls)
    except (bedrock_client.exceptions.ValidationException, UserError) as e:
        logger.warning(f'WEB DATA SOURCE - Validation exception for {user_id}')
        logger.warning(f'KNOWLEDGE BASE ID: {kb_id}')
        logger.warning(f'URLS: {json.dumps(urls)}')
        return {
            'statusCode': 400,
            'body': json.dumps(
                {'message': f'Bad request - {e}'})
        }
    except:
        tb = traceback.format_exc()
        logger.error(tb)
        return {
            'statusCode': 500,
            'body': json.dumps(
                {'message': 'Unexpected error. Please contact the administrator.'})
        }


def get_kwargs(user_id: str, kb_id: str, urls: t.List[str]):
    return {
        'dataDeletionPolicy': 'DELETE',
        'dataSourceConfiguration': {
            'type': 'WEB',
            'webConfiguration': {
                'crawlerConfiguration': {
                    'scope': 'HOST_ONLY'
                },
                'sourceConfiguration': {
                    'urlConfiguration': {
                        'seedUrls': [{'url': u} for u in urls]
                    }
                }
            }
        },
        'knowledgeBaseId': kb_id,
        'name': f'{user_id} - WEB',
        'vectorIngestionConfiguration': {
            'chunkingConfiguration': {
                'chunkingStrategy': 'FIXED_SIZE',
                'fixedSizeChunkingConfiguration': {
                    'maxTokens': 800,
                    'overlapPercentage': 20
                }
            }
        }
    }


def create_data_source(user_id: str, kb_id: str, urls: t.List[str]):
    kwargs = get_kwargs(user_id, kb_id, urls)
    response = bedrock_client.create_data_source(**kwargs)
    return response['dataSource']['dataSourceId']


def add_urls_to_data_source(user_id: str, kb_id: str, data_source_id: str, urls: t.List[str]):
    data_source = bedrock_client.get_data_source(
        dataSourceId=data_source_id,
        knowledgeBaseId=kb_id
    )
    current_urls = [
        su['url'] for su in
        data_source['dataSource']['dataSourceConfiguration']['webConfiguration']['sourceConfiguration']
        ['urlConfiguration']['seedUrls']
    ]

    urls = list(set(urls + current_urls))
    if len(urls) > 10:
        raise UserError('Web data source can hold no more than 10 urls')

    kwargs = get_kwargs(user_id, kb_id, urls)
    kwargs['dataSourceId'] = data_source_id
    bedrock_client.update_data_source(**kwargs)


def store_data_source_info(user_id: str, data_source_id: str):
    table.update_item(
        Key={
            'id': user_id
        },
        UpdateExpression="SET data_source_web_crawler = :data_source_id",
        ExpressionAttributeValues={
            ':data_source_id': data_source_id
        }
    )
