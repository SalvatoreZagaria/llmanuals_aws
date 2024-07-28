import os
import json
import time

import boto3


def lambda_handler(event, context):
    connection_id = event['connectionId']

    websocket_endpoint = os.getenv('WEBSOCKET_ENDPOINT')
    if not websocket_endpoint:
        raise Exception('Please set the WEBSOCKET_ENDPOINT env variable')

    client = boto3.client('apigatewaymanagementapi', endpoint_url=websocket_endpoint)

    for i in range(10):
        client.post_to_connection(
            ConnectionId=connection_id,
            Data=json.dumps({'message': f'Event {i}'}))
        time.sleep(1)
