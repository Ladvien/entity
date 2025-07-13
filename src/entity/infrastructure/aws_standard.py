from __future__ import annotations

from typing import Dict

from .opentofu import OpenTofuInfrastructure


class AWSStandardInfrastructure(OpenTofuInfrastructure):
    """Basic AWS deployment using ECS, RDS and S3."""

    name = "aws-standard"
    provider = "aws"

    def __init__(self, region: str = "us-east-1", config: Dict | None = None) -> None:
        super().__init__("aws", "standard", region, config)

    # -----------------------------------------------------
    # templates
    # -----------------------------------------------------
    def generate_templates(self) -> dict[str, str]:
        templates = super().generate_templates()
        templates.update(
            {
                "ecs.tf": self._ecs_module(),
                "rds.tf": self._rds_module(),
                "s3.tf": self._s3_module(),
            }
        )
        return templates

    async def deploy(self) -> None:
        """Write AWS resources using the OpenTofu backend."""
        await super().deploy()

    def _ecs_module(self) -> str:
        return (
            'resource "aws_ecs_cluster" "agent" {}\n'
            'resource "aws_ecs_service" "agent" {\n'
            '  name        = "agent"\n'
            "  cluster     = aws_ecs_cluster.agent.id\n"
            '  launch_type = "FARGATE"\n'
            "}\n"
        )

    def _rds_module(self) -> str:
        return (
            'resource "aws_db_instance" "agent" {\n'
            '  engine               = "postgres"\n'
            '  instance_class       = "db.t3.micro"\n'
            "  allocated_storage    = 20\n"
            '  username             = "agent"\n'
            '  password             = "password"\n'
            "  skip_final_snapshot  = true\n"
            "}\n"
        )

    def _s3_module(self) -> str:
        return (
            'resource "aws_s3_bucket" "agent" {\n'
            '  bucket = "agent-${var.region}"\n'
            "}\n"
        )
