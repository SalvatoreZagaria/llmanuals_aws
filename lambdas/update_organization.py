import os
import time
import json
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

    lambda_client = boto3.client('lambda', region_name=os.getenv('AWS_REGION', 'eu-west-2'))
    response = lambda_client.invoke(
        FunctionName='prepare_agent',
        InvocationType='RequestResponse',
        Payload=json.dumps({
            'agent_id': agent_id,
            'current_alias_id': user_data['alias_id'],
            'current_version': user_data['agent_version']
        })
    )
    prepare_agent_response = json.loads(response['Payload'].read().decode('utf-8'))
    prepare_agent_body = json.loads(prepare_agent_response['body'])
    alias_id = prepare_agent_body['alias_id']
    agent_version = prepare_agent_body['agent_version']

    table.update_item(
        Key={
            'id': user_id
        },
        UpdateExpression="SET organization_name = :org_name, organization_description = :descr, alias_id = :al_id, agent_version = :agent_v",
        ExpressionAttributeValues={
            ':org_name': new_org_name, ':descr': new_description, ':al_id': alias_id, ':agent_v': agent_version
        }
    )
