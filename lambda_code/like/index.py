"""
Like microservice.
Handles: like post, unlike post, list likes
Also writes notifications on like.
"""

import os
import uuid
import time
from typing import Any, Dict

import boto3
from botocore.exceptions import ClientError

from auth_utils import verify_token
from response_utils import success_response, error_response, get_path_param
from db_utils import get_item, query_by_partition, update_counter

ddb = boto3.resource("dynamodb")
LIKES_TABLE = os.environ["LIKES_TABLE"]
POSTS_TABLE = os.environ["POSTS_TABLE"]
NOTIFICATIONS_TABLE = os.environ["NOTIFICATIONS_TABLE"]
likes_table = ddb.Table(LIKES_TABLE)
posts_table = ddb.Table(POSTS_TABLE)
notifications_table = ddb.Table(NOTIFICATIONS_TABLE)


def lambda_handler(event: Dict[str, Any], context: Any) -> Dict[str, Any]:
    method = event.get("httpMethod", "")
    resource = event.get("resource", "")

    try:
        if method == "POST" and resource == "/posts/{postId}/like":
            return handle_like(event)
        elif method == "DELETE" and resource == "/posts/{postId}/like":
            return handle_unlike(event)
        elif method == "GET" and resource == "/posts/{postId}/likes":
            return handle_get_likes(event)
        else:
            return error_response(404, "Not found")
    except Exception as exc:
        print(f"Unhandled error: {exc}")
        return error_response(500, "Internal server error")


def handle_like(event: Dict) -> Dict:
    user = verify_token(event)
    if not user:
        return error_response(401, "Unauthorized")

    post_id = get_path_param(event, "postId")
    user_id = user["userId"]
    now = int(time.time() * 1000)

    try:
        likes_table.put_item(
            Item={
                "postId": post_id,
                "userId": user_id,
                "createdAt": now,
            },
            ConditionExpression="attribute_not_exists(postId) AND attribute_not_exists(userId)",
        )
    except ClientError as e:
        if e.response["Error"]["Code"] == "ConditionalCheckFailedException":
            return error_response(409, "Already liked")
        raise

    update_counter(posts_table, {"postId": post_id}, "likeCount", 1)

    post = get_item(posts_table, {"postId": post_id})
    if post and post.get("userId") != user_id:
        notifications_table.put_item(
            Item={
                "userId": post["userId"],
                "notifId": f"{now}#{uuid.uuid4()}",
                "type": "LIKE",
                "sourceUserId": user_id,
                "sourceUsername": user["username"],
                "postId": post_id,
                "message": f'{user["username"]} liked your post',
                "isRead": False,
                "createdAt": now,
            }
        )

    return success_response({"message": "Liked"}, 201)


def handle_unlike(event: Dict) -> Dict:
    user = verify_token(event)
    if not user:
        return error_response(401, "Unauthorized")

    post_id = get_path_param(event, "postId")
    user_id = user["userId"]

    existing = get_item(likes_table, {"postId": post_id, "userId": user_id})
    if not existing:
        return error_response(404, "Not liked")

    likes_table.delete_item(Key={"postId": post_id, "userId": user_id})
    update_counter(posts_table, {"postId": post_id}, "likeCount", -1)

    return success_response({"message": "Unliked"})


def handle_get_likes(event: Dict) -> Dict:
    post_id = get_path_param(event, "postId")
    likes = query_by_partition(likes_table, "postId", post_id, limit=100)
    return success_response({"likes": likes})
