import os
import json
import uuid
import logging
import traceback
from datetime import datetime

import boto3


logger = logging.getLogger()
logger.setLevel("INFO")


def lambda_handler(event, context):
    user_id = event["requestContext"]["authorizer"]["claims"]["sub"]

    dynamodb_client = boto3.resource(
        "dynamodb", region_name=os.getenv("AWS_REGION", "eu-west-2")
    )

    task_table = dynamodb_client.Table('crawler_task')
    try:
        response = task_table.get_item(
            Key={
                'id': user_id
            }
        )
        is_task_running = not response['Item']['is_ended']
    except dynamodb_client.exceptions.ResourceNotFoundException:
        is_task_running = False

    if is_task_running:
        return {
            "statusCode": 503,
            "headers": {"Access-Control-Allow-Origin": "*"},
            "body": json.dumps(
                {
                    "message": "Another crawling job is still ongoing.",
                    "statusLocation": "/api/admin/agent/status",
                }
            ),
        }

    user_table = dynamodb_client.Table("user")
    response = user_table.get_item(
        Key={
            "id": user_id
        }
    )
    user_data = response["Item"]
    urls = user_data["data_source_web_urls"]
    if not urls:
        return {
            "statusCode": 400,
            "headers": {"Access-Control-Allow-Origin": "*"},
            "body": json.dumps(
                {
                    "message": "No data source web URLs found."
                }
            ),
        }

    ecs_client = boto3.client('ecs', region_name=os.getenv('AWS_REGION', 'eu-west-2'))

    subnets = os.getenv('SUBNETS_IDS',
                        'subnet-040092248db77265d;subnet-0b0abd7d8cc9dcb70;subnet-0dc6d2c32b7fbb32e').split(';')
    security_groups = os.getenv('SECURITY_GROUPS_IDS', 'sg-03d8c0bff07221f50').split(';')

    try:
        ecs_client.run_task(
            cluster=os.getenv('CLUSTER', 'arn:aws:ecs:eu-west-2:851725385545:cluster/llmanuals'),
            count=1,
            enableExecuteCommand=True,
            launchType='FARGATE',
            networkConfiguration={
                'awsvpcConfiguration': {
                    'subnets': subnets,
                    'securityGroups': security_groups,
                    'assignPublicIp': 'ENABLED'
                }
            },
            overrides={
                'containerOverrides': [
                    {
                        'name': os.getenv('CONTAINER_NAME', 'scraper'),
                        'command': urls,
                        'environment': [
                            {
                                'name': 'USER_ID',
                                'value': user_id
                            },
                        ]
                    },
                ],
            },
            referenceId=str(uuid.uuid4()),
            taskDefinition=os.getenv('TASK_DEFINITION',
                                     'arn:aws:ecs:eu-west-2:851725385545:task-definition/scraping:3')
        )

        task_table.update_item(
            Key={
                'id': user_id
            },
            UpdateExpression="SET started_at = :started_at, is_ended = :is_ended, ended_at = :ended_at, "
                             "metadata = :metadata, status = :status",
            ExpressionAttributeValues={
                ':started_at': datetime.now().isoformat(), ':is_ended': False,
                ':ended_at': None, ':metadata': {}, ':status': 'RUNNING'
            }
        )

        return {
            "statusCode": 202,
            "headers": {"Access-Control-Allow-Origin": "*"},
            "body": json.dumps(
                {"message": "Crawling task started."}
            ),
        }

    except:
        tb = traceback.format_exc()
        logger.error(tb)
        return {
            "statusCode": 500,
            "headers": {"Access-Control-Allow-Origin": "*"},
            "body": json.dumps(
                {"message": "Unexpected error. Please contact the administrator."}
            ),
        }
