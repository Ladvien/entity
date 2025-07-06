import shutil

import pytest

docker = pytest.importorskip("docker")
infrastructure = pytest.importorskip("plugins.builtin.infrastructure")
DockerInfrastructure = infrastructure.DockerInfrastructure


@pytest.fixture()
def infra():
    if shutil.which("docker") is None:
        pytest.skip("Docker not installed")
    return DockerInfrastructure()


def test_build_image(infra, tmp_path):
    dockerfile = tmp_path / "Dockerfile"
    dockerfile.write_text("FROM scratch")
    infra.build_image(str(tmp_path), tag="agent:test", dockerfile="Dockerfile")
    images = [img.tags for img in docker.from_env().images.list()]
    assert any("agent:test" in tags for tags in images)


def test_run_container(infra):
    infra.run_container("alpine", ["echo", "hi"])
