import os
import json

import boto3


def lambda_handler(event, context):
    user_id = event['requestContext']['authorizer']['claims']['sub']

    dynamodb_client = boto3.resource('dynamodb', region_name=os.getenv('AWS_REGION', 'eu-west-2'))
    table = dynamodb_client.Table('user')

    response = table.get_item(
        Key={
            'id': user_id
        }
    )
    user_data = response['Item']

    return {
        'statusCode': 200,
        'headers': {
            "Access-Control-Allow-Origin": "*"
        },
        'body': json.dumps({
            'urls': user_data['data_source_web_urls']
        })
    }
