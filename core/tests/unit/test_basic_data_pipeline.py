# Copyright 2022 Amazon.com, Inc. or its affiliates
#
# Licensed under the Apache License, Version 2.0 (the "License").
# You may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

from pathlib import Path

from aws_cdk.assertions import Match, Template
from aws_cdk.aws_lambda import Code
from aws_ddk_core.base import BaseStack
from aws_ddk_core.pipelines import DataPipeline
from aws_ddk_core.resources import S3Factory
from aws_ddk_core.stages import (
    AppFlowIngestionStage,
    AthenaSQLStage,
    GlueTransformStage,
    S3EventStage,
    SqsToLambdaStage,
)


def test_basic_pipeline(test_stack: BaseStack) -> None:
    bucket = S3Factory.bucket(
        scope=test_stack,
        id="dummy-bucket",
        environment_id="dev",
    )

    s3_event_stage = S3EventStage(
        scope=test_stack,
        id="dummy-s3-event",
        environment_id="dev",
        event_names=["Object Created"],
        bucket_name=bucket.bucket_name,
    )
    sqs_lambda_stage = SqsToLambdaStage(
        scope=test_stack,
        id="dummy-sqs-lambda",
        environment_id="dev",
        code=Code.from_asset(f"{Path(__file__).parents[2]}"),
        handler="commons.handlers.lambda_handler",
    )
    bucket.grant_read_write(sqs_lambda_stage.function)
    sqs_lambda_stage.add_alarm(
        alarm_id="dummy-sqs-lambda-throttles", alarm_metric=sqs_lambda_stage.function.metric_throttles()
    )
    glue_stage = GlueTransformStage(
        scope=test_stack,
        id="dummy-glue",
        environment_id="dev",
        job_name="dummy-glue-job",
        crawler_name="dummy-glue-crawler",
    )
    appflow_stage = AppFlowIngestionStage(
        scope=test_stack,
        id="dummy-appflow",
        environment_id="dev",
        flow_name="dummy-appflow-flow",
    )
    appflow_stage.add_alarm(
        alarm_id="dummy-appflow-timedout",
        alarm_metric=appflow_stage.state_machine.metric_timed_out(),
        alarm_threshold=1,
    )
    athena_stage = AthenaSQLStage(
        scope=test_stack,
        id="athena-sql",
        environment_id="dev",
        query_string="SELECT 1;",
        workgroup="primary",
    )

    DataPipeline(scope=test_stack, id="dummy-pipeline").add_notifications().add_stage(s3_event_stage).add_stage(
        sqs_lambda_stage
    ).add_stage(glue_stage).add_stage(appflow_stage).add_stage(athena_stage)

    template = Template.from_stack(test_stack)
    template.has_resource_properties(
        "AWS::Events::Rule",
        props={
            "Targets": [
                {
                    "Arn": {
                        "Fn::GetAtt": [
                            "dummysqslambdadummysqslambdaqueue97906E01",
                            "Arn",
                        ]
                    },
                    "Id": "Target0",
                }
            ],
        },
    )
    template.has_resource_properties(
        "AWS::SNS::Topic",
        props={
            "TopicName": Match.string_like_regexp(pattern="dummy-pipeline-notifications"),
        },
    )
    template.has_resource_properties(
        "AWS::CloudWatch::Alarm",
        props={
            "Dimensions": Match.array_with(
                pattern=[
                    Match.object_like(
                        pattern={
                            "Name": "FunctionName",
                            "Value": {"Ref": "dummysqslambdadummysqslambdafunction6E0AB03E"},
                        }
                    )
                ]
            ),
            "AlarmActions": Match.array_with(
                pattern=[Match.object_like(pattern={"Ref": "dummypipelinepipelinedummypipelinenotifications161779A9"})]
            ),
            "Threshold": 5,
        },
    )
    template.has_resource_properties(
        "AWS::CloudWatch::Alarm",
        props={
            "Dimensions": Match.array_with(
                pattern=[
                    Match.object_like(
                        pattern={
                            "Name": "StateMachineArn",
                            "Value": {"Ref": "dummyappflowdummyappflowstatemachine490B3250"},
                        }
                    )
                ]
            ),
            "Threshold": 1,
        },
    )
    template.has_resource_properties(
        "AWS::StepFunctions::StateMachine",
        props={
            "DefinitionString": {
                "Fn::Join": [
                    "",
                    Match.array_with(
                        pattern=[
                            Match.string_like_regexp(pattern="start-job-run"),
                            Match.string_like_regexp(pattern="crawl-object"),
                        ]
                    ),
                ]
            }
        },
    )
    template.has_resource_properties(
        "AWS::Lambda::Function",
        props={
            "Runtime": "python3.9",
            "Handler": "lambda_function.lambda_handler",
        },
    )
    template.has_resource_properties(
        "AWS::StepFunctions::StateMachine",
        props={
            "DefinitionString": {
                "Fn::Join": [
                    "",
                    Match.array_with(
                        pattern=[
                            Match.string_like_regexp(pattern="start-flow-execution"),
                            Match.string_like_regexp(pattern="check-flow-execution-status"),
                        ]
                    ),
                ]
            }
        },
    )
    template.has_resource_properties(
        "AWS::StepFunctions::StateMachine",
        props={
            "DefinitionString": {
                "Fn::Join": [
                    "",
                    Match.array_with(
                        pattern=[
                            Match.string_like_regexp(pattern="start-query-exec"),
                        ]
                    ),
                ]
            }
        },
    )


