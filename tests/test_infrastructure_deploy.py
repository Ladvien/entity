import pytest

from entity.infrastructure import DockerInfrastructure


@pytest.mark.asyncio
async def test_docker_deploy_creates_files(tmp_path):
    infra = DockerInfrastructure({"path": str(tmp_path)})
    await infra.deploy()
    assert (tmp_path / "Dockerfile").exists()
    assert (tmp_path / "docker-compose.yml").exists()
    compose_content = (tmp_path / "docker-compose.yml").read_text()
    assert "volumes:" in compose_content
    assert "networks:" in compose_content
    assert infra.deployed

    await infra.destroy()
    assert not (tmp_path / "Dockerfile").exists()
    assert not (tmp_path / "docker-compose.yml").exists()
    assert not infra.deployed
