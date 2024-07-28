import os
import time
import logging

import boto3

logger = logging.getLogger()
logger.setLevel("INFO")


DEFAULT_ASSISTANT_INSTRUCTIONS = (
    'You are an assistant for the organization "{name}", you answer a user query by searching what they need among '
    "the files at your disposal, citing the source of your information. Please do not cite your sources more than "
    "once, only answer queries that concern the content of the files and reject unrelated topics, but "
    "you can use external knowledge to integrate with the files at your disposal."
)
bedrock_client = boto3.client('bedrock-agent', region_name=os.getenv('AWS_REGION', 'eu-west-2'))


class AgentPreparationFailed(Exception):
    pass


def lambda_handler(event, context):
    user_id = event['body']['sub']
    org_name = event['body']['organization_name']

    model = os.getenv('BEDROCK_MODEL', 'anthropic.claude-3-haiku-20240307-v1:0')
    agent_role = os.getenv(
        'AGENT_ROLE', 'arn:aws:iam::851725385545:role/service-role/AmazonBedrockExecutionRoleForAgents_4Q1JMLC7NUJ'
    )
    instruction = DEFAULT_ASSISTANT_INSTRUCTIONS.format(name=org_name)
    logger.info('Creating agent...')
    start = time.time()
    response = bedrock_client.create_agent(
        agentName=user_id,
        agentResourceRoleArn=agent_role,
        clientToken=user_id,
        foundationModel=model,
        instruction=instruction,
    )
    agent_id = response['agent']['agentId']

    wait_for_agent_operation(agent_id, 'CREATING')
    logger.info(f'Done in {time.time() - start}')

    logger.info('Preparing agent...')
    start = time.time()
    bedrock_client.prepare_agent(
        agentId=agent_id
    )
    wait_for_agent_operation(agent_id, 'PREPARING')
    logger.info(f'Done in {time.time() - start}')

    logger.info('Creating agent alias...')
    start = time.time()
    response = bedrock_client.create_agent_alias(
        agentAliasName=agent_id,
        agentId=agent_id
    )
    alias_id = response['agentAlias']['agentAliasId']
    wait_for_alias_operation(agent_id, alias_id)
    logger.info(f'Done in {time.time() - start}')

    logger.info('Storing info in DynamoDB...')
    dynamodb_client = boto3.client('dynamodb')
    dynamodb_client.put_item(
        TableName='user',
        Item={
            'id': {'S': user_id},
            'organization_name': {'S': org_name},
            'organization_description': {'S': ''},
            'agent_id': {'S': agent_id},
            'alias_id': {'S': alias_id},
            'knowledge_base_id_s3': {'S': ''},
            'knowledge_base_id_web_crawler': {'S': ''},
        }
    )


def get_agent_status(agent_id: str):
    response = bedrock_client.get_agent(
        agentId=agent_id
    )
    return response['agent']['agentStatus']


def wait_for_agent_operation(agent_id: str, operation: str):
    while True:
        agent_status = get_agent_status(agent_id)
        if agent_status == operation:
            time.sleep(3)
            continue
        if agent_status == 'FAILED':
            raise AgentPreparationFailed(f"Agent failed - AGENT ID: {agent_id}; OPERATION: {operation}")
        return


def get_alias_status(agent_id: str, alias_id: str):
    response = bedrock_client.get_agent_alias(
        agentId=agent_id,
        agentAliasId=alias_id,
    )
    return response['agentAlias']['agentAliasStatus']


def wait_for_alias_operation(agent_id: str, alias_id: str):
    while True:
        alias_status = get_alias_status(agent_id, alias_id)
        if alias_status == 'CREATING':
            time.sleep(1)
            continue
        if alias_status == 'FAILED':
            raise AgentPreparationFailed(f"Agent alias failed - AGENT ID: {agent_id}; ALIAS ID: {alias_id}")
        return
