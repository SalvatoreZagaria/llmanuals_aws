import os
import json

import boto3


def lambda_handler(event, context):
    client = boto3.client('lambda', region_name=os.getenv('AWS_REGION', 'eu-west-2'))
    client.invoke(
        FunctionName='generate_stream_test',
        InvocationType='Event',
        Payload=json.dumps({'connectionId': event['requestContext']['connectionId']})
    )

    return {'statusCode': 202}
