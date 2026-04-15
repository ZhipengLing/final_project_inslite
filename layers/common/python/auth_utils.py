"""JWT authentication helpers for all Lambda microservices."""

import os
import time
from typing import Dict, Optional

import jwt

JWT_SECRET = os.environ.get("JWT_SECRET", "insta-lite-secret-2025")
TOKEN_EXPIRY = 86400  # 24 hours


def create_token(user_id: str, username: str) -> str:
    now = int(time.time())
    payload = {
        "userId": user_id,
        "username": username,
        "iat": now,
        "exp": now + TOKEN_EXPIRY,
    }
    return jwt.encode(payload, JWT_SECRET, algorithm="HS256")


def verify_token(event: Dict) -> Optional[Dict]:
    headers = event.get("headers") or {}
    auth = headers.get("Authorization") or headers.get("authorization") or ""
    if not auth.startswith("Bearer "):
        return None
    token = auth[7:]
    try:
        return jwt.decode(token, JWT_SECRET, algorithms=["HS256"])
    except jwt.InvalidTokenError:
        return None
