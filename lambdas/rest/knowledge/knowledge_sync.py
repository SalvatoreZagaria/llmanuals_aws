import os
import json
import logging
import traceback

import boto3


logger = logging.getLogger()
logger.setLevel("INFO")


def lambda_handler(event, context):
    user_id = event["requestContext"]["authorizer"]["claims"]["sub"]

    if event["resource"] == "/api/admin/knowledge/static/sync":
        source_kind = "STATIC"
        data_source_key = "data_source_s3"
    elif event["resource"] == "/api/admin/knowledge/web/sync":
        source_kind = "WEB"
        data_source_key = "data_source_web_crawler"
    else:
        logger.error(f'Unhandled case - {event["resource"]}')
        return {
            "statusCode": 500,
            "headers": {"Access-Control-Allow-Origin": "*"},
            "body": json.dumps({"message": "Server error"}),
        }

    client = boto3.client("lambda", region_name=os.getenv("AWS_REGION", "eu-west-2"))

    response = client.invoke(
        FunctionName="agent_status",
        InvocationType="RequestResponse",
        Payload=json.dumps(event),
    )
    status_response = json.loads(response["Payload"].read().decode("utf-8"))
    if status_response["statusCode"] != 200:
        return {
            "statusCode": status_response["statusCode"],
            "headers": {"Access-Control-Allow-Origin": "*"},
            "body": status_response["body"],
        }
    status_body = json.loads(status_response["body"])
    if not (
        status_body["knowledge"]["isKnowledgeReady"]
        and not status_body["knowledge"]["knowledgeError"]
    ):
        return {
            "statusCode": 503,
            "headers": {"Access-Control-Allow-Origin": "*"},
            "body": json.dumps(
                {
                    "message": "Knowledge is not ready or there is a knowledge error.",
                    "statusLocation": "/api/admin/agent/status",
                }
            ),
        }
    if status_body["knowledge"]["dataSources"][source_kind.lower()]["synchronization"][
        "status"
    ] in (None, "STARTING", "IN_PROGRESS") or (
        source_kind == "WEB"
        and status_body["knowledge"]["dataSources"][source_kind.lower()]
        .get("crawling", {})
        .get("status")
        == "RUNNING"
    ):
        return {
            "statusCode": 503,
            "headers": {"Access-Control-Allow-Origin": "*"},
            "body": json.dumps(
                {
                    "message": "Another synchronization job is still ongoing.",
                    "statusLocation": "/api/admin/agent/status",
                }
            ),
        }

    dynamodb_client = boto3.resource(
        "dynamodb", region_name=os.getenv("AWS_REGION", "eu-west-2")
    )
    table = dynamodb_client.Table("user")
    response = table.get_item(Key={"id": user_id})
    user_data = response["Item"]
    kb_id = user_data["knowledge_base"]
    data_source_id = user_data[data_source_key]

    bedrock_client = boto3.client(
        "bedrock-agent", region_name=os.getenv("AWS_REGION", "eu-west-2")
    )

    try:
        bedrock_client.start_ingestion_job(
            clientToken=user_id, dataSourceId=data_source_id, knowledgeBaseId=kb_id
        )
        return {
            "statusCode": 202,
            "headers": {"Access-Control-Allow-Origin": "*"},
            "body": json.dumps(
                {
                    "message": "Synchronization job started.",
                    "statusLocation": "/api/admin/agent/status",
                }
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
