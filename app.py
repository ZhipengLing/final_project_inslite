#!/usr/bin/env python3
"""
Instagram-Lite CDK entry point.

Stacks:
  1. DatabaseStack   — 6 DynamoDB tables with GSIs
  2. StorageStack    — S3 image bucket with CORS
  3. LayerStack      — Shared Lambda layer (auth, response, db utils)
  4. ApiStack        — REST API + 10 Lambda microservices
  5. FrontendStack   — S3 static website
"""

import aws_cdk as cdk

from stacks.database_stack import DatabaseStack
from stacks.storage_stack import StorageStack
from stacks.layer_stack import LayerStack
from stacks.api_stack import ApiStack
from stacks.frontend_stack import FrontendStack

app = cdk.App()

db = DatabaseStack(
    app,
    "InstaLiteDB",
    description="InstaLite DynamoDB tables and GSIs",
)

storage = StorageStack(
    app,
    "InstaLiteStorage",
    description="InstaLite S3 media bucket with CORS",
)

layer = LayerStack(
    app,
    "InstaLiteLayer",
    description="InstaLite shared Lambda layer",
)

api = ApiStack(
    app,
    "InstaLiteApi",
    users_table=db.users_table,
    posts_table=db.posts_table,
    likes_table=db.likes_table,
    comments_table=db.comments_table,
    follows_table=db.follows_table,
    notifications_table=db.notifications_table,
    media_bucket=storage.media_bucket,
    common_layer=layer.common_layer,
    description="InstaLite REST API and Lambda microservices",
)
api.add_dependency(db)
api.add_dependency(storage)
api.add_dependency(layer)

frontend = FrontendStack(
    app,
    "InstaLiteFrontend",
    description="InstaLite frontend static website",
)
frontend.add_dependency(api)

cdk.CfnOutput(api, "ApiUrl", value=api.api_url)
cdk.CfnOutput(frontend, "WebsiteUrl", value=frontend.website_url)
cdk.CfnOutput(frontend, "FrontendBucketName", value=frontend.bucket_name)
cdk.CfnOutput(storage, "MediaBucketName", value=storage.media_bucket.bucket_name)

app.synth()
