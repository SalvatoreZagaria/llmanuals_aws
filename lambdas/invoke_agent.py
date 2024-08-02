import os
import uuid
import logging
import traceback

import boto3


logger = logging.getLogger()
logger.setLevel("INFO")


def lambda_handler(event, context):
    websocket_endpoint = os.getenv('WEBSOCKET_ENDPOINT')
    if not websocket_endpoint:
        raise Exception('Please set the WEBSOCKET_ENDPOINT env variable')
    apigateway_client = boto3.client('apigatewaymanagementapi', endpoint_url=websocket_endpoint)
    bedrock_client_runtime = boto3.client('bedrock-agent-runtime')

    connection_id = event['body']['connection_id']
    user_attributes = event['body']['user_attributes']
    stream_id = event['body']['stream_id']
    prompt = event['body']['prompt']

    kwargs = {
        'agentId': user_attributes['agent_id'],
        'agentAliasId': user_attributes['alias_id'],
        'sessionId': f'{user_attributes['agent_id']}-{user_attributes['alias_id']}-{uuid.uuid4()}',
        'inputText': prompt,
        'sessionState': {}
    }
    for kb_key in ('knowledge_base_id_s3', 'knowledge_base_id_web_crawler'):
        if not user_attributes[kb_key]:
            continue
        kwargs['sessionState'].setdefault('knowledgeBaseConfigurations', [])
        kwargs['sessionState']['knowledgeBaseConfigurations'].append(
            {
                'knowledgeBaseId': user_attributes[kb_key],
                'retrievalConfiguration': {
                    'vectorSearchConfiguration': {
                        'numberOfResults': int(os.getenv('CHUNKS_NUMBER', 5))
                    }
                }
            }
        )

    try:
        response = bedrock_client_runtime.invoke_agent(**kwargs)
        for n, event in enumerate(response["completion"]):
            pass    # TODO
    except:
        tb = traceback.format_exc()
        logger.error(tb)
