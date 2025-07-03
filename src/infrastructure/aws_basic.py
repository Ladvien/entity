"""Minimal AWS example using :class:`Infrastructure`."""

from cdktf import TerraformOutput
from cdktf_cdktf_provider_aws.provider import AwsProvider

from .infrastructure import Infrastructure


class BasicAwsInfrastructure(Infrastructure):
    def __init__(self, region: str) -> None:
        super().__init__("aws-basic")
        AwsProvider(self.stack, "aws", region=region)
        TerraformOutput(self.stack, "region", value=region)


if __name__ == "__main__":
    infra = BasicAwsInfrastructure("us-east-1")
    infra.deploy()
