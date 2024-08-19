import os
import json
import hashlib
import logging

import boto3


logger = logging.getLogger()
logger.setLevel("INFO")

bedrock_client = boto3.client(
    "bedrock-agent", region_name=os.getenv("AWS_REGION", "eu-west-2")
)
dynamodb_client = boto3.resource(
    "dynamodb", region_name=os.getenv("AWS_REGION", "eu-west-2")
)
table = dynamodb_client.Table("user")


class UserError(Exception):
    pass


def hash_string(s: str) -> str:
    return hashlib.md5(s.encode()).hexdigest()


def bad_request(msg):
    return {
        "statusCode": 400,
        "headers": {"Access-Control-Allow-Origin": "*"},
        "body": json.dumps({"message": msg}),
    }


def lambda_handler(event, context):
    user_id = event["requestContext"]["authorizer"]["claims"]["sub"]

    body = event["body"]
    if not body:
        return bad_request("Bad request - no payload")
    body = json.loads(body)
    urls = body.get("urls") or []
    if not (isinstance(urls, list)):
        return bad_request("Bad request - urls must be provided and it should be list")
    fixed_urls = set()
    for url in urls:
        if not (isinstance(url, str) and url.strip()):
            return bad_request("Bad request - invalid urls")
        fixed_urls.add(url.strip())

    if len(fixed_urls) > 10:
        return bad_request("Bad request - Max urls allowed: 10")

    response = table.get_item(Key={"id": user_id})
    user_data = response["Item"]
    old_urls = set(user_data["data_source_web_urls"])

    folders_to_delete = old_urls - fixed_urls
    s3 = boto3.resource("s3", region_name=os.getenv("AWS_REGION", "eu-west-2"))
    bucket = s3.Bucket(os.getenv("BUCKET_NAME", "llmanuals-knowledge-source-web"))
    for f in folders_to_delete:
        bucket.objects.filter(Prefix=f"{user_id}/{hash_string(f)}/").delete()

    table.update_item(
        Key={"id": user_id},
        UpdateExpression="SET data_source_web_urls = :urls",
        ExpressionAttributeValues={":urls": list(fixed_urls)},
    )
    return {"statusCode": 200, "headers": {"Access-Control-Allow-Origin": "*"}}
