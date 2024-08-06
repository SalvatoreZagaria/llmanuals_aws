import os
import uuid
import json
import logging
import traceback

import boto3


logger = logging.getLogger()
logger.setLevel("INFO")


S3_HTTPS_LINK = os.getenv('S3_STATIC_LINK', 'https://llmanuals-knowledge-source.s3.eu-west-2.amazonaws.com/')
S3_LINK = os.getenv('S3_LINK', 's3://llmanuals-knowledge-source/')


def lambda_handler(event, context):
    websocket_endpoint = os.getenv('WEBSOCKET_ENDPOINT')
    if not websocket_endpoint:
        raise Exception('Please set the WEBSOCKET_ENDPOINT env variable')
    apigateway_client = boto3.client('apigatewaymanagementapi', endpoint_url=websocket_endpoint)
    bedrock_client_runtime = boto3.client('bedrock-agent-runtime', region_name=os.getenv('AWS_REGION', 'eu-west-2'))

    connection_id = event['connection_id']
    user_attributes = event['user_attributes']
    stream_id = event['stream_id']
    prompt = event['prompt']

    kwargs = {
        'agentId': user_attributes['agent_id'],
        'agentAliasId': user_attributes['alias_id'],
        'sessionId': f'{user_attributes['agent_id']}-{user_attributes['alias_id']}-{uuid.uuid4()}',
        'inputText': prompt,
        'sessionState': {
            'knowledgeBaseConfigurations': [
                {
                    'knowledgeBaseId': user_attributes['knowledge_base'],
                    'retrievalConfiguration': {
                        'vectorSearchConfiguration': {
                            'numberOfResults': int(os.getenv('CHUNKS_NUMBER', 5))
                        }
                    }
                }
            ]
        }
    }

    apigateway_client.post_to_connection(
        ConnectionId=connection_id,
        Data=json.dumps({'type': 'start', 'streamId': stream_id}))
    try:
        response = bedrock_client_runtime.invoke_agent(**kwargs)
        n = 1
        for bedrock_event in response["completion"]:
            if not bedrock_event.get('chunk'):
                apigateway_client.post_to_connection(
                    ConnectionId=connection_id,
                    Data=json.dumps(
                        {'type': 'message', 'message': 'Nothing found.', 'streamId': stream_id, 'messageNumber': n}
                    ))
                logger.warning(f'Nothing found for {user_attributes["id"]}')
                logger.warning(f'Prompt: {prompt}')
                logger.warning(json.dumps(bedrock_event))
                break
            for citation in bedrock_event['chunk']['attribution']['citations']:
                message = {
                    'type': 'message',
                    'streamId': stream_id,
                    'message': citation['generatedResponsePart']['textResponsePart']['text'],
                    'references': [
                        {
                            'text': r['content']['text'],
                            'link': _transform_ref_link(r['location']['s3Location']['uri'])
                        }
                        for r in (citation.get('retrievedReferences') or [])
                    ],
                    'messageNumber': n
                }
                apigateway_client.post_to_connection(
                    ConnectionId=connection_id,
                    Data=json.dumps(message)
                )
                n += 1

        apigateway_client.post_to_connection(
            ConnectionId=connection_id,
            Data=json.dumps({'type': 'end', 'streamId': stream_id}))
    except:
        tb = traceback.format_exc()
        logger.error(tb)
        apigateway_client.post_to_connection(
            ConnectionId=connection_id,
            Data=json.dumps({'type': 'error', 'message': 'Unexpected error'}))


def _transform_ref_link(s3_link: str) -> str:
    return s3_link.replace(S3_LINK, S3_HTTPS_LINK)
