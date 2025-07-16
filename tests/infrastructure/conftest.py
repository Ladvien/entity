import pytest

# Override heavy fixtures from tests.conftest that require Docker


@pytest.fixture(autouse=True)
async def _clear_pg_memory():
    # No-op fixture to avoid Docker dependencies in simple template tests
    yield
