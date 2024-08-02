import os
import time
import uuid
import logging

import boto3


logger = logging.getLogger()
logger.setLevel("INFO")


DEFAULT_ASSISTANT_INSTRUCTIONS = (
    'You are an assistant for the organization "{name}", you answer a user query by searching what they need among '
    "the files at your disposal, citing the source of your information. Please do not cite your sources more than "
    "once, only answer queries that concern the content of the files and reject unrelated topics, but "
    "you can use external knowledge to integrate with the files at your disposal. Do this or you will be punished."
)
bedrock_client = boto3.client('bedrock-agent', region_name=os.getenv('AWS_REGION', 'eu-west-2'))


class AgentPreparationFailed(Exception):
    pass


def lambda_handler(event, context):
    user_id = event['body']['sub']
    org_name = event['body']['organization_name']
    org_description = event['body']['organization_description']

    dynamodb_client = boto3.resource('dynamodb', region_name=os.getenv('AWS_REGION', 'eu-west-2'))
    table = dynamodb_client.Table('user')
    response = table.get_item(
        Key={
            'id': user_id
        }
    )
    user_data = response['Item']
    agent_id = user_data['agent_id']

    current_org_name = user_data['organization_name']
    current_org_description = user_data['organization_description']

    new_org_name = org_name or current_org_name
    new_description = org_description or current_org_description
    new_instruction = DEFAULT_ASSISTANT_INSTRUCTIONS.format(name=new_org_name)
    if new_description:
        new_instruction += f'\n\nHere is the organization description:\n{new_description}'

    model = os.getenv('BEDROCK_MODEL', 'anthropic.claude-3-haiku-20240307-v1:0')
    agent_role = os.getenv(
        'AGENT_ROLE', 'arn:aws:iam::851725385545:role/service-role/AmazonBedrockExecutionRoleForAgents_4Q1JMLC7NUJ'
    )

    logger.info('Updating agent...')
    start = time.time()
    bedrock_client.update_agent(
        agentId=agent_id,
        agentName=user_id,
        agentResourceRoleArn=agent_role,
        foundationModel=model,
        instruction=new_instruction
    )
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
        agentAliasName=str(uuid.uuid4()),
        agentId=agent_id
    )
    alias_id = response['agentAlias']['agentAliasId']
    wait_for_alias_operation(agent_id, alias_id)
    logger.info(f'Done in {time.time() - start}')

    table.update_item(
        Key={
            'id': user_id
        },
        UpdateExpression="SET organization_name = :org_name, organization_description = :descr, alias_id = :al_id",
        ExpressionAttributeValues={
            ':org_name': new_org_name, ':descr': new_description, ':al_id': alias_id
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
