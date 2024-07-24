import os
import json
import time

import boto3


def lambda_handler(event, context):
    connection_id = event['body']['connectionId']

    websocket_api_id = os.getenv('WEBSOCKET_API_ID')
    region_name = os.getenv('AWS_REGION', 'eu-west-2')

    if not websocket_api_id:
        raise Exception('Please set the WEBSOCKET_API_ID env variable')

    websoocket_endpoint = f"https://{websocket_api_id}.execute-api.{region_name}.amazonaws.com/Prod"
    for i in range(10):
        api_gateway_management_api = boto3.client('apigatewaymanagementapi', endpoint_url=websoocket_endpoint)
        api_gateway_management_api.post_to_connection(
            ConnectionId=connection_id,
            Data=json.dumps({'message': f'Event {i}'}))
        time.sleep(1)