def test_rshift_pipeline(test_stack: BaseStack) -> None:
    bucket = S3Factory.bucket(
        scope=test_stack,
        id="dummy-bucket",
        environment_id="dev",
    )

    s3_event_stage = S3EventStage(
        scope=test_stack,
        id="dummy-s3-event",
        environment_id="dev",
        event_names=["Object Created"],
        bucket_name=bucket.bucket_name,
    )
    sqs_lambda_stage = SqsToLambdaStage(
        scope=test_stack,
        id="dummy-sqs-lambda",
        environment_id="dev",
        code=Code.from_asset(f"{Path(__file__).parents[2]}"),
        handler="commons.handlers.lambda_handler",
    )
    bucket.grant_read_write(sqs_lambda_stage.function)
    glue_stage = GlueTransformStage(
        scope=test_stack,
        id="dummy-glue",
        environment_id="dev",
        job_name="dummy-glue-job",
        crawler_name="dummy-glue-crawler",
    )

    # Chain stages with bitshift operator
    s3_event_stage >> sqs_lambda_stage >> glue_stage

    # Check both event rules were created
    template = Template.from_stack(test_stack)
    template.has_resource_properties(
        "AWS::Events::Rule",
        props={
            "Targets": [
                {
                    "Arn": {
                        "Fn::GetAtt": [
                            "dummysqslambdadummysqslambdaqueue97906E01",
                            "Arn",
                        ]
                    },
                }
            ],
        },
    )
    template.has_resource_properties(
        "AWS::Events::Rule",
        props={
            "Targets": [
                {
                    "Arn": {
                        "Ref": "dummygluedummygluestatemachine23F75506",
                    },
                }
            ],
        },
    )


def test_data_pipeline_event_rule_name(test_stack: BaseStack) -> None:
    bucket = S3Factory.bucket(
        scope=test_stack,
        id="dummy-bucket",
        environment_id="dev",
    )

    s3_event_stage = S3EventStage(
        scope=test_stack,
        id="dummy-s3-event",
        environment_id="dev",
        event_names=["Object Created"],
        bucket_name=bucket.bucket_name,
    )
    sqs_lambda_stage = SqsToLambdaStage(
        scope=test_stack,
        id="dummy-sqs-lambda",
        environment_id="dev",
        code=Code.from_asset(f"{Path(__file__).parents[2]}"),
        handler="commons.handlers.lambda_handler",
    )

    DataPipeline(scope=test_stack, id="dummy-pipeline").add_stage(s3_event_stage).add_stage(
        sqs_lambda_stage, rule_name="dummy-event"
    )

    template = Template.from_stack(test_stack)
    template.has_resource_properties(
        "AWS::Events::Rule",
        props={
            "Name": "dummy-event",
        },
    )
