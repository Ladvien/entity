import pytest

from entity.core.resources.container import ResourceContainer
from entity.resources.metrics import MetricsCollectorResource
from entity.resources.interfaces.vector_store import VectorStoreResource
from entity.core.plugins import InfrastructurePlugin


class DummyVectorInfra(InfrastructurePlugin):
    infrastructure_type = "vector_store"
    resource_category = "database"


class DummyVector(VectorStoreResource):
    infrastructure_dependencies = ["vector_store"]

    async def add_embedding(self, text: str) -> None:
        return None

    async def query_similar(self, query: str, k: int = 5):
        return []


@pytest.mark.asyncio
async def test_metrics_collector_injected_via_container():
    container = ResourceContainer()
    container.register("vector_store", DummyVectorInfra, {}, layer=1)
    container.register("custom_store", DummyVector, {}, layer=2)
    container.register("metrics_collector", MetricsCollectorResource, {}, layer=3)
    await container.build_all()
    vec: DummyVector = container.get("custom_store")
    pool = vec.get_connection_pool()
    assert getattr(pool, "_metrics", None) is not None

    await container.shutdown_all()
