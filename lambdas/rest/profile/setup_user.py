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
    "you can use external knowledge to integrate with the files at your disposal."
)
bedrock_client = boto3.client('bedrock-agent', region_name=os.getenv('AWS_REGION', 'eu-west-2'))


class AgentPreparationFailed(Exception):
    pass


def lambda_handler(event, context):
    user_id = event['body']['sub']
    org_name = event['body']['organization_name']

    agent_id = create_agent(user_id, org_name)
    kb_id = create_knowledge_base(user_id, agent_id)
    s3_data_source_id = create_s3_data_source(user_id, kb_id)
    web_data_source_id = create_web_data_source(user_id, kb_id)

    lambda_client = boto3.client('lambda', region_name=os.getenv('AWS_REGION', 'eu-west-2'))
    response = lambda_client.invoke(
        FunctionName='prepare_agent',
        InvocationType='RequestResponse',
        Payload=json.dumps({'agent_id': agent_id})
    )
    prepare_agent_response = json.loads(response['Payload'].read().decode('utf-8'))
    prepare_agent_body = json.loads(prepare_agent_response['body'])
    alias_id = prepare_agent_body['alias_id']
    agent_version = prepare_agent_body['agent_version']

    logger.info('Storing info in DynamoDB...')
    dynamodb_client = boto3.client('dynamodb', region_name=os.getenv('AWS_REGION', 'eu-west-2'))
    dynamodb_client.put_item(
        TableName='user',
        Item={
            'id': {'S': user_id},
            'organization_name': {'S': org_name},
            'organization_description': {'S': ''},
            'agent_id': {'S': agent_id},
            'agent_version': {'S': agent_version},
            'alias_id': {'S': alias_id},
            'knowledge_base': {'S': kb_id},
            'data_source_s3': {'S': s3_data_source_id},
            'data_source_web_crawler': {'S': web_data_source_id},
            'data_source_web_urls': {'L': []}
        }
    )


def create_agent(user_id, org_name):
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

    return agent_id


def create_knowledge_base(user_id, agent_id):
    logger.info('Creating knowledge base...')
    start = time.time()

    response = bedrock_client.create_knowledge_base(
        clientToken=user_id,
        name=f'{user_id}_kb',
        roleArn=os.getenv(
            'KB_ROLE', 'arn:aws:iam::851725385545:role/service-role/AmazonBedrockExecutionRoleForKnowledgeBase_k7n89'),
        knowledgeBaseConfiguration={
            'type': 'VECTOR',
            'vectorKnowledgeBaseConfiguration': {
                'embeddingModelArn': 'arn:aws:bedrock:eu-west-2::foundation-model/amazon.titan-embed-text-v2:0'
            }
        },
        storageConfiguration={
            'rdsConfiguration':
            {
                'credentialsSecretArn': os.getenv(
                    'RDS_SECRET_ARN', 'arn:aws:secretsmanager:eu-west-2:851725385545:secret:LLManualsAurora-hfpK6Y'
                ),
                'databaseName': os.getenv('RDS_DB_NAME', 'llmanuals'),
                'fieldMapping': {'metadataField': 'metadata',
                                 'primaryKeyField': 'id',
                                 'textField': 'chunks',
                                 'vectorField': 'embedding'},
                'resourceArn': os.getenv('RDS_DB_ARN', 'arn:aws:rds:eu-west-2:851725385545:cluster:llmanualsdev'),
                'tableName': os.getenv('RDS_DB_TABLE_NAME', 'bedrock_integration.bedrock_kb')
            },
            'type': 'RDS'
        },
    )
    kb_id = response['knowledgeBase']['knowledgeBaseId']
    wait_for_knowledge_operation(kb_id)
    logger.info(f'Done in {time.time() - start}')

    bedrock_client.associate_agent_knowledge_base(
        agentId=agent_id,
        agentVersion='DRAFT',
        description=f"{user_id}'s KB",
        knowledgeBaseId=kb_id,
        knowledgeBaseState='DISABLED'
    )

    return kb_id


def create_data_source(user_id: str, kb_id: str, bucket_arn: str, name: str):
    kwargs = {
        'clientToken': user_id,
        'dataSourceConfiguration': {
            'type': 'S3',
            's3Configuration': {
                'bucketArn': bucket_arn,
                'inclusionPrefixes': [
                    f'{user_id}/',
                ]
            }
        },
        'knowledgeBaseId': kb_id,
        'name': name,
        'vectorIngestionConfiguration': {
            'chunkingConfiguration': {
                'chunkingStrategy': 'FIXED_SIZE',
                'fixedSizeChunkingConfiguration': {
                    'maxTokens': 800,
                    'overlapPercentage': 20
                }
            }
        }
    }

    response = bedrock_client.create_data_source(**kwargs)
    return response['dataSource']['dataSourceId']


def create_s3_data_source(user_id, kb_id):
    return create_data_source(
        user_id, kb_id, os.getenv('S3_BUCKET_ARN', 'arn:aws:s3:::llmanuals-knowledge-source'),
        f'S3_{user_id}'
    )


def create_web_data_source(user_id, kb_id):
    return create_data_source(
        user_id, kb_id, os.getenv('WEB_BUCKET_ARN', 'arn:aws:s3:::llmanuals-knowledge-source-web'),
        f'WEB_{user_id}'
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


def get_kb_status(kb_id: str):
    response = bedrock_client.get_knowledge_base(
        knowledgeBaseId=kb_id
    )
    return response['knowledgeBase']['status']


def wait_for_knowledge_operation(kb_id: str):
    while True:
        kb_status = get_kb_status(kb_id)
        if kb_status == 'CREATING':
            time.sleep(1)
            continue
        if kb_status == 'FAILED':
            raise AgentPreparationFailed(f"Knowledge base failed - KB ID: {kb_id}")
        return
