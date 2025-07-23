"""Resource for storing text to an S3 bucket."""

from entity.infrastructure.s3_infra import S3Infrastructure


class StorageResource:
    """Layer 2 resource for S3-based file storage."""

    def __init__(self, infrastructure: S3Infrastructure) -> None:
        """Initialize the resource with an S3 infrastructure instance."""

        self.infrastructure = infrastructure

    async def upload_text(self, key: str, data: str) -> None:
        """Upload plain text to the configured bucket under the given key."""

        async with self.infrastructure.client() as client:
            await client.put_object(
                Bucket=self.infrastructure.bucket, Key=key, Body=data
            )
