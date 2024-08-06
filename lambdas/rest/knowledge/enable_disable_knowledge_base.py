import os
import json

import boto3


def lambda_handler(event, context):
    user_data = event['body']['user_data']
    kb_state = event['body']['kb_state']

    bedrock_client = boto3.client('bedrock-agent', region_name=os.getenv('AWS_REGION', 'eu-west-2'))
    bedrock_client.update_agent_knowledge_base(
        agentId=user_data['agent_id'],
        agentVersion='DRAFT',
        knowledgeBaseId=user_data['knowledge_base'],
        knowledgeBaseState=kb_state
    )

    lambda_client = boto3.client('lambda', region_name=os.getenv('AWS_REGION', 'eu-west-2'))
    response = lambda_client.invoke(
        FunctionName='prepare_agent',
        InvocationType='RequestResponse',
        Payload=json.dumps({
            'agent_id': user_data['agent_id'],
            'current_alias_id': user_data['alias_id'],
            'current_version': user_data['agent_version']
        })
    )
    prepare_agent_response = json.loads(response['Payload'].read().decode('utf-8'))
    prepare_agent_body = json.loads(prepare_agent_response['body'])
    alias_id = prepare_agent_body['alias_id']
    agent_version = prepare_agent_body['agent_version']

    dynamodb_client = boto3.resource('dynamodb', region_name=os.getenv('AWS_REGION', 'eu-west-2'))
    table = dynamodb_client.Table('user')
    table.update_item(
        Key={
            'id': user_data['id']
        },
        UpdateExpression="SET alias_id = :al_id, agent_version = :agent_v",
        ExpressionAttributeValues={
            ':al_id': alias_id, ':agent_v': agent_version
        }
    )
