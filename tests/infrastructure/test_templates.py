from entity.infrastructure import DockerInfrastructure, AWSStandardInfrastructure


def test_docker_generate_compose():
    infra = DockerInfrastructure()
    content = infra.generate_compose()
    assert "services:" in content
    assert "agent:" in content


def test_aws_standard_templates():
    infra = AWSStandardInfrastructure()
    templates = infra.generate_templates()
    assert "provider" in templates["main.tf"]
    assert "aws_ecs_cluster" in templates["ecs.tf"]
    assert "aws_db_instance" in templates["rds.tf"]
    assert "aws_s3_bucket" in templates["s3.tf"]
