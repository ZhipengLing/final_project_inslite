"""
Feed microservice.
Handles: get feed (posts from followed users)
Uses fan-out-on-read with parallel DynamoDB queries.
"""

import os
from concurrent.futures import ThreadPoolExecutor, as_completed
from typing import Any, Dict, List

import boto3

from auth_utils import verify_token
from response_utils import success_response, error_response, get_query_param
from db_utils import query_by_partition, query_gsi

ddb = boto3.resource("dynamodb")
FOLLOWS_TABLE = os.environ["FOLLOWS_TABLE"]
POSTS_TABLE = os.environ["POSTS_TABLE"]
follows_table = ddb.Table(FOLLOWS_TABLE)
posts_table = ddb.Table(POSTS_TABLE)


def lambda_handler(event: Dict[str, Any], context: Any) -> Dict[str, Any]:
    method = event.get("httpMethod", "")
    resource = event.get("resource", "")

    try:
        if method == "GET" and resource == "/feed":
            return handle_get_feed(event)
        else:
            return error_response(404, "Not found")
    except Exception as exc:
        print(f"Unhandled error: {exc}")
        return error_response(500, "Internal server error")


def _fetch_user_posts(user_id: str, limit: int) -> List[Dict]:
    return query_gsi(
        posts_table,
        "userId-createdAt-index",
        "userId",
        user_id,
        limit=limit,
        scan_forward=False,
    )


def handle_get_feed(event: Dict) -> Dict:
    user = verify_token(event)
    if not user:
        return error_response(401, "Unauthorized")

    limit = int(get_query_param(event, "limit", "20"))
    user_id = user["userId"]

    following = query_by_partition(
        follows_table, "followerId", user_id, limit=100
    )

    # Always include own posts + posts from followed users
    followee_ids = [user_id] + [f["followeeId"] for f in following]

    all_posts: List[Dict] = []
    max_workers = min(len(followee_ids), 10)

    with ThreadPoolExecutor(max_workers=max_workers) as executor:
        futures = {
            executor.submit(_fetch_user_posts, fid, 10): fid
            for fid in followee_ids
        }
        for future in as_completed(futures):
            try:
                posts = future.result()
                all_posts.extend(posts)
            except Exception as exc:
                print(f"Error fetching posts for {futures[future]}: {exc}")

    all_posts.sort(key=lambda p: p.get("createdAt", 0), reverse=True)
    feed = all_posts[:limit]

    return success_response({"posts": feed})
