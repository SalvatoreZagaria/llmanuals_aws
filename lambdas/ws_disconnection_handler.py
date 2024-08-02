import os
import json

import boto3


def lambda_handler(event, context):
    connection_id = event['requestContext']['connectionId']

    dynamodb = boto3.resource('dynamodb', region_name=os.getenv('AWS_REGION', 'eu-west-2'))
    table = dynamodb.Table('connection')
    table.delete_item(
        Key={
            'id': connection_id
        }
    )

    return {
        'statusCode': 200
    }
