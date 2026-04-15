"""
Notification microservice.
Handles: list notifications, mark notification as read
"""

import os
from typing import Any, Dict

import boto3

from auth_utils import verify_token
from response_utils import success_response, error_response, get_path_param
from db_utils import query_by_partition

ddb = boto3.resource("dynamodb")
NOTIFICATIONS_TABLE = os.environ["NOTIFICATIONS_TABLE"]
notifications_table = ddb.Table(NOTIFICATIONS_TABLE)


def lambda_handler(event: Dict[str, Any], context: Any) -> Dict[str, Any]:
    method = event.get("httpMethod", "")
    resource = event.get("resource", "")

    try:
        if method == "GET" and resource == "/notifications":
            return handle_get_notifications(event)
        elif method == "PUT" and resource == "/notifications/{notifId}/read":
            return handle_mark_read(event)
        else:
            return error_response(404, "Not found")
    except Exception as exc:
        print(f"Unhandled error: {exc}")
        return error_response(500, "Internal server error")


def handle_get_notifications(event: Dict) -> Dict:
    user = verify_token(event)
    if not user:
        return error_response(401, "Unauthorized")

    notifications = query_by_partition(
        notifications_table, "userId", user["userId"], limit=50, scan_forward=False
    )

    unread_count = sum(1 for n in notifications if not n.get("isRead", False))

    return success_response(
        {
            "notifications": notifications,
            "unreadCount": unread_count,
        }
    )


def handle_mark_read(event: Dict) -> Dict:
    user = verify_token(event)
    if not user:
        return error_response(401, "Unauthorized")

    notif_id = get_path_param(event, "notifId")

    notifications_table.update_item(
        Key={"userId": user["userId"], "notifId": notif_id},
        UpdateExpression="SET isRead = :t",
        ExpressionAttributeValues={":t": True},
    )

    return success_response({"message": "Marked as read"})
