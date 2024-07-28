import json

import boto3


DEFAULT_ASSISTANT_INSTRUCTIONS = (
    'You are an assistant for the organization "{name}", you answer a user query by searching what they need among '
    "the files at your disposal, citing the source of your information. Please do not cite your sources more than "
    "once, only answer queries that concern the content of the files and reject unrelated topics, but "
    "you can use external knowledge to integrate with the files at your disposal. Do this or you will be punished."
)


def lambda_handler(event, context):
    user_attributes = event['request']['userAttributes']
    user_id = user_attributes['sub']

    organization_name = event['request']['body'].get('organization_name')
    if not (organization_name and isinstance(organization_name, str) and
            3 <= len(organization_name) <= 100):
        return {
            'statusCode': 400,
            'body': json.dumps({'message': 'Bad request - organization_name must be a string with maximum '
                                           'length of 100 characters'})
        }

    dynamodb = boto3.resource('dynamodb')
    table = dynamodb.Table('user')
    response = table.get_item(
        Key={
            'id': user_id
        }
    )
    user_data = response['Item']
    agent_id = user_data['agent_id']
    organization_description = user_data['organization_description']

    new_instruction = DEFAULT_ASSISTANT_INSTRUCTIONS.format(name=organization_name)
    if organization_description:
        new_instruction += f'\n\nHere is the organization description:\n{organization_description}'

    bedrock_client = boto3.client('bedrock-agent')
    bedrock_client.update_agent(
        agentId=agent_id,
        instruction=new_instruction
    )

    # TODO prepare, create new alias, replace alias_id with new alias

    table.update_item(
        Key={
            'id': user_id
        },
        UpdateExpression="SET organization_name = :org_name",
        ExpressionAttributeValues={
            ':org_name': organization_name
        }
    )

    return {
        'statusCode': 200
    }
