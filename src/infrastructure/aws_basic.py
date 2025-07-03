"""Example AWS deployment using :class:`Infrastructure`."""

from cdktf import TerraformStack
from cdktf_cdktf_provider_aws.provider import AwsProvider
from cdktf_cdktf_provider_aws.s3_bucket import S3Bucket
from constructs import Construct

from .infrastructure import Infrastructure


class BasicAwsStack(TerraformStack):
    def __init__(self, scope: Construct, ns: str) -> None:
        super().__init__(scope, ns)
        AwsProvider(self, "aws", region="us-east-1")
        S3Bucket(self, "bucket", bucket="entity-demo-bucket")


def deploy() -> None:
    infra = Infrastructure()
    infra.add_stack(BasicAwsStack)
    infra.deploy()


if __name__ == "__main__":  # pragma: no cover - manual example
    deploy()
