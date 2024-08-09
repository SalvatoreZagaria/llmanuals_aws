import os
import json
import logging

import boto3


logger = logging.getLogger()
logger.setLevel("INFO")


def lambda_handler(event, context):
    user_id = event['requestContext']['authorizer']['claims']['sub']

    dynamodb_client = boto3.resource('dynamodb', region_name=os.getenv('AWS_REGION', 'eu-west-2'))
    table = dynamodb_client.Table('user')
    try:
        response = table.get_item(
            Key={
                'id': user_id
            }
        )
    except dynamodb_client.exceptions.ResourceNotFoundException:
        logger.error(f'User not found in DynamoDB - USER ID: {user_id}')
        return {
            'statusCode': 500,
            'headers': {
                "Access-Control-Allow-Origin": "*"
            },
            'body': json.dumps({
                'message': 'Unexpected error. Please contact the administrator.'
            })
        }
    user = response['Item']
    agent_id = user['agent_id']
    agent_version = user['agent_version']
    knowledge_base_id = user['knowledge_base']

    bedrock_client = boto3.client('bedrock-agent', region_name=os.getenv('AWS_REGION', 'eu-west-2'))
    try:
        response = bedrock_client.get_agent(
            agentId=agent_id
        )
    except bedrock_client.exceptions.ResourceNotFoundException:
        return {
            'statusCode': 500,
            'headers': {
                "Access-Control-Allow-Origin": "*"
            },
            'body': json.dumps({
                'message': 'Agent not found. Please contact the administrator.'
            })
        }

    agent_status = response['agent']['agentStatus']

    kb_response = bedrock_client.get_agent_knowledge_base(
        agentId=agent_id,
        agentVersion=agent_version,
        knowledgeBaseId=knowledge_base_id
    )

    data_sources = {}
    for key, ds in zip(('static', 'web'), ('data_source_s3', 'data_source_web_crawler')):
        if not user[ds]:
            continue
        data_sources[key] = {}
        jobs_response = bedrock_client.list_ingestion_jobs(
            dataSourceId=user[ds],
            knowledgeBaseId=knowledge_base_id,
            maxResults=1,
            sortBy={
                'attribute': 'STARTED_AT',
                'order': 'DESCENDING'
            }
        )
        if not jobs_response['ingestionJobSummaries']:
            data_sources[key]['status'] = 'NOT SYNCHRONISED'
        else:
            data_sources[key]['status'] = jobs_response['ingestionJobSummaries'][0]['status']
            data_sources[key]['stats'] = jobs_response['ingestionJobSummaries'][0]['statistics']

    return {
        'statusCode': 200,
        'headers': {
            "Access-Control-Allow-Origin": "*"
        },
        'body': json.dumps({
            'agent': {
                'agentStatus': agent_status,
                'isAgentReady': agent_status == 'PREPARED',
                'agentError': agent_status == 'FAILED'
            },
            'knowledge': {
                'knowledgeBaseStatus': kb_response['agentKnowledgeBase']['knowledgeBaseState'],
                'dataSources': data_sources
            }
        })
    }
