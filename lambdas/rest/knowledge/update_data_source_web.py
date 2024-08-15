import os
import json
import logging

import boto3


logger = logging.getLogger()
logger.setLevel("INFO")

bedrock_client = boto3.client('bedrock-agent', region_name=os.getenv('AWS_REGION', 'eu-west-2'))
dynamodb_client = boto3.resource('dynamodb', region_name=os.getenv('AWS_REGION', 'eu-west-2'))
table = dynamodb_client.Table('user')


class UserError(Exception):
    pass


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
    urls = body.get('urls') or []
    if not (urls and isinstance(urls, list) and len(set(urls)) <= 10 and all([u and isinstance(u, str) for u in urls])):
        return {
            'statusCode': 400,
            'headers': {
                "Access-Control-Allow-Origin": "*"
            },
            'body': json.dumps({'message': 'Bad request - urls must be provided and it should be '
                                           'no longer than 10 elements'})
        }
    urls = list(set(urls))

    response = table.get_item(
        Key={
            'id': user_id
        }
    )
    user_data = response['Item']
    old_urls = set(user_data['data_source_web_urls'])

    folders_to_delete = old_urls - urls
    s3 = boto3.resource('s3', region_name=os.getenv('AWS_REGION', 'eu-west-2'))
    bucket = s3.Bucket(os.getenv('BUCKET_NAME', 'llmanuals-knowledge-source-web'))
    for f in folders_to_delete:
        bucket.objects.filter(Prefix=f"{user_id}/{f}/").delete()

    table.update_item(
        Key={
            'id': user_id
        },
        UpdateExpression="SET data_source_web_urls = :urls",
        ExpressionAttributeValues={
            ':urls': urls
        }
    )
    return {
        'statusCode': 200,
        'headers': {
            "Access-Control-Allow-Origin": "*"
        }
    }
