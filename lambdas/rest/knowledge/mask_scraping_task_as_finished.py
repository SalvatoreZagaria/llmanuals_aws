import os
from datetime import datetime

import boto3


def lambda_handler(event, context):
    user_id = event['ItemSelector']['UserID']
    url_tasks = event['ItemSelector']['UrlsTasks']

    dynamodb_resource = boto3.resource('dynamodb', region_name=os.getenv('AWS_REGION', 'eu-west-2'))
    response = dynamodb_resource.batch_get_item(
        RequestItems={
            'single_scraper_task': {
                'Keys': [
                    {
                        'task_id': st,
                        'user_id': user_id
                    } for url, st in url_tasks
                ]
            }
        }
    )
    single_tasks = {st['task_id']: st for st in response.get('Responses', {}).get('single_scraper_task') or []}

    metadata = {}
    for url, st_id in url_tasks:
        st = single_tasks[st_id]
        metadata[url] = {
            'status': st['task_status'],
            'metadata': st['metadata']
        }

    task_table = dynamodb_resource.Table('crawler_task')
    task_table.update_item(
        Key={
            'user_id': user_id
        },
        UpdateExpression="SET is_ended = :is_ended, ended_at = :ended_at, metadata = :metadata, "
                         "task_status = :task_status",
        ExpressionAttributeValues={
            ':is_ended': True, ':ended_at': datetime.now().isoformat(), ':metadata': metadata,
            ':task_status': 'SUCCEEDED' if all([v['status'] == 'SUCCEEDED' for v in metadata.values()]) else 'FAILED'
        }
    )
