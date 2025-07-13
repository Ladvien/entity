import pytest

from entity.infrastructure import DockerInfrastructure, AWSStandardInfrastructure


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


@pytest.mark.asyncio
async def test_opentofu_deploy_creates_main(tmp_path):
    infra = AWSStandardInfrastructure(
        region="us-east-1", config={"path": str(tmp_path)}
    )
    await infra.deploy()
    assert (tmp_path / "main.tf").exists()
    assert (tmp_path / "ecs.tf").exists()
    assert (tmp_path / "rds.tf").exists()
    assert (tmp_path / "s3.tf").exists()
    assert (tmp_path / "variables.tf").exists()
    assert infra.deployed

    await infra.destroy()
    assert not (tmp_path / "main.tf").exists()
    assert not infra.deployed
