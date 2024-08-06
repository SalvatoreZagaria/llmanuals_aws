import os

import boto3


def lambda_handler(event, context):
    user_data = event['body']
    user_id = user_data['sub']
    kb_id = user_data['knowledge_base']
    data_source_id = user_data['data_source_web_crawler']

    bedrock_client = boto3.client('bedrock-agent', region_name=os.getenv('AWS_REGION', 'eu-west-2'))
    dynamodb_client = boto3.resource('dynamodb', region_name=os.getenv('AWS_REGION', 'eu-west-2'))
    table = dynamodb_client.Table('user')

    bedrock_client.delete_data_source(
        dataSourceId=data_source_id,
        knowledgeBaseId=kb_id
    )

    table.update_item(
        Key={
            'id': user_id
        },
        UpdateExpression="SET data_source_web_crawler = :data_source_id",
        ExpressionAttributeValues={
            ':data_source_id': ''
        }
    )
