"""
Post Read microservice.
Handles: get single post, get user's posts
"""

import os
from typing import Any, Dict

import boto3

from response_utils import success_response, error_response, get_path_param, get_query_param
from db_utils import get_item, query_gsi

ddb = boto3.resource("dynamodb")
POSTS_TABLE = os.environ["POSTS_TABLE"]
posts_table = ddb.Table(POSTS_TABLE)


def lambda_handler(event: Dict[str, Any], context: Any) -> Dict[str, Any]:
    method = event.get("httpMethod", "")
    resource = event.get("resource", "")

    try:
        if method == "GET" and resource == "/posts/{postId}":
            return handle_get_post(event)
        elif method == "GET" and resource == "/users/{userId}/posts":
            return handle_get_user_posts(event)
        else:
            return error_response(404, "Not found")
    except Exception as exc:
        print(f"Unhandled error: {exc}")
        return error_response(500, "Internal server error")


def handle_get_post(event: Dict) -> Dict:
    post_id = get_path_param(event, "postId")
    if not post_id:
        return error_response(400, "postId is required")

    post = get_item(posts_table, {"postId": post_id})
    if not post:
        return error_response(404, "Post not found")

    return success_response(post)


def handle_get_user_posts(event: Dict) -> Dict:
    user_id = get_path_param(event, "userId")
    if not user_id:
        return error_response(400, "userId is required")

    limit = int(get_query_param(event, "limit", "20"))
    posts = query_gsi(
        posts_table,
        "userId-createdAt-index",
        "userId",
        user_id,
        limit=limit,
        scan_forward=False,
    )

    return success_response({"posts": posts})
