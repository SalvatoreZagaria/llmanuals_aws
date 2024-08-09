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
            'headers': {
                "Access-Control-Allow-Origin": "*"
            },
            'body': json.dumps({'message': 'Bad request - no payload'})
        }
    body = json.loads(body)
    urls = body.get('urls') or []
    if not (urls and isinstance(urls, list) and all([u and isinstance(u, str) for u in urls])):
        return {
            'statusCode': 400,
            'headers': {
                "Access-Control-Allow-Origin": "*"
            },
            'body': json.dumps({'message': 'Bad request - invalid urls'})
        }
    urls = set(urls)

    response = table.get_item(
        Key={
            'id': user_id
        }
    )
    user_data = response['Item']

    kb_id = user_data['knowledge_base']
    data_source_id = user_data['data_source_web_crawler']

    data_source = bedrock_client.get_data_source(
        dataSourceId=data_source_id,
        knowledgeBaseId=kb_id
    )
    current_urls = {
        su['url'] for su in
        data_source['dataSource']['dataSourceConfiguration']['webConfiguration']['sourceConfiguration']
        ['urlConfiguration']['seedUrls']
    }

    not_found_urls = urls - current_urls
    if not_found_urls:
        return {
            'statusCode': 400,
            'headers': {
                "Access-Control-Allow-Origin": "*"
            },
            'body': json.dumps(
                {
                    'message': 'Bad request - urls not found in data source',
                    'urls': list(not_found_urls)
                }
            )
        }

    new_urls = current_urls - urls
    if not new_urls:
        return {
            'statusCode': 400,
            'headers': {
                "Access-Control-Allow-Origin": "*"
            },
            'body': json.dumps(
                {
                    'message': 'Bad request - cannot remove all urls from data source. '
                               'Please use [DELETE] /api/admin/knowledge/web/delete'
                }
            )
        }

    try:
        update_urls(user_id, kb_id, data_source_id, new_urls)
    except (bedrock_client.exceptions.ValidationException, UserError) as e:
        logger.warning(f'WEB DATA SOURCE - Validation exception for {user_id}')
        logger.warning(f'KNOWLEDGE BASE ID: {kb_id}')
        logger.warning(f'URLS: {json.dumps(new_urls)}')
        return {
            'statusCode': 400,
            'headers': {
                "Access-Control-Allow-Origin": "*"
            },
            'body': json.dumps(
                {'message': f'Bad request - {e}'})
        }
    except:
        tb = traceback.format_exc()
        logger.error(f'WEB DATA SOURCE - Validation exception for {user_id}')
        logger.error(f'KNOWLEDGE BASE ID: {kb_id}')
        logger.error(f'URLS: {json.dumps(new_urls)}')
        logger.error(tb)
        return {
            'statusCode': 500,
            'headers': {
                "Access-Control-Allow-Origin": "*"
            },
            'body': json.dumps(
                {'message': 'Unexpected error. Please contact the administrator.'})
        }


def update_urls(user_id: str, kb_id: str, data_source_id: str, urls: t.List[str]):
    kwargs = {
        'dataSourceId': data_source_id,
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

    bedrock_client.update_data_source(**kwargs)
