"""Shared HTTP response helpers for all Lambda microservices."""

import json
from typing import Any, Dict, Optional

CORS_HEADERS = {
    "Access-Control-Allow-Origin": "*",
    "Access-Control-Allow-Headers": "Content-Type,Authorization",
    "Access-Control-Allow-Methods": "GET,POST,PUT,DELETE,OPTIONS",
    "Content-Type": "application/json",
}


def success_response(data: Any, status_code: int = 200) -> Dict:
    return {
        "statusCode": status_code,
        "headers": CORS_HEADERS,
        "body": json.dumps(data, default=str),
    }


def error_response(status_code: int, message: str) -> Dict:
    return {
        "statusCode": status_code,
        "headers": CORS_HEADERS,
        "body": json.dumps({"error": message}),
    }


def get_body(event: Dict) -> Dict:
    body = event.get("body", "{}")
    if isinstance(body, str):
        try:
            return json.loads(body) if body else {}
        except (json.JSONDecodeError, TypeError):
            return {}
    return body if body else {}


def get_path_param(event: Dict, param: str) -> str:
    params = event.get("pathParameters") or {}
    return params.get(param, "")


def get_query_param(event: Dict, param: str, default: Optional[str] = None) -> Optional[str]:
    params = event.get("queryStringParameters") or {}
    return params.get(param, default)
