import aioboto3

from .base import BaseInfrastructure


class S3Infrastructure(BaseInfrastructure):
    """Layer 1 infrastructure for interacting with an S3 bucket."""

    def __init__(self, bucket: str, version: str | None = None) -> None:
        """Configure the target bucket."""

        super().__init__(version)
        self.bucket = bucket
        self._session: aioboto3.Session | None = None

    def session(self) -> aioboto3.Session:
        """Return an aioboto3 session, creating one if needed."""

        if self._session is None:
            self._session = aioboto3.Session()
        return self._session

    def client(self):
        """Create an S3 client from the session."""

        return self.session().client("s3")

    async def startup(self) -> None:  # pragma: no cover - thin wrapper
        await super().startup()
        self._session = aioboto3.Session()
        self.logger.info("Using bucket %s", self.bucket)

    async def shutdown(self) -> None:  # pragma: no cover - thin wrapper
        await super().shutdown()

    def health_check(self) -> bool:
        """Return ``True`` if the bucket is reachable."""

        try:
            client = self.client()
            client.list_buckets()
            return True
        except Exception:
            return False
