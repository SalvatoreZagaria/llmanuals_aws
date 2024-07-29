import os
import json

import boto3


def lambda_handler(event, context):
    user_id = event['requestContext']['authorizer']['claims']['sub']
    body = event['body']
    if not body:
        return {
            'statusCode': 400,
            'body': json.dumps({'message': 'Bad request - no payload'})
        }
    body = json.loads(body)
    organization_name = None
    if 'organization_name' in body:
        organization_name = body['organization_name']
        if not (organization_name and isinstance(organization_name, str) and
                3 <= len(organization_name) <= 100):
            return {
                'statusCode': 400,
                'body': json.dumps({'message': 'Bad request - organization_name must be a string between '
                                               '3 and 100 characters'})
            }
    organization_description = None
    if 'organization_description' in body:
        organization_description = body['organization_description']
        if not (organization_description and isinstance(organization_description, str) and
                len(organization_description) <= 1000):
            return {
                'statusCode': 400,
                'body': json.dumps({'message': 'Bad request - organization_description must be a string with maximum '
                                               'length of 1000 characters'})
            }

    if not any((organization_name, organization_description)):
        return {
            'statusCode': 400,
            'body': json.dumps({'message': 'Bad request - one of [organization_name, organization_description] '
                                           'required'})
        }

    client = boto3.client('lambda', region_name=os.getenv('AWS_REGION', 'eu-west-2'))

    response = client.invoke(
        FunctionName='agent_status',
        InvocationType='RequestResponse',
        Payload=json.dumps(event)
    )
    status_response = json.loads(response['Payload'].read().decode('utf-8'))
    if status_response['statusCode'] != 200:
        return {
            'statusCode': status_response['statusCode'],
            'body': status_response['body']
        }
    status_body = json.loads(status_response['body'])
    if not status_body['isAgentReady']:
        return {
            'statusCode': 423,
            'body': json.dumps({
                'message': 'Agent is busy, try later',
                'statusLocation': '/api/admin/agent/status'
            })
        }
    if status_body['agentError']:
        return {
            'statusCode': 500,
            'body': json.dumps({
                'message': 'Agent is in error state. Please contact an administrator.'
            })
        }

    client.invoke(
        FunctionName='update_organization',
        InvocationType='Event',
        Payload=json.dumps(
            {
                'body': {
                    'sub': user_id,
                    'organization_name': organization_name,
                    'organization_description': organization_description
                }
            }
        )
    )

    return {
        'statusCode': 202,
        'body': json.dumps({
            'message': 'Updating the agent',
            'statusLocation': '/api/admin/agent/status'
        })
    }
