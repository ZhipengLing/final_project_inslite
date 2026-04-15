"""
User Profile microservice.
Handles: get profile, update profile
"""

import os
from typing import Any, Dict

import boto3

from auth_utils import verify_token
from response_utils import success_response, error_response, get_body, get_path_param
from db_utils import get_item

ddb = boto3.resource("dynamodb")
USERS_TABLE = os.environ["USERS_TABLE"]
users_table = ddb.Table(USERS_TABLE)


def lambda_handler(event: Dict[str, Any], context: Any) -> Dict[str, Any]:
    method = event.get("httpMethod", "")
    resource = event.get("resource", "")

    try:
        if method == "GET" and resource == "/users/{userId}":
            return handle_get_profile(event)
        elif method == "PUT" and resource == "/users/{userId}":
            return handle_update_profile(event)
        else:
            return error_response(404, "Not found")
    except Exception as exc:
        print(f"Unhandled error: {exc}")
        return error_response(500, "Internal server error")


def handle_get_profile(event: Dict) -> Dict:
    user_id = get_path_param(event, "userId")
    if not user_id:
        return error_response(400, "userId is required")

    user = get_item(users_table, {"userId": user_id})
    if not user:
        return error_response(404, "User not found")

    user.pop("passwordHash", None)
    return success_response(user)


def handle_update_profile(event: Dict) -> Dict:
    current_user = verify_token(event)
    if not current_user:
        return error_response(401, "Unauthorized")

    user_id = get_path_param(event, "userId")
    if current_user["userId"] != user_id:
        return error_response(403, "Cannot edit another user's profile")

    body = get_body(event)
    update_parts = []
    expr_names = {}
    expr_values = {}

    for field in ("displayName", "bio", "avatarUrl"):
        if field in body:
            safe_name = f"#{field}"
            safe_value = f":{field}"
            update_parts.append(f"{safe_name} = {safe_value}")
            expr_names[safe_name] = field
            expr_values[safe_value] = body[field]

    if not update_parts:
        return error_response(400, "No fields to update")

    users_table.update_item(
        Key={"userId": user_id},
        UpdateExpression="SET " + ", ".join(update_parts),
        ExpressionAttributeNames=expr_names,
        ExpressionAttributeValues=expr_values,
    )

    user = get_item(users_table, {"userId": user_id})
    user.pop("passwordHash", None)
    return success_response(user)
