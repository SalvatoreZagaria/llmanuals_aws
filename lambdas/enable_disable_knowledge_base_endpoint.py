import os
import json
import logging

import boto3


logger = logging.getLogger()
logger.setLevel("INFO")


def lambda_handler(event, context):
    user_id = event['requestContext']['authorizer']['claims']['sub']

    if event['resource'] == '/api/admin/knowledge/enable':
        state = 'ENABLED'
    elif event['resource'] == '/api/admin/knowledge/disable':
        state = 'DISABLED'
    else:
        logger.error(f'Unhandled case - {event["resource"]}')
        return {
            'statusCode': 500,
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

    bedrock_client = boto3.client('bedrock-agent', region_name=os.getenv('AWS_REGION', 'eu-west-2'))

    response = bedrock_client.get_agent_knowledge_base(
        agentId=user_data['agent_id'],
        agentVersion=user_data['agent_version'],
        knowledgeBaseId=user_data['knowledge_base'],
    )

    if response['agentKnowledgeBase']['knowledgeBaseState'] == state:
        return {
            'statusCode': 409,
            'body': json.dumps({'message': f'Conflict: Knowledge base is already {state}'})
        }

    lambda_client = boto3.client('lambda', region_name=os.getenv('AWS_REGION', 'eu-west-2'))
    lambda_client.invoke(
        FunctionName='enable_disable_knowledge_base',
        InvocationType='Event',
        Payload=json.dumps(
            {
                'body': {
                    'user_data': user_data,
                    'kb_state': state,
                }
            }
        )
    )

    return {
        'statusCode': 202
    }
