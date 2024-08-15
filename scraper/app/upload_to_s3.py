import os
import asyncio
import logging
import traceback
import typing as t
from pathlib import Path

import boto3
import aioboto3


BUCKET_NAME = os.getenv('BUCKET_NAME', 'llmanuals-knowledge-source-web')
INPUT_FOLDER = 'output'

LOGGER = logging.getLogger()
LOGGER.setLevel("INFO")


async def upload_files(prefix: str, files: t.List[Path]):
    boto_session = aioboto3.Session()

    async def upload_file(f: Path):
        async with boto_session.client('s3', region_name=os.getenv('AWS_REGION', 'eu-west-2')) as s3:
            with open(f, 'rb') as f_bytes:
                await s3.upload_fileobj(f_bytes, BUCKET_NAME, f'{prefix}/{f.parent.name}/{f.name}')

    await asyncio.gather(*[upload_file(f) for f in files])


async def copy_obj(boto_session, source_key, destination_key):
    async with boto_session.client('s3', region_name=os.getenv('AWS_REGION', 'eu-west-2')) as s3:
        copy_source = {'Bucket': BUCKET_NAME, 'Key': source_key}
        await s3.copy_object(CopySource=copy_source, Bucket=BUCKET_NAME, Key=destination_key)


async def copy_folder(src, dest):
    boto_session = aioboto3.Session()

    continuation_token = None
    kwargs = {
        'Bucket': BUCKET_NAME,
        'Prefix': src
    }

    s3_client = boto3.client('s3', region_name=os.getenv('AWS_REGION', 'eu-west-2'))
    while True:
        if continuation_token:
            kwargs['ContinuationToken'] = continuation_token
        response = s3_client.list_objects_v2(**kwargs)
        await asyncio.gather(*[copy_obj(boto_session, item['Key'], dest + item['Key'].lstrip(src))
                               for item in response.get('Contents') or []])

        if not response.get('IsTruncated'):
            break
        continuation_token = response.get('NextContinuationToken')


async def make_backup(prefix):
    backup_folder = f'{prefix}_backup'
    await copy_folder(prefix, backup_folder)
    return backup_folder


def delete_folder(folder):
    s3 = boto3.resource('s3', region_name=os.getenv('AWS_REGION', 'eu-west-2'))
    bucket = s3.Bucket(BUCKET_NAME)
    bucket.objects.filter(Prefix=f"{folder}/").delete()


async def restore_backup(prefix):
    delete_folder(prefix)
    await copy_folder(f'{prefix}_backup', prefix)
    delete_folder(f'{prefix}_backup')


async def main():
    bucket_prefix = os.environ['USER_ID']
    files = [f for f in Path(INPUT_FOLDER).rglob('*') if f.is_file()]
    if not files:
        LOGGER.warning('No url scraped. Aborting.')
        return
    LOGGER.info(f'Saving {len(files)} files into s3...')
    try:
        backup_folder = await make_backup(bucket_prefix)
        delete_folder(bucket_prefix)
        await upload_files(bucket_prefix, files)
        delete_folder(backup_folder)
    except:
        LOGGER.error(traceback.format_exc())
        LOGGER.error('Restoring backup...')
        await restore_backup(bucket_prefix)


if __name__ == '__main__':
    asyncio.run(main())
