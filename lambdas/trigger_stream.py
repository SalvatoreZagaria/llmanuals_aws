import os
import json

import boto3


def lambda_handler(event, context):
    websocket_endpoint = os.getenv('WEBSOCKET_ENDPOINT')
    if not websocket_endpoint:
        raise Exception('Please set the WEBSOCKET_ENDPOINT env variable')
    apigateway_client = boto3.client('apigatewaymanagementapi', endpoint_url=websocket_endpoint)
    dynamodb_client = boto3.resource('dynamodb', region_name=os.getenv('AWS_REGION', 'eu-west-2'))
    lambda_client = boto3.client('lambda', region_name=os.getenv('AWS_REGION', 'eu-west-2'))

    connection_id = event['requestContext']['connectionId']
    body = event['body']
    if not body:
        apigateway_client.post_to_connection(
            ConnectionId=connection_id,
            Data=json.dumps({'type': 'error', 'message': 'Bad request - no payload'}))
        return {'statusCode': 400}
    try:
        body = json.loads(body)
        stream_id = body.get('streamId') or None
        prompt = body['prompt']
        assert prompt and isinstance(prompt, str)
    except (KeyError, AssertionError):
        apigateway_client.post_to_connection(
            ConnectionId=connection_id,
            Data=json.dumps({'type': 'error', 'message': 'Bad request - prompt and streamId required'}))
        return {'statusCode': 400}
    try:
        table = dynamodb_client.Table('connection')
        response = table.get_item(
            Key={
                'connection_id': connection_id
            }
        )
        user_attributes = response['Item']['user_attributes']
    except:
        apigateway_client.post_to_connection(
            ConnectionId=connection_id,
            Data=json.dumps({'type': 'error', 'message': 'Unauthorized'}))
        return {'statusCode': 401}

    lambda_client.invoke(
        FunctionName='invoke_agent',
        InvocationType='Event',
        Payload=json.dumps(
            {
                'connection_id': connection_id,
                'user_attributes': user_attributes,
                'stream_id': stream_id,
                'prompt': prompt
            }
        )
    )

    return {'statusCode': 202}
