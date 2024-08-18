import os
from pathlib import Path
from datetime import datetime

import boto3

OUTPUT_FOLDER = Path('output')


def main(status, task_id):
    user_id = os.environ['USER_ID']

    metadata = {}
    if status == 'SUCCEEDED':
        if not OUTPUT_FOLDER.is_dir():
            raise Exception(f'{OUTPUT_FOLDER} does not exist')
        metadata = {
            'scrapedUrls': len([d for d in OUTPUT_FOLDER.glob('*') if d.is_dir()]),
            'totalScrapedPages': len([f for f in OUTPUT_FOLDER.rglob('*.txt') if f.is_file()])
        }

    dynamodb_resource = boto3.resource('dynamodb', region_name=os.getenv('AWS_REGION', 'eu-west-2'))
    task_table = dynamodb_resource.Table('single_scraper_task')
    task_table.update_item(
        Key={
            'user_id': user_id,
            'task_id': task_id
        },
        UpdateExpression="SET is_ended = :is_ended, ended_at = :ended_at, metadata = :metadata, "
                         "task_status = :task_status",
        ExpressionAttributeValues={
            ':is_ended': True, ':ended_at': datetime.now().isoformat(), ':metadata': metadata, ':task_status': status
        }
    )


if __name__ == '__main__':
    import argparse

    parser = argparse.ArgumentParser(description="Update web crawler task status")
    parser.add_argument("--status", help="Task status", required=True)
    parser.add_argument("--task_id", help="Task id", required=True)
    args = parser.parse_args()

    status = args.status
    task_id = args.task_id

    main(status, task_id)
