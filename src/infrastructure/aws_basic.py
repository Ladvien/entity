<<<<<<< HEAD
"""Minimal AWS example using :class:`Infrastructure`."""

from cdktf import TerraformOutput
from cdktf_cdktf_provider_aws.provider import AwsProvider
=======
"""Example AWS deployment using :class:`Infrastructure`."""

from cdktf import TerraformStack
from cdktf_cdktf_provider_aws.provider import AwsProvider
from cdktf_cdktf_provider_aws.s3_bucket import S3Bucket
from constructs import Construct
>>>>>>> fdd01ee24c0cc5f74953ed08a44185415b3acc61

from .infrastructure import Infrastructure


<<<<<<< HEAD
class BasicAwsInfrastructure(Infrastructure):
    def __init__(self, region: str) -> None:
        super().__init__("aws-basic")
        AwsProvider(self.stack, "aws", region=region)
        TerraformOutput(self.stack, "region", value=region)


if __name__ == "__main__":
    infra = BasicAwsInfrastructure("us-east-1")
    infra.deploy()
=======
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
>>>>>>> fdd01ee24c0cc5f74953ed08a44185415b3acc61
