import os
from pathlib import Path
from datetime import datetime

import boto3

OUTPUT_FOLDER = Path('output')


def main(task_id):
    user_id = os.environ['USER_ID']

    dynamodb_client = boto3.client('dynamodb', region_name=os.getenv('AWS_REGION', 'eu-west-2'))
    dynamodb_client.put_item(
        TableName='single_scraper_task',
        Item={
            'task_id': {'S': task_id},
            'user_id': {'S': user_id},
            'started_at': {'S': datetime.now().isoformat()},
            'is_ended': {'BOOL': False},
            'ended_at': {'S': ''},
            'metadata': {'M': {}},
            'task_status': {'S': 'RUNNING'}
        }
    )


if __name__ == '__main__':
    import argparse

    parser = argparse.ArgumentParser(description="Create single web crawler task")
    parser.add_argument("--task_id", help="Task id", required=True)
    args = parser.parse_args()

    task_id = args.task_id

    main(task_id)
