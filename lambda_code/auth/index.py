"""
Auth microservice.
Handles: signup, login
"""

import json
import os
import uuid
import time
from typing import Any, Dict

import boto3
import bcrypt

from auth_utils import create_token
from response_utils import success_response, error_response, get_body
from db_utils import put_item, query_gsi

ddb = boto3.resource("dynamodb")
USERS_TABLE = os.environ["USERS_TABLE"]
users_table = ddb.Table(USERS_TABLE)


def lambda_handler(event: Dict[str, Any], context: Any) -> Dict[str, Any]:
    method = event.get("httpMethod", "")
    resource = event.get("resource", "")

    try:
        if method == "POST" and resource == "/auth/signup":
            return handle_signup(event)
        elif method == "POST" and resource == "/auth/login":
            return handle_login(event)
        else:
            return error_response(404, "Not found")
    except Exception as exc:
        print(f"Unhandled error: {exc}")
        return error_response(500, "Internal server error")


def handle_signup(event: Dict) -> Dict:
    body = get_body(event)
    username = body.get("username", "").strip()
    email = body.get("email", "").strip()
    password = body.get("password", "")

    if not username or not email or not password:
        return error_response(400, "username, email, and password are required")
    if len(password) < 6:
        return error_response(400, "Password must be at least 6 characters")

    existing = query_gsi(users_table, "username-index", "username", username, limit=1)
    if existing:
        return error_response(409, "Username already taken")

    user_id = str(uuid.uuid4())
    password_hash = bcrypt.hashpw(password.encode(), bcrypt.gensalt()).decode()
    now = int(time.time() * 1000)

    item = {
        "userId": user_id,
        "username": username,
        "email": email,
        "passwordHash": password_hash,
        "displayName": username,
        "bio": "",
        "avatarUrl": "",
        "postCount": 0,
        "followerCount": 0,
        "followingCount": 0,
        "createdAt": now,
    }
    put_item(users_table, item)

    token = create_token(user_id, username)
    return success_response(
        {
            "token": token,
            "user": {
                "userId": user_id,
                "username": username,
                "displayName": username,
            },
        },
        201,
    )


def handle_login(event: Dict) -> Dict:
    body = get_body(event)
    username = body.get("username", "").strip()
    password = body.get("password", "")

    if not username or not password:
        return error_response(400, "username and password are required")

    results = query_gsi(users_table, "username-index", "username", username, limit=1)
    if not results:
        return error_response(401, "Invalid credentials")

    user = results[0]
    if not bcrypt.checkpw(password.encode(), user["passwordHash"].encode()):
        return error_response(401, "Invalid credentials")

    token = create_token(user["userId"], user["username"])
    return success_response(
        {
            "token": token,
            "user": {
                "userId": user["userId"],
                "username": user["username"],
                "displayName": user.get("displayName", user["username"]),
            },
        }
    )
