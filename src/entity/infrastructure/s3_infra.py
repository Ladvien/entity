import aioboto3


class S3Infrastructure:
    """Layer 1 infrastructure for interacting with an S3 bucket."""

    def __init__(self, bucket: str) -> None:
        """Configure the target bucket."""

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

    def health_check(self) -> bool:
        """Return ``True`` if the bucket is reachable."""

        try:
            client = self.client()
            client.list_buckets()
            return True
        except Exception:
            return False
