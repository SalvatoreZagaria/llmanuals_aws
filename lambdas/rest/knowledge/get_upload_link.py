import re
import os
import json

import boto3


def is_valid_s3_key(key: str) -> bool:
    if not key or len(key) > 1024:
        return False

    pattern = re.compile(r'[&$@=;/+:,?\x00-\x1F\x7F\\{}^%`"\[\]~<>#|]')
    return not pattern.search(key)


def lambda_handler(event, context):
    user_id = event['requestContext']['authorizer']['claims']['sub']

    filename = event.get('queryStringParameters', {}).get('fileName')
    if not is_valid_s3_key(filename):
        return {
            'statusCode': 400,
            'headers': {
                "Access-Control-Allow-Origin": "*"
            },
            'body': json.dumps(
                {'message': 'Bad request - fileName query parameter required and should not contain special characters '
                            'such as [&$@=;/+:,?\x00-\x1F\x7F\{}^%`"[]~<>#|]'}
            )
        }

    bucket_name = os.getenv('BUCKET_NAME', 'llmanuals-knowledge-source')
    expires_in = int(os.getenv('PRESIGNED_URL_EXPIRATION_TIME', 600))

    s3_client = boto3.client('s3', region_name=os.getenv('AWS_REGION', 'eu-west-2'))
    response = s3_client.generate_presigned_url('put_object',
                                                Params={'Bucket': bucket_name,
                                                        'Key': f'{user_id}/{filename}'},
                                                ExpiresIn=expires_in)

    return {
        'statusCode': 200,
        'headers': {
            "Access-Control-Allow-Origin": "*"
        },
        'body': json.dumps(
            {
                'presignedUrl': response,
                'expiresIn': expires_in
            }
        )
    }
