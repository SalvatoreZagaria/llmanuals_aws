import os
import json

import boto3


def lambda_handler(event, context):
    user_id = event['requestContext']['authorizer']['claims']['sub']

    client = boto3.client('lambda', region_name=os.getenv('AWS_REGION', 'eu-west-2'))
    client.invoke(
        FunctionName='delete_organization_profile',
        InvocationType='Event',
        Payload=json.dumps(
            {
                'body': {
                    'sub': user_id
                }
            }
        )
    )

    return {
        'statusCode': 202,
        'body': json.dumps({
            'message': 'Deleting profile...',
        })
    }
