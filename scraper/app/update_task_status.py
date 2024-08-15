import os
from pathlib import Path
from datetime import datetime

import boto3

OUTPUT_FOLDER = Path('output')


def main(status):
    user_id = os.environ['USER_ID']

    dynamodb_client = boto3.resource(
        "dynamodb", region_name=os.getenv("AWS_REGION", "eu-west-2")
    )

    metadata = {}
    if status == 'SUCCEEDED':
        if not OUTPUT_FOLDER.is_dir():
            raise Exception(f'{OUTPUT_FOLDER} does not exist')
        metadata = {
            'scrapedUrls': len([d for d in OUTPUT_FOLDER.glob('*') if d.is_dir()]),
            'totalScrapedPages': len([f for f in OUTPUT_FOLDER.rglob('*.txt') if f.is_file()])
        }

    task_table = dynamodb_client.Table('crawler_task')
    task_table.update_item(
        Key={
            'id': user_id
        },
        UpdateExpression="SET is_ended = :is_ended, ended_at = :ended_at, metadata = :metadata, status = :status",
        ExpressionAttributeValues={
            ':is_ended': True, ':ended_at': datetime.now().isoformat(), ':metadata': metadata, ':status': status
        }
    )


if __name__ == '__main__':
    import argparse

    parser = argparse.ArgumentParser(description="Update web crawler task status")
    parser.add_argument("--status", help="Task status", required=True)
    args = parser.parse_args()

    status = args.status

    main(status)
