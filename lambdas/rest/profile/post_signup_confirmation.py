import os
import json

import boto3


def lambda_handler(event, context):
    user_attributes = event['request']['userAttributes']
    client = boto3.client('lambda', region_name=os.getenv('AWS_REGION', 'eu-west-2'))
    client.invoke(
        FunctionName='setup_user',
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

    return event
