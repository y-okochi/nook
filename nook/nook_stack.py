import os
from dataclasses import dataclass

from aws_cdk import AssetHashType, BundlingOptions, Duration, RemovalPolicy, Stack
from aws_cdk import aws_events as events
from aws_cdk import aws_events_targets as targets
from aws_cdk import aws_lambda as _lambda
from aws_cdk import aws_s3 as s3
from aws_cdk.aws_lambda import Code, Function, LayerVersion, Runtime
from constructs import Construct


@dataclass
class NookNames:
    hacker_news: str = "hacker_news"
    paper_summarizer: str = "paper_summarizer"
    reddit_explorer: str = "reddit_explorer"
    tech_feed: str = "tech_feed"
    github_trending: str = "github_trending"
    viewer: str = "viewer"


class NookStack(Stack):
    def __init__(
        self, scope: Construct, construct_id: str, env_vars: dict[str, str], **kwargs
    ) -> None:
        super().__init__(scope, construct_id, **kwargs)
        information_retriever_names = NookNames()
        root_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "lambda")

        # s3 bucket for storing the historical data
        s3_bucket = s3.Bucket(
            self,
            id="NookBucket",
            removal_policy=RemovalPolicy.DESTROY,
            auto_delete_objects=True,
        )

        # Create the common utils layer
        common_utils_layer = LayerVersion(
            self,
            "CommonUtilsLayer",
            code=Code.from_asset(
                os.path.join(root_dir, "common"),
                bundling=BundlingOptions(
                    image=_lambda.Runtime.PYTHON_3_11.bundling_image,
                    command=[
                        "bash",
                        "-c",
                        "&&".join(
                            [
                                "python -m pip install --platform manylinux2014_x86_64 --only-binary=:all: --python-version 3.11 --implementation cp -r requirements.txt -t /asset-output/python",
                                "cp -r python /asset-output/",
                            ]
                        ),
                    ],
                    user="root:root",
                ),
            ),
            compatible_runtimes=[Runtime.PYTHON_3_11],
            description="Common dependencies",
        )

        for i, app_name in enumerate(information_retriever_names.__dict__.values()):
            if app_name in [information_retriever_names.tech_feed]:
                lambda_function = _lambda.DockerImageFunction(
                    self,
                    id=app_name,
                    code=_lambda.DockerImageCode.from_image_asset(
                        directory=os.path.join(root_dir, app_name)
                    ),
                    environment={
                        "GEMINI_API_KEY": env_vars["GEMINI_API_KEY"],
                    },
                    timeout=Duration.seconds(900),
                )
            else:
                installation_command = "python -m pip install --platform manylinux2014_x86_64 --only-binary=:all: --python-version 3.11 --implementation cp -r requirements.txt -t /asset-output"
                if app_name == information_retriever_names.paper_summarizer:
                    installation_command = (
                        "python -m pip install sgmllib3k arxiv -t /asset-output && "
                        + installation_command
                    )
                lambda_function = Function(
                    self,
                    id=app_name,
                    runtime=Runtime.PYTHON_3_11,
                    code=Code.from_asset(
                        os.path.join(root_dir, app_name),
                        asset_hash_type=AssetHashType.SOURCE,
                        bundling=BundlingOptions(
                            image=_lambda.Runtime.PYTHON_3_11.bundling_image,
                            command=[
                                "bash",
                                "-c",
                                "&&".join(
                                    [
                                        installation_command,
                                        "cp -rT /asset-input /asset-output",
                                    ]
                                ),
                            ],
                            user="root:root",
                        ),
                    ),
                    handler=f"{app_name}.lambda_handler",
                    environment={
                        "GEMINI_API_KEY": env_vars["GEMINI_API_KEY"],
                        "REDDIT_CLIENT_ID": env_vars["REDDIT_CLIENT_ID"],
                        "REDDIT_CLIENT_SECRET": env_vars["REDDIT_CLIENT_SECRET"],
                        "REDDIT_USER_AGENT": env_vars["REDDIT_USER_AGENT"],
                    },
                    memory_size=2048
                    if app_name == information_retriever_names.paper_summarizer
                    else 128,
                    timeout=Duration.seconds(900),
                    layers=[common_utils_layer],
                )

            # UTC 23:00 (JST 8:00) から5分おき
            daily_23_oclock_cron_rule = events.Rule(
                self,
                id=f"Daily23OClockRule{i}",
                schedule=events.Schedule.cron(
                    minute=f"{5 * i}", hour="23", month="*", week_day="*", year="*"
                ),
            )

            lambda_function.add_function_url(
                auth_type=_lambda.FunctionUrlAuthType.NONE,
                cors=_lambda.FunctionUrlCorsOptions(
                    allowed_origins=["*"],
                    allowed_methods=[
                        _lambda.HttpMethod.GET,
                        _lambda.HttpMethod.POST,
                    ],
                ),
            )

            lambda_function.add_environment(
                key="BUCKET_NAME", value=s3_bucket.bucket_name
            )
            s3_bucket.grant_read_write(lambda_function)

            match app_name:
                case information_retriever_names.viewer:
                    pass
                case _:
                    daily_23_oclock_cron_rule.add_target(
                        targets.LambdaFunction(lambda_function)
                    )
