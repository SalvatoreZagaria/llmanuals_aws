import os
import json
import uuid
import logging
import traceback

import boto3

logger = logging.getLogger()
logger.setLevel("INFO")


S3_HTTPS_LINK = os.getenv(
    "S3_STATIC_LINK", "https://llmanuals-knowledge-source.s3.eu-west-2.amazonaws.com/"
)
S3_LINK = os.getenv("S3_LINK", "s3://llmanuals-knowledge-source/")


def lambda_handler(event, context):
    user_id = event["requestContext"]["authorizer"]["claims"]["sub"]

    body = event["body"]
    if not body:
        return {
            "statusCode": 400,
            "headers": {"Access-Control-Allow-Origin": "*"},
            "body": json.dumps({"message": "Bad request - no payload"}),
        }
    try:
        body = json.loads(body)
        stream_id = body.get("streamId")
        stream_id = str(stream_id) if stream_id else None
        prompt = body["prompt"]
        assert prompt and isinstance(prompt, str)
    except (KeyError, AssertionError):
        return {
            "statusCode": 400,
            "headers": {"Access-Control-Allow-Origin": "*"},
            "body": json.dumps({"message": "Bad request - prompt and streamId required"}),
        }

    dynamodb_client = boto3.resource(
        "dynamodb", region_name=os.getenv("AWS_REGION", "eu-west-2")
    )
    table = dynamodb_client.Table("user")
    response = table.get_item(Key={"id": user_id})
    user_attributes = response["Item"]

    kwargs = {
        "agentId": user_attributes["agent_id"],
        "agentAliasId": user_attributes["alias_id"],
        'sessionId': f'{user_attributes['agent_id']}-{user_attributes['alias_id']}-{uuid.uuid4()}',
        "inputText": prompt,
        "sessionState": {
            "knowledgeBaseConfigurations": [
                {
                    "knowledgeBaseId": user_attributes["knowledge_base"],
                    "retrievalConfiguration": {
                        "vectorSearchConfiguration": {
                            "numberOfResults": int(os.getenv("CHUNKS_NUMBER", 5))
                        }
                    },
                }
            ]
        },
    }

    bedrock_client_runtime = boto3.client(
        "bedrock-agent-runtime", region_name=os.getenv("AWS_REGION", "eu-west-2")
    )
    res = {'streamId': stream_id, 'prompt': prompt, 'messages': []}
    try:
        response = bedrock_client_runtime.invoke_agent(**kwargs)
        for bedrock_event in response["completion"]:
            if not bedrock_event.get("chunk"):
                res['messages'].append(
                    {
                        "type": "message",
                        "message": "Nothing found.",
                        "references": []
                    }
                )
                logger.warning(f'Nothing found for {user_attributes["id"]}')
                logger.warning(f"Prompt: {prompt}")
                logger.warning(json.dumps(bedrock_event))
                break
            chunk = bedrock_event["chunk"]
            if "attribution" not in chunk:
                res['messages'].append(
                    {
                        "type": "message",
                        "message": chunk.get("bytes", "").decode("utf-8"),
                        "references": []
                    }
                )
                continue
            for citation in chunk.get("attribution", {}).get("citations") or []:
                message = {
                    "type": "message",
                    "message": citation["generatedResponsePart"]["textResponsePart"][
                        "text"
                    ],
                    "references": [
                        {
                            "text": r["content"]["text"],
                            "link": _get_link_from_reference(r),
                        }
                        for r in (citation.get("retrievedReferences") or [])
                    ]
                }
                res['messages'].append(message)
    except:
        tb = traceback.format_exc()
        logger.error(tb)
        res['messages'] = [{"type": "error", "message": "Unexpected error", "references": []}]

    return {
        "statusCode": 200,
        "headers": {"Access-Control-Allow-Origin": "*"},
        "body": json.dumps(res),
    }


def _get_link_from_reference(r):
    original_url = r.get("metadata", {}).get("url")
    if original_url:
        return original_url
    return r["location"]["s3Location"]["uri"].replace(S3_LINK, S3_HTTPS_LINK)

