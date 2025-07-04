from unittest import mock

import pytest

pytest.importorskip("docker")
infrastructure = pytest.importorskip("infrastructure")
DockerInfrastructure = infrastructure.DockerInfrastructure


@mock.patch("docker.from_env")
def test_build_image(from_env):
    client = mock.Mock()
    from_env.return_value = client
    infra = DockerInfrastructure()
    infra.build_image(".", tag="agent:test")
    client.images.build.assert_called_with(
        path=".", tag="agent:test", dockerfile="Dockerfile"
    )


@mock.patch("docker.from_env")
def test_run_container(from_env):
    client = mock.Mock()
    from_env.return_value = client
    infra = DockerInfrastructure()
    infra.run_container("image", ["echo", "hi"])
    client.containers.run.assert_called()
