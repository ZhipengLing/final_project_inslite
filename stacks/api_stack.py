"""
API stack.

Creates a single API Gateway REST API and 10 Lambda microservices.
All routes are defined in one place for visibility.
"""

from aws_cdk import (
    Duration,
    Stack,
    aws_apigateway as apigateway,
    aws_dynamodb as dynamodb,
    aws_lambda as lambda_,
    aws_s3 as s3,
)
from constructs import Construct


class ApiStack(Stack):
    def __init__(
        self,
        scope: Construct,
        construct_id: str,
        users_table: dynamodb.ITable,
        posts_table: dynamodb.ITable,
        likes_table: dynamodb.ITable,
        comments_table: dynamodb.ITable,
        follows_table: dynamodb.ITable,
        notifications_table: dynamodb.ITable,
        media_bucket: s3.IBucket,
        common_layer: lambda_.ILayerVersion,
        **kwargs,
    ) -> None:
        super().__init__(scope, construct_id, **kwargs)

        self._common_layer = common_layer
        self._base_env = {
            "USERS_TABLE": users_table.table_name,
            "POSTS_TABLE": posts_table.table_name,
            "LIKES_TABLE": likes_table.table_name,
            "COMMENTS_TABLE": comments_table.table_name,
            "FOLLOWS_TABLE": follows_table.table_name,
            "NOTIFICATIONS_TABLE": notifications_table.table_name,
            "MEDIA_BUCKET": media_bucket.bucket_name,
            "JWT_SECRET": "insta-lite-secret-2025",
        }

        # ── Lambda Functions ─────────────────────────────────

        auth_fn = self._create_lambda("AuthFunction", "auth")
        users_table.grant_read_write_data(auth_fn)

        user_profile_fn = self._create_lambda("UserProfileFunction", "user_profile")
        users_table.grant_read_write_data(user_profile_fn)

        post_create_fn = self._create_lambda("PostCreateFunction", "post_create")
        posts_table.grant_read_write_data(post_create_fn)
        users_table.grant_read_write_data(post_create_fn)

        post_read_fn = self._create_lambda("PostReadFunction", "post_read")
        posts_table.grant_read_data(post_read_fn)

        media_fn = self._create_lambda("MediaFunction", "media")
        media_bucket.grant_put(media_fn)
        media_bucket.grant_read(media_fn)

        like_fn = self._create_lambda("LikeFunction", "like")
        likes_table.grant_read_write_data(like_fn)
        posts_table.grant_read_write_data(like_fn)
        notifications_table.grant_read_write_data(like_fn)

        comment_fn = self._create_lambda("CommentFunction", "comment")
        comments_table.grant_read_write_data(comment_fn)
        posts_table.grant_read_write_data(comment_fn)
        notifications_table.grant_read_write_data(comment_fn)

        follow_fn = self._create_lambda("FollowFunction", "follow")
        follows_table.grant_read_write_data(follow_fn)
        users_table.grant_read_write_data(follow_fn)
        notifications_table.grant_read_write_data(follow_fn)

        feed_fn = self._create_lambda("FeedFunction", "feed", timeout=60)
        follows_table.grant_read_data(feed_fn)
        posts_table.grant_read_data(feed_fn)

        notification_fn = self._create_lambda("NotificationFunction", "notification")
        notifications_table.grant_read_write_data(notification_fn)

        # ── API Gateway ──────────────────────────────────────

        api = apigateway.RestApi(
            self,
            "InstaLiteApi",
            rest_api_name="InstaLiteApi",
            description="Instagram-Lite REST API",
            default_cors_preflight_options=apigateway.CorsOptions(
                allow_origins=apigateway.Cors.ALL_ORIGINS,
                allow_methods=apigateway.Cors.ALL_METHODS,
                allow_headers=["Content-Type", "Authorization"],
            ),
            deploy_options=apigateway.StageOptions(stage_name="prod"),
        )

        # /auth/signup, /auth/login
        auth_resource = api.root.add_resource("auth")
        auth_signup = auth_resource.add_resource("signup")
        auth_login = auth_resource.add_resource("login")
        auth_signup.add_method("POST", apigateway.LambdaIntegration(auth_fn, proxy=True))
        auth_login.add_method("POST", apigateway.LambdaIntegration(auth_fn, proxy=True))

        # /users/{userId}
        users_resource = api.root.add_resource("users")
        user_resource = users_resource.add_resource("{userId}")
        user_resource.add_method("GET", apigateway.LambdaIntegration(user_profile_fn, proxy=True))
        user_resource.add_method("PUT", apigateway.LambdaIntegration(user_profile_fn, proxy=True))

        # /users/{userId}/posts
        user_posts_resource = user_resource.add_resource("posts")
        user_posts_resource.add_method("GET", apigateway.LambdaIntegration(post_read_fn, proxy=True))

        # /users/{userId}/follow, /users/{userId}/followers, /users/{userId}/following
        user_follow_resource = user_resource.add_resource("follow")
        user_follow_resource.add_method("POST", apigateway.LambdaIntegration(follow_fn, proxy=True))
        user_follow_resource.add_method("DELETE", apigateway.LambdaIntegration(follow_fn, proxy=True))
        user_followers_resource = user_resource.add_resource("followers")
        user_followers_resource.add_method("GET", apigateway.LambdaIntegration(follow_fn, proxy=True))
        user_following_resource = user_resource.add_resource("following")
        user_following_resource.add_method("GET", apigateway.LambdaIntegration(follow_fn, proxy=True))

        # /posts, /posts/{postId}
        posts_resource = api.root.add_resource("posts")
        posts_resource.add_method("POST", apigateway.LambdaIntegration(post_create_fn, proxy=True))
        post_resource = posts_resource.add_resource("{postId}")
        post_resource.add_method("GET", apigateway.LambdaIntegration(post_read_fn, proxy=True))

        # /posts/{postId}/like, /posts/{postId}/likes
        like_resource = post_resource.add_resource("like")
        like_resource.add_method("POST", apigateway.LambdaIntegration(like_fn, proxy=True))
        like_resource.add_method("DELETE", apigateway.LambdaIntegration(like_fn, proxy=True))
        likes_resource = post_resource.add_resource("likes")
        likes_resource.add_method("GET", apigateway.LambdaIntegration(like_fn, proxy=True))

        # /posts/{postId}/comments
        comments_resource = post_resource.add_resource("comments")
        comments_resource.add_method("POST", apigateway.LambdaIntegration(comment_fn, proxy=True))
        comments_resource.add_method("GET", apigateway.LambdaIntegration(comment_fn, proxy=True))

        # /media/presign
        media_resource = api.root.add_resource("media")
        presign_resource = media_resource.add_resource("presign")
        presign_resource.add_method("POST", apigateway.LambdaIntegration(media_fn, proxy=True))

        # /feed
        feed_resource = api.root.add_resource("feed")
        feed_resource.add_method("GET", apigateway.LambdaIntegration(feed_fn, proxy=True))

        # /notifications, /notifications/{notifId}/read
        notif_resource = api.root.add_resource("notifications")
        notif_resource.add_method("GET", apigateway.LambdaIntegration(notification_fn, proxy=True))
        notif_id_resource = notif_resource.add_resource("{notifId}")
        notif_read_resource = notif_id_resource.add_resource("read")
        notif_read_resource.add_method("PUT", apigateway.LambdaIntegration(notification_fn, proxy=True))

        self.api_url = api.url

    def _create_lambda(
        self,
        logical_id: str,
        code_dir: str,
        timeout: int = 30,
    ) -> lambda_.Function:
        return lambda_.Function(
            self,
            logical_id,
            runtime=lambda_.Runtime.PYTHON_3_12,
            handler="index.lambda_handler",
            code=lambda_.Code.from_asset(f"lambda_code/{code_dir}"),
            timeout=Duration.seconds(timeout),
            memory_size=256,
            layers=[self._common_layer],
            environment={**self._base_env},
        )
