"""
Layer stack.

Creates shared Lambda Layer with common utilities:
auth_utils, response_utils, db_utils, plus PyJWT and bcrypt.
"""

from aws_cdk import (
    Stack,
    aws_lambda as lambda_,
)
from constructs import Construct


class LayerStack(Stack):
    def __init__(self, scope: Construct, construct_id: str, **kwargs) -> None:
        super().__init__(scope, construct_id, **kwargs)

        self.common_layer = lambda_.LayerVersion(
            self,
            "CommonLayer",
            code=lambda_.Code.from_asset("layers/common/layer.zip"),
            compatible_runtimes=[lambda_.Runtime.PYTHON_3_12],
            description="Common utilities for InstaLite Lambda functions",
        )
