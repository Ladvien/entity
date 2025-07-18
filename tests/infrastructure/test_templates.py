from entity.infrastructure import DockerInfrastructure


def test_docker_generate_compose():
    infra = DockerInfrastructure()
    content = infra.generate_compose()
    assert "services:" in content
    assert "agent:" in content
