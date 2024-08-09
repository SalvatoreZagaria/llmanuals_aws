import os
import json
import logging
import traceback

import boto3


logger = logging.getLogger()
logger.setLevel("INFO")


def lambda_handler(event, context):
    user_id = event['requestContext']['authorizer']['claims']['sub']

    if event['resource'] == '/api/admin/knowledge/static/sync':
        source_kind = 'STATIC'
        data_source_key = 'data_source_s3'
    elif event['resource'] == '/api/admin/knowledge/web/sync':
        source_kind = 'WEB'
        data_source_key = 'data_source_web_crawler'
    else:
        logger.error(f'Unhandled case - {event["resource"]}')
        return {
            'statusCode': 500,
            'headers': {
                "Access-Control-Allow-Origin": "*"
            },
            'body': json.dumps({'message': 'Server error'})
        }

    dynamodb_client = boto3.resource('dynamodb', region_name=os.getenv('AWS_REGION', 'eu-west-2'))
    table = dynamodb_client.Table('user')
    response = table.get_item(
        Key={
            'id': user_id
        }
    )
    user_data = response['Item']
    kb_id = user_data['knowledge_base']
    data_source_id = user_data[data_source_key]
    if not data_source_id:
        return {
            'statusCode': 404,
            'headers': {
                "Access-Control-Allow-Origin": "*"
            },
            'body': json.dumps({'message': f'No {source_kind} source data found. You need to create one first.'})
        }

    bedrock_client = boto3.client('bedrock-agent', region_name=os.getenv('AWS_REGION', 'eu-west-2'))

    try:
        jobs_response = bedrock_client.list_ingestion_jobs(
            dataSourceId=data_source_id,
            knowledgeBaseId=kb_id,
            filters=[
                {
                    'attribute': 'STATUS',
                    'operator': 'EQ',
                    'values': [
                        'STARTING', 'IN_PROGRESS'
                    ]
                },
            ],
            maxResults=1,
            sortBy={
                'attribute': 'STARTED_AT',
                'order': 'DESCENDING'
            }
        )
        if jobs_response['ingestionJobSummaries']:
            return {
                'statusCode': 503,
                'headers': {
                    "Access-Control-Allow-Origin": "*"
                },
                'body': json.dumps({
                    'message': 'Another synchronization job is still ongoing.',
                    'statusLocation': '/api/admin/agent/status'
                })
            }
        bedrock_client.start_ingestion_job(
            clientToken=user_id,
            dataSourceId=data_source_id,
            knowledgeBaseId=kb_id
        )
        return {
            'statusCode': 202,
            'headers': {
                "Access-Control-Allow-Origin": "*"
            },
            'body': json.dumps({
                'message': 'Synchronization job started.',
                'statusLocation': '/api/admin/agent/status'
            })
        }
    except:
        tb = traceback.format_exc()
        logger.error(tb)
        return {
            'statusCode': 500,
            'headers': {
                "Access-Control-Allow-Origin": "*"
            },
            'body': json.dumps(
                {'message': 'Unexpected error. Please contact the administrator.'})
        }
