"""
Comment microservice.
Handles: create comment, list comments
Also writes notifications on comment.
"""

import os
import uuid
import time
from typing import Any, Dict

import boto3

from auth_utils import verify_token
from response_utils import success_response, error_response, get_body, get_path_param
from db_utils import put_item, get_item, query_by_partition, update_counter

ddb = boto3.resource("dynamodb")
COMMENTS_TABLE = os.environ["COMMENTS_TABLE"]
POSTS_TABLE = os.environ["POSTS_TABLE"]
NOTIFICATIONS_TABLE = os.environ["NOTIFICATIONS_TABLE"]
comments_table = ddb.Table(COMMENTS_TABLE)
posts_table = ddb.Table(POSTS_TABLE)
notifications_table = ddb.Table(NOTIFICATIONS_TABLE)


def lambda_handler(event: Dict[str, Any], context: Any) -> Dict[str, Any]:
    method = event.get("httpMethod", "")
    resource = event.get("resource", "")

    try:
        if method == "POST" and resource == "/posts/{postId}/comments":
            return handle_create_comment(event)
        elif method == "GET" and resource == "/posts/{postId}/comments":
            return handle_get_comments(event)
        else:
            return error_response(404, "Not found")
    except Exception as exc:
        print(f"Unhandled error: {exc}")
        return error_response(500, "Internal server error")

def handle_create_comment(event: Dict) -> Dict:
    user = verify_token(event)
    if not user:
        return error_response(401, "Unauthorized")

    post_id = get_path_param(event, "postId")
    body = get_body(event)
    text = body.get("text", "").strip()
    parent_comment_id = body.get("parentCommentId", None)

    if not text:
        return error_response(400, "Comment text is required")
    if len(text) > 500:
        return error_response(400, "Comment must be under 500 characters")

    comment_id = str(uuid.uuid4())
    now = int(time.time() * 1000)

    item = {
        "postId": post_id,
        "commentId": comment_id,
        "userId": user["userId"],
        "username": user["username"],
        "text": text,
        "createdAt": now,
    }
    if parent_comment_id:
        item["parentCommentId"] = parent_comment_id

    put_item(comments_table, item)
    
    if not parent_comment_id:
        update_counter(posts_table, {"postId": post_id}, "commentCount", 1)

    post = get_item(posts_table, {"postId": post_id})
    if post and post.get("userId") != user["userId"]:
        preview = text[:50] + ("..." if len(text) > 50 else "")
        notifications_table.put_item(
            Item={
                "userId": post["userId"],
                "notifId": f"{now}#{uuid.uuid4()}",
                "type": "COMMENT",
                "sourceUserId": user["userId"],
                "sourceUsername": user["username"],
                "postId": post_id,
                "message": f'{user["username"]} commented: {preview}',
                "isRead": False,
                "createdAt": now,
            }
        )

    return success_response(item, 201)

def handle_get_comments(event: Dict) -> Dict:
    post_id = get_path_param(event, "postId")
    comments = query_by_partition(
        comments_table, "postId", post_id, limit=100, scan_forward=True
    )
    return success_response({"comments": comments})
