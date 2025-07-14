import pytest

from entity.core.resources.container import ResourceContainer
from entity.core.plugins import InfrastructurePlugin, AgentResource
from entity.pipeline.errors import InitializationError


class DBInfra(InfrastructurePlugin):
    infrastructure_type = "db"
    stages: list = []
    dependencies: list = []


DBInfra.dependencies = []


class JumpResource(AgentResource):
    dependencies = ["db"]
    stages: list = []


JumpResource.dependencies = ["db"]


@pytest.mark.asyncio
async def test_layer_jump_violation() -> None:
    container = ResourceContainer()
    container.register("db", DBInfra, {}, layer=1)
    container.register("jump", JumpResource, {}, layer=4)

    with pytest.raises(InitializationError, match="layer rules"):
        await container.build_all()
