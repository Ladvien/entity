"""Example AWS Bedrock deployment."""

from __future__ import annotations

import json

from cdktf import TerraformStack
from cdktf_cdktf_provider_aws.iam_role import IamRole
from cdktf_cdktf_provider_aws.iam_role_policy_attachment import \
    IamRolePolicyAttachment
from cdktf_cdktf_provider_aws.provider import AwsProvider
from cdktf_cdktf_provider_aws.s3_bucket import S3Bucket
from constructs import Construct

from .infrastructure import Infrastructure


class BedrockLLMStack(TerraformStack):
    """Minimal infrastructure for invoking Bedrock models."""

    def __init__(self, scope: Construct, ns: str) -> None:
        super().__init__(scope, ns)
        AwsProvider(self, "aws", region="us-east-1")
        S3Bucket(self, "logs", bucket="entity-bedrock-logs")
        assume = {
            "Version": "2012-10-17",
            "Statement": [
                {
                    "Effect": "Allow",
                    "Principal": {"Service": "bedrock.amazonaws.com"},
                    "Action": "sts:AssumeRole",
                }
            ],
        }
        role = IamRole(
            self,
            "bedrockRole",
            name="entity-bedrock-role",
            assume_role_policy=json.dumps(assume),
        )
        IamRolePolicyAttachment(
            self,
            "bedrockAccess",
            role=role.name,
            policy_arn="arn:aws:iam::aws:policy/AmazonBedrockFullAccess",
        )


def deploy() -> None:
    """Deploy the Bedrock stack using Terraform CDK."""

    infra = Infrastructure()
    infra.add_stack(BedrockLLMStack)
    infra.deploy()


if __name__ == "__main__":  # pragma: no cover - manual example
    deploy()
