"""
Storage stack.

Creates S3 bucket for image uploads with CORS configured
for presigned URL PUT uploads from the browser.
Images are publicly readable via bucket policy.
"""

from aws_cdk import (
    RemovalPolicy,
    Stack,
    aws_iam as iam,
    aws_s3 as s3,
)
from constructs import Construct


class StorageStack(Stack):
    def __init__(self, scope: Construct, construct_id: str, **kwargs) -> None:
        super().__init__(scope, construct_id, **kwargs)

        self.media_bucket = s3.Bucket(
            self,
            "MediaBucket",
            versioned=False,
            removal_policy=RemovalPolicy.DESTROY,
            auto_delete_objects=True,
            block_public_access=s3.BlockPublicAccess(
                block_public_acls=True,
                ignore_public_acls=True,
                block_public_policy=False,
                restrict_public_buckets=False,
            ),
            cors=[
                s3.CorsRule(
                    allowed_methods=[
                        s3.HttpMethods.PUT,
                        s3.HttpMethods.GET,
                    ],
                    allowed_origins=["*"],
                    allowed_headers=["*"],
                    max_age=3600,
                )
            ],
        )

        self.media_bucket.add_to_resource_policy(
            iam.PolicyStatement(
                actions=["s3:GetObject"],
                resources=[self.media_bucket.arn_for_objects("uploads/*")],
                principals=[iam.AnyPrincipal()],
            )
        )
