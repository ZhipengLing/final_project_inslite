"""
Search microservice.
Handles: search users by username
"""

import os
from typing import Any, Dict

import boto3
from boto3.dynamodb.conditions import Attr

from response_utils import success_response, error_response

ddb = boto3.resource("dynamodb")
USERS_TABLE = os.environ["USERS_TABLE"]
users_table = ddb.Table(USERS_TABLE)


def lambda_handler(event: Dict[str, Any], context: Any) -> Dict[str, Any]:
    method = event.get("httpMethod", "")
    resource = event.get("resource", "")

    try:
        if method == "GET" and resource == "/search/users":
            return handle_search_users(event)
        else:
            return error_response(404, "Not found")
    except Exception as exc:
        print(f"Unhandled error: {exc}")
        return error_response(500, "Internal server error")


def handle_search_users(event: Dict) -> Dict:
    params = event.get("queryStringParameters") or {}
    query = params.get("q", "").strip().lower()

    if not query:
        return error_response(400, "Query parameter 'q' is required")
    if len(query) < 1:
        return error_response(400, "Query too short")

    resp = users_table.scan(
        FilterExpression=Attr("username").contains(query),
        ProjectionExpression="userId, username, displayName, avatarUrl, followerCount, followingCount",
        Limit=20,
    )

    users = resp.get("Items", [])
    return success_response({"users": users, "count": len(users)})