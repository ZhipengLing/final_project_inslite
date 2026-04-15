"""
Frontend stack.

Creates S3 bucket configured as a static website for the
Instagram-Lite single-page application.
"""

from aws_cdk import (
    RemovalPolicy,
    Stack,
    aws_s3 as s3,
)
from constructs import Construct


class FrontendStack(Stack):
    def __init__(self, scope: Construct, construct_id: str, **kwargs) -> None:
        super().__init__(scope, construct_id, **kwargs)

        website_bucket = s3.Bucket(
            self,
            "WebsiteBucket",
            website_index_document="index.html",
            website_error_document="index.html",
            public_read_access=True,
            block_public_access=s3.BlockPublicAccess(
                block_public_acls=False,
                ignore_public_acls=False,
                block_public_policy=False,
                restrict_public_buckets=False,
            ),
            removal_policy=RemovalPolicy.DESTROY,
            auto_delete_objects=True,
        )

        self.website_url = website_bucket.bucket_website_url
        self.bucket_name = website_bucket.bucket_name
