import os

import boto3


class Unauthorized(Exception):
    pass


def lambda_handler(event, context):
    connection_id = event['requestContext']['connectionId']

    authorization = (event['queryStringParameters'] or {}).get('accessToken')
    if not authorization:
        raise Unauthorized('No Authorization provided')

    cognito_client = boto3.client('cognito-idp', region_name=os.getenv('AWS_REGION', 'eu-west-2'))
    try:
        response = cognito_client.get_user(
            AccessToken=authorization
        )
    except:
        raise Unauthorized('Invalid token')

    user_id = [i['Value'] for i in response['UserAttributes'] if i['Name'] == 'sub'][0]
    dynamodb = boto3.resource('dynamodb', region_name=os.getenv('AWS_REGION', 'eu-west-2'))
    table = dynamodb.Table('user')
    response = table.get_item(
        Key={
            'id': user_id
        }
    )
    user_attributes = {key: {'S': value} for key, value in response['Item'].items()}
    table = dynamodb.Table('connection')
    table.put_item(
        Item={
            'connection_id': connection_id,
            'user_attributes': user_attributes,
        }
    )

    return {
        'statusCode': 200
    }
