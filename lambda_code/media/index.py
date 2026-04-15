"""
Media Upload microservice.
Handles: generate presigned URL for S3 image upload
"""

import os
import uuid
from typing import Any, Dict

import boto3
from botocore.config import Config

from auth_utils import verify_token
from response_utils import success_response, error_response, get_body

REGION = os.environ.get("AWS_REGION", "us-west-2")
s3_client = boto3.client(
    "s3",
    region_name=REGION,
    config=Config(
        signature_version="s3v4",
        s3={"addressing_style": "virtual"},
    ),
)
MEDIA_BUCKET = os.environ["MEDIA_BUCKET"]


def lambda_handler(event: Dict[str, Any], context: Any) -> Dict[str, Any]:
    method = event.get("httpMethod", "")
    resource = event.get("resource", "")

    try:
        if method == "POST" and resource == "/media/presign":
            return handle_presign(event)
        else:
            return error_response(404, "Not found")
    except Exception as exc:
        print(f"Unhandled error: {exc}")
        return error_response(500, "Internal server error")


def handle_presign(event: Dict) -> Dict:
    user = verify_token(event)
    if not user:
        return error_response(401, "Unauthorized")

    body = get_body(event)
    content_type = body.get("contentType", "image/jpeg")
    filename = body.get("filename", "photo.jpg")

    if not content_type.startswith("image/"):
        return error_response(400, "Only image uploads are supported")

    ext = filename.rsplit(".", 1)[-1] if "." in filename else "jpg"
    key = f"uploads/{user['userId']}/{uuid.uuid4()}.{ext}"

    upload_url = s3_client.generate_presigned_url(
        "put_object",
        Params={
            "Bucket": MEDIA_BUCKET,
            "Key": key,
            "ContentType": content_type,
        },
        ExpiresIn=300,
    )

    image_url = f"https://{MEDIA_BUCKET}.s3.{REGION}.amazonaws.com/{key}"

    return success_response(
        {
            "uploadUrl": upload_url,
            "imageUrl": image_url,
            "key": key,
        }
    )
