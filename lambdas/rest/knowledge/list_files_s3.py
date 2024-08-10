import os
import json

import boto3


def lambda_handler(event, context):
    user_id = event['requestContext']['authorizer']['claims']['sub']

    bucket_name = os.getenv('BUCKET_NAME', 'llmanuals-knowledge-source')
    s3_client = boto3.client('s3', region_name=os.getenv('AWS_REGION', 'eu-west-2'))

    continuation_token = None
    objects = set()

    prefix = f'{user_id}/'
    kwargs = {
        'Bucket': bucket_name,
        'Prefix': prefix
    }
    while True:
        if continuation_token:
            kwargs['ContinuationToken'] = continuation_token
        response = s3_client.list_objects_v2(**kwargs)
        objects.update({o['Key'].lstrip(prefix) for o in response.get('Contents', [])})

        if not response.get('IsTruncated'):
            break
        continuation_token = response.get('NextContinuationToken')

    objects = [o for o in objects if o]
    return {
        'statusCode': 200,
        'headers': {
            "Access-Control-Allow-Origin": "*"
        },
        'body': json.dumps(
            {
                'files': objects
            }
        )
    }
