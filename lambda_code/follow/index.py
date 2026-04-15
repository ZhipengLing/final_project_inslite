"""
Follow microservice.
Handles: follow, unfollow, list followers, list following
Also writes notifications on follow.
"""

import os
import uuid
import time
from typing import Any, Dict

import boto3
from botocore.exceptions import ClientError

from auth_utils import verify_token
from response_utils import success_response, error_response, get_path_param
from db_utils import get_item, query_by_partition, query_gsi, update_counter

ddb = boto3.resource("dynamodb")
FOLLOWS_TABLE = os.environ["FOLLOWS_TABLE"]
USERS_TABLE = os.environ["USERS_TABLE"]
NOTIFICATIONS_TABLE = os.environ["NOTIFICATIONS_TABLE"]
follows_table = ddb.Table(FOLLOWS_TABLE)
users_table = ddb.Table(USERS_TABLE)
notifications_table = ddb.Table(NOTIFICATIONS_TABLE)


def lambda_handler(event: Dict[str, Any], context: Any) -> Dict[str, Any]:
    method = event.get("httpMethod", "")
    resource = event.get("resource", "")

    try:
        if method == "POST" and resource == "/users/{userId}/follow":
            return handle_follow(event)
        elif method == "DELETE" and resource == "/users/{userId}/follow":
            return handle_unfollow(event)
        elif method == "GET" and resource == "/users/{userId}/followers":
            return handle_get_followers(event)
        elif method == "GET" and resource == "/users/{userId}/following":
            return handle_get_following(event)
        else:
            return error_response(404, "Not found")
    except Exception as exc:
        print(f"Unhandled error: {exc}")
        return error_response(500, "Internal server error")


def handle_follow(event: Dict) -> Dict:
    user = verify_token(event)
    if not user:
        return error_response(401, "Unauthorized")

    followee_id = get_path_param(event, "userId")
    follower_id = user["userId"]

    if follower_id == followee_id:
        return error_response(400, "Cannot follow yourself")

    now = int(time.time() * 1000)

    try:
        follows_table.put_item(
            Item={
                "followerId": follower_id,
                "followeeId": followee_id,
                "createdAt": now,
            },
            ConditionExpression="attribute_not_exists(followerId) AND attribute_not_exists(followeeId)",
        )
    except ClientError as e:
        if e.response["Error"]["Code"] == "ConditionalCheckFailedException":
            return error_response(409, "Already following")
        raise

    update_counter(users_table, {"userId": follower_id}, "followingCount", 1)
    update_counter(users_table, {"userId": followee_id}, "followerCount", 1)

    notifications_table.put_item(
        Item={
            "userId": followee_id,
            "notifId": f"{now}#{uuid.uuid4()}",
            "type": "FOLLOW",
            "sourceUserId": follower_id,
            "sourceUsername": user["username"],
            "postId": "",
            "message": f'{user["username"]} started following you',
            "isRead": False,
            "createdAt": now,
        }
    )

    return success_response({"message": "Followed"}, 201)


def handle_unfollow(event: Dict) -> Dict:
    user = verify_token(event)
    if not user:
        return error_response(401, "Unauthorized")

    followee_id = get_path_param(event, "userId")
    follower_id = user["userId"]

    existing = get_item(follows_table, {"followerId": follower_id, "followeeId": followee_id})
    if not existing:
        return error_response(404, "Not following")

    follows_table.delete_item(Key={"followerId": follower_id, "followeeId": followee_id})
    update_counter(users_table, {"userId": follower_id}, "followingCount", -1)
    update_counter(users_table, {"userId": followee_id}, "followerCount", -1)

    return success_response({"message": "Unfollowed"})


def handle_get_followers(event: Dict) -> Dict:
    user_id = get_path_param(event, "userId")
    followers = query_gsi(
        follows_table, "followee-index", "followeeId", user_id, limit=100
    )
    return success_response({"followers": followers})


def handle_get_following(event: Dict) -> Dict:
    user_id = get_path_param(event, "userId")
    following = query_by_partition(
        follows_table, "followerId", user_id, limit=100
    )
    return success_response({"following": following})
