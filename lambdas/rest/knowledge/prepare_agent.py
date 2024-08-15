import os
import time
import uuid
import json
import logging

import boto3

logger = logging.getLogger()
logger.setLevel("INFO")

bedrock_client = boto3.client('bedrock-agent', region_name=os.getenv('AWS_REGION', 'eu-west-2'))


class AgentPreparationFailed(Exception):
    pass


def lambda_handler(event, context):
    agent_id = event['agent_id']
    current_alias_id = event.get('current_alias_id')
    current_version = event.get('current_version')

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
    agent_version = wait_for_alias_operation(agent_id, alias_id)
    logger.info(f'Done in {time.time() - start}')

    if current_alias_id and current_version:
        logger.info('Deleting old agent version and alias...')
        start = time.time()
        bedrock_client.delete_agent_alias(
            agentAliasId=current_alias_id,
            agentId=agent_id
        )
        bedrock_client.delete_agent_version(
            agentId=agent_id,
            agentVersion=current_version,
            skipResourceInUseCheck=True
        )
        logger.info(f'Done in {time.time() - start}')

    return {
        'statusCode': 200,
        'body': json.dumps({
            'alias_id': alias_id,
            'agent_version': agent_version
        })
    }


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


def get_alias(agent_id: str, alias_id: str):
    response = bedrock_client.get_agent_alias(
        agentId=agent_id,
        agentAliasId=alias_id,
    )
    agent_version = None
    if response['agentAlias']['routingConfiguration']:
        agent_version = response['agentAlias']['routingConfiguration'][0].get('agentVersion')
    return response['agentAlias']['agentAliasStatus'], agent_version


def wait_for_alias_operation(agent_id: str, alias_id: str):
    while True:
        alias_status, agent_version = get_alias(agent_id, alias_id)
        if alias_status == 'CREATING':
            time.sleep(1)
            continue
        if alias_status == 'FAILED':
            raise AgentPreparationFailed(f"Agent alias failed - AGENT ID: {agent_id}; ALIAS ID: {alias_id}")
        return agent_version
