from __future__ import annotations

from typing import Dict

import aioboto3

from pipeline.plugins import ResourcePlugin, ValidationResult
from pipeline.resources import FileSystemResource
from pipeline.stages import PipelineStage


class S3FileSystem(ResourcePlugin, FileSystemResource):
    """S3-backed file storage using ``aioboto3``."""

    stages = [PipelineStage.PARSE]
    name = "filesystem"

    def __init__(self, config: Dict | None = None) -> None:
        super().__init__(config)
        self.bucket: str = str(self.config.get("bucket", ""))
        self.region: str | None = self.config.get("region")

    @classmethod
    def validate_config(cls, config: Dict) -> ValidationResult:
        if not config.get("bucket"):
            return ValidationResult.error_result("'bucket' is required")
        return ValidationResult.success_result()

    async def _execute_impl(self, context) -> None:  # pragma: no cover - no op
        return None

    async def store(self, key: str, content: bytes) -> str:
        async with aioboto3.client("s3", region_name=self.region) as s3:
            await s3.put_object(Bucket=self.bucket, Key=key, Body=content)
        return f"s3://{self.bucket}/{key}"

    async def load(self, key: str) -> bytes:
        async with aioboto3.client("s3", region_name=self.region) as s3:
            resp = await s3.get_object(Bucket=self.bucket, Key=key)
            body = await resp["Body"].read()
        return body
