import os
import time
import logging
import traceback

import boto3


logger = logging.getLogger()
logger.setLevel("INFO")


bedrock_client = boto3.client('bedrock-agent', region_name=os.getenv('AWS_REGION', 'eu-west-2'))


def lambda_handler(event, context):
    user_id = event['body']['sub']
    logger.info(f'Deleting profile - USER_ID: {user_id}')

    cognito_client = boto3.client('cognito-idp', region_name=os.getenv('AWS_REGION', 'eu-west-2'))
    cognito_client.admin_disable_user(
        UserPoolId=os.getenv('USER_POOL_ID', 'eu-west-2_JUVPtjO37'),
        Username=user_id
    )

    dynamodb_client = boto3.resource('dynamodb', region_name=os.getenv('AWS_REGION', 'eu-west-2'))
    table = dynamodb_client.Table('user')
    response = table.get_item(
        Key={
            'id': user_id
        }
    )
    user_data = response['Item']
    kb_id = user_data['knowledge_base']
    agent_id = user_data['agent_id']

    error = False

    for key in ('data_source_s3', 'data_source_web_crawler'):
        if user_data.get(key):
            success = delete_data_source(kb_id, user_data[key])
            error = error or not success

    success = delete_knowledge_base(kb_id)
    error = error or not success

    success = delete_agent(agent_id)
    error = error or not success

    if error:
        logger.warning(f'Skipping DynamoDB and Cognito cleanup due to previous errors - USER_ID: {user_id}')
        return

    table.delete_item(
        Key={
            'id': user_id
        }
    )

    logger.info(f'Profile deactivated and user environment cleaned - USER_ID: {user_id}')


def delete_data_source(kb_id: str, ds_id: str) -> bool:
    try:
        bedrock_client.delete_data_source(
            dataSourceId=ds_id,
            knowledgeBaseId=kb_id
        )
    except:
        logger.error(f'Deleting data source unsuccessful: KNOWLEDGE_BASE: {kb_id}, DATA_SOURCE: {ds_id}')
        tb = traceback.format_exc()
        logger.error(tb)
        return False

    while True:
        time.sleep(2)
        try:
            response = bedrock_client.get_data_source(
                dataSourceId=ds_id,
                knowledgeBaseId=kb_id
            )
            status = response['dataSource']['status']
            if status == 'DELETE_UNSUCCESSFUL':
                logger.error(f'Deleting data source unsuccessful: KNOWLEDGE_BASE: {kb_id}, DATA_SOURCE: {ds_id}')
                return False
        except bedrock_client.exceptions.ResourceNotFoundException:
            return True


def delete_knowledge_base(kb_id: str) -> bool:
    try:
        bedrock_client.delete_knowledge_base(
            knowledgeBaseId=kb_id
        )
    except:
        logger.error(f'Deleting knowledge base unsuccessful: KNOWLEDGE_BASE: {kb_id}')
        tb = traceback.format_exc()
        logger.error(tb)
        return False

    while True:
        time.sleep(2)
        try:
            response = bedrock_client.get_knowledge_base(
                knowledgeBaseId=kb_id
            )
            status = response['knowledgeBase']['status']
            if status == 'DELETE_UNSUCCESSFUL':
                logger.error(f'Deleting knowledge base unsuccessful: KNOWLEDGE_BASE: {kb_id}')
                return False
        except bedrock_client.exceptions.ResourceNotFoundException:
            return True


def delete_agent(agent_id: str) -> bool:
    try:
        bedrock_client.delete_agent(
            agentId=agent_id,
            skipResourceInUseCheck=True
        )
    except:
        logger.error(f'Deleting agent unsuccessful: AGENT_ID: {agent_id}')
        tb = traceback.format_exc()
        logger.error(tb)
        return False

    while True:
        time.sleep(2)
        try:
            bedrock_client.get_agent(
                agentId=agent_id,
            )
        except bedrock_client.exceptions.ResourceNotFoundException:
            return True
