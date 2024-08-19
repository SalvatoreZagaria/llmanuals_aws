import os
import json

import boto3


def lambda_handler(event, context):
    user_id = event["requestContext"]["authorizer"]["claims"]["sub"]
    try:
        file_name = event["queryStringParameters"]["fileName"]
        assert file_name
    except:
        return {
            "statusCode": 400,
            "headers": {"Access-Control-Allow-Origin": "*"},
            "body": json.dumps(
                {"message": "Bad request - fileName query parameter required"}
            ),
        }

    bucket_name = os.getenv("BUCKET_NAME", "llmanuals-knowledge-source")
    s3_client = boto3.client("s3", region_name=os.getenv("AWS_REGION", "eu-west-2"))

    s3_client.delete_object(Bucket=bucket_name, Key=f"{user_id}/{file_name}")

    return {
        "statusCode": 200,
        "headers": {"Access-Control-Allow-Origin": "*"},
        "body": json.dumps(""),
    }
