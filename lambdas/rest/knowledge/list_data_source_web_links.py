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
    kb_id = user_data['knowledge_base']
    if not data_source_id:
        return {
            'statusCode': 404,
            'headers': {
                "Access-Control-Allow-Origin": "*"
            },
            'body': json.dumps({'message': 'Web data source not found'})
        }

    bedrock_client = boto3.client('bedrock-agent', region_name=os.getenv('AWS_REGION', 'eu-west-2'))
    data_source = bedrock_client.get_data_source(
        dataSourceId=data_source_id,
        knowledgeBaseId=kb_id
    )

    return {
        'statusCode': 200,
        'headers': {
            "Access-Control-Allow-Origin": "*"
        },
        'body': json.dumps({
            'urls': [
                su['url'] for su in
                data_source['dataSource']['dataSourceConfiguration']['webConfiguration']['sourceConfiguration']
                ['urlConfiguration']['seedUrls']
            ]
        })
    }
