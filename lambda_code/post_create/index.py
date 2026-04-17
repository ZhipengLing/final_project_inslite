"""
Post Creation microservice.
Handles: create post, delete post
"""
import os
import uuid
import time
from typing import Any, Dict
import boto3
from botocore.exceptions import ClientError
from auth_utils import verify_token
from response_utils import success_response, error_response, get_body
from db_utils import put_item, update_counter

ddb = boto3.resource("dynamodb")
s3 = boto3.client("s3")

POSTS_TABLE = os.environ["POSTS_TABLE"]
USERS_TABLE = os.environ["USERS_TABLE"]
LIKES_TABLE = os.environ["LIKES_TABLE"]
COMMENTS_TABLE = os.environ["COMMENTS_TABLE"]
MEDIA_BUCKET = os.environ["MEDIA_BUCKET"]

posts_table = ddb.Table(POSTS_TABLE)
users_table = ddb.Table(USERS_TABLE)
likes_table = ddb.Table(LIKES_TABLE)
comments_table = ddb.Table(COMMENTS_TABLE)


def lambda_handler(event: Dict[str, Any], context: Any) -> Dict[str, Any]:
    method = event.get("httpMethod", "")
    resource = event.get("resource", "")
    try:
        if method == "POST" and resource == "/posts":
            return handle_create_post(event)
        elif method == "DELETE" and resource == "/posts/{postId}":
            return handle_delete_post(event)
        else:
            return error_response(404, "Not found")
    except Exception as exc:
        print(f"Unhandled error: {exc}")
        return error_response(500, "Internal server error")


def handle_create_post(event: Dict) -> Dict:
    user = verify_token(event)
    if not user:
        return error_response(401, "Unauthorized")
    body = get_body(event)
    image_url = body.get("imageUrl", "")
    caption = body.get("caption", "")
    if not image_url:
        return error_response(400, "imageUrl is required")
    post_id = str(uuid.uuid4())
    now = int(time.time() * 1000)
    item = {
        "postId": post_id,
        "userId": user["userId"],
        "username": user["username"],
        "imageUrl": image_url,
        "caption": caption,
        "likeCount": 0,
        "commentCount": 0,
        "createdAt": now,
    }
    put_item(posts_table, item)
    update_counter(users_table, {"userId": user["userId"]}, "postCount", 1)
    return success_response(item, 201)


def handle_delete_post(event: Dict) -> Dict:
    user = verify_token(event)
    if not user:
        return error_response(401, "Unauthorized")

    post_id = event.get("pathParameters", {}).get("postId")
    if not post_id:
        return error_response(400, "postId is required")

    resp = posts_table.get_item(Key={"postId": post_id})
    post = resp.get("Item")
    if not post:
        return error_response(404, "Post not found")
    if post["userId"] != user["userId"]:
        return error_response(403, "Cannot delete another user's post")

    if post.get("imageUrl"):
        try:
            key = post["imageUrl"].split(f"{MEDIA_BUCKET}.s3.")[-1].split("/", 1)[-1]
            s3.delete_object(Bucket=MEDIA_BUCKET, Key=key)
        except ClientError as e:
            print(f"S3 delete warning: {e}")

    likes_resp = likes_table.query(
        KeyConditionExpression=boto3.dynamodb.conditions.Key("postId").eq(post_id)
    )
    for like in likes_resp.get("Items", []):
        likes_table.delete_item(Key={"postId": post_id, "userId": like["userId"]})

    comments_resp = comments_table.query(
        KeyConditionExpression=boto3.dynamodb.conditions.Key("postId").eq(post_id)
    )
    for comment in comments_resp.get("Items", []):
        comments_table.delete_item(Key={"postId": post_id, "commentId": comment["commentId"]})

    posts_table.delete_item(Key={"postId": post_id})
    update_counter(users_table, {"userId": user["userId"]}, "postCount", -1)

    return success_response({"message": "Post deleted"}, 200)