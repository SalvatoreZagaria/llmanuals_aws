import os
import json

import boto3


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
    file_names = body.get('fileNames')
    if not (file_names and isinstance(file_names, list) and all([f and isinstance(f, str) for f in file_names])):
        return {
            'statusCode': 400,
            'headers': {
                "Access-Control-Allow-Origin": "*"
            },
            'body': json.dumps({'message': 'Bad request - invalid fileNames'})
        }

    bucket_name = os.getenv('BUCKET_NAME', 'llmanuals-knowledge-source')
    s3_client = boto3.client('s3', region_name=os.getenv('AWS_REGION', 'eu-west-2'))

    response = s3_client.delete_objects(
        Bucket=bucket_name,
        Delete={
            'Objects': [
                {
                    'Key': f'{user_id}/{f}',
                } for f in file_names
            ]
        }
    )

    return {
        'statusCode': 200,
        'headers': {
            "Access-Control-Allow-Origin": "*"
        },
        'body': json.dumps(
            {
                'deleted': [{'Key': d['Key']} for d in response.get('Deleted') or []],
                'errors': [{'Key': e['Key'], 'Code': e['Code'], 'Message': e['Message']}
                           for e in response.get('Errors') or []]
            }
        )
    }
