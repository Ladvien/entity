import aioboto3


class S3Infrastructure:
    """Layer 1 infrastructure for interacting with an S3 bucket."""

    def __init__(self, bucket: str) -> None:
        self.bucket = bucket
        self._session: aioboto3.Session | None = None

    def session(self) -> aioboto3.Session:
        if self._session is None:
            self._session = aioboto3.Session()
        return self._session

    def client(self):
        return self.session().client("s3")
