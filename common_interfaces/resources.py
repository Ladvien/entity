class BaseResource:
    """Simplified resource base class used in tests."""

    dependencies: list[str] = []

    async def initialize(self) -> None:
        pass

    async def shutdown(self) -> None:
        pass

    async def health_check(self) -> bool:  # pragma: no cover - default ok
        return True
