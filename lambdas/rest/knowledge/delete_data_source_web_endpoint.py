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

    data_source_id = user_data['data_source_web_crawler']
    if not data_source_id:
        return {
            'statusCode': 404,
            'headers': {
                "Access-Control-Allow-Origin": "*"
            },
            'body': json.dumps({'message': 'Web data source not found'})
        }

    client = boto3.client('lambda', region_name=os.getenv('AWS_REGION', 'eu-west-2'))
    client.invoke(
        FunctionName='delete_data_source_web',
        InvocationType='Event',
        Payload=json.dumps(user_data)
    )

    return {
        'statusCode': 202,
        'headers': {
            "Access-Control-Allow-Origin": "*"
        },
        'body': json.dumps({
            'message': 'Deleting web data source',
            'statusLocation': '/api/admin/agent/status'
        })
    }
