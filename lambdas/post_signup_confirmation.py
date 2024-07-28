import os
import json

import boto3


def lambda_handler(event, context):
    user_attributes = event['request']['userAttributes']
    client = boto3.client('lambda', region_name=os.getenv('AWS_REGION', 'eu-west-2'))
    client.invoke(
        FunctionName='prepare_agent',
        InvocationType='Event',
        Payload=json.dumps(
            {
                'body': {
                    'sub': user_attributes['sub'],
                    'organization_name': user_attributes['custom:organization_name']
                }
            }
        )
    )
    event.setdefault('response', {})
    event['response'].update({
        'statusCode': 202,
        'message': 'Preparing the agent',
        'statusLocation': '/api/admin/agent/status'
    })

    return event
