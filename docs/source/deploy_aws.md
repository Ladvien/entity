# AWS Deployment Guide

Deploying the Entity Pipeline Framework on AWS lets you scale reliably with managed services. This guide outlines required resources and provides a Python example that drives Terraform to create them.

## Required AWS Resources

- **Database**: Amazon RDS (PostgreSQL) or DynamoDB for durable state.
- **Storage**: S3 bucket for file uploads and static assets.
- **Compute**: ECS service or AWS Lambda function to run the agent.
- **Networking**: VPC, subnets and security groups to control access.
- **IAM Roles**: permissions for the compute layer to access the database and S3.

## Terraform with Python

The [python-terraform](https://github.com/beelit94/python-terraform) package lets you drive Terraform commands from Python. Keep your `.tf` files in an `infra/` directory and orchestrate them with a small helper class.

```python
from python_terraform import Terraform

class EntityAWSInfra:
    """Wrap Terraform commands for object oriented clarity."""

    def __init__(self, working_dir: str = "infra") -> None:
        self.tf = Terraform(working_dir=working_dir)

    def init(self) -> None:
        self.tf.init()

    def apply(self) -> None:
        # --auto-approve avoids interactive prompts
        self.tf.apply(skip_plan=True, auto_approve=True)

if __name__ == "__main__":
    infra = EntityAWSInfra()
    infra.init()
    infra.apply()
```

### Example Terraform Files

Below is a minimal `main.tf` showing the core resources. Adjust values to fit your environment.

```hcl
provider "aws" {
  region = "us-east-1"
}

resource "aws_s3_bucket" "files" {
  bucket = "entity-files"
}

resource "aws_db_instance" "postgres" {
  allocated_storage    = 20
  engine               = "postgres"
  instance_class       = "db.t3.micro"
  name                 = "entity"
  username             = "entity"
  password             = "${var.db_password}"
  skip_final_snapshot  = true
}

resource "aws_ecs_cluster" "agent" {}
```

Run the Python helper after creating these `.tf` files to provision the infrastructure.

