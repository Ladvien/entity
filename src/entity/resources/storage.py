from ..infrastructure.s3_infra import S3Infrastructure


class StorageResource:
    """Layer 2 resource for S3-based file storage."""

    def __init__(self, infrastructure: S3Infrastructure) -> None:
        self.infrastructure = infrastructure

    async def upload_text(self, key: str, data: str) -> None:
        async with self.infrastructure.client() as client:
            await client.put_object(
                Bucket=self.infrastructure.bucket, Key=key, Body=data
            )
