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
            'message': 'Unexpected error. Please contact the administrator.'
        }
    user = response['Item']
    agent_id = user['agent_id']

    bedrock_client = boto3.client('bedrock-agent', region_name=os.getenv('AWS_REGION', 'eu-west-2'))
    try:
        response = bedrock_client.get_agent(
            agentId=agent_id
        )
    except bedrock_client.exceptions.ResourceNotFoundException:
        return {
            'statusCode': 500,
            'message': 'Agent not found. Please contact the administrator.'
        }

    agent_status = response['agent']['agentStatus']

    return {
        'statusCode': 200,
        'body': json.dumps({
            'agentStatus': agent_status,
            'isAgentReady': agent_status == 'PREPARED',
            'agentError': agent_status == 'FAILED'
        })
    }
