# AWS Deployment Guide

<<<<<<< HEAD
Deploying the Entity Pipeline Framework on AWS lets you scale reliably with managed services. This guide outlines required resources and provides a Python example that drives Terraform to create them.

## Required AWS Resources

- **Database**: Amazon RDS (PostgreSQL) or DynamoDB for durable state.
- **Storage**: S3 bucket for file uploads and static assets.
- **Compute**: ECS service or AWS Lambda function to run the agent.
- **Networking**: VPC, subnets and security groups to control access.
- **IAM Roles**: permissions for the compute layer to access the database and S3.

## Terraform with Python

The [python-terraform](https://github.com/beelit94/python-terraform) package lets you drive Terraform commands from Python. Keep your `.tf` files in an `infra/` directory and orchestrate them with a small helper class.
=======
This guide outlines the core AWS services required to run the framework in production and demonstrates how to provision them using the Terraform Python SDK.

## Required Resources

- **Database**: either Amazon RDS for relational workloads or DynamoDB for serverless NoSQL.
- **Object Storage**: an S3 bucket for file and model storage.
- **Compute**: choose between ECS for containerized workloads or Lambda for serverless functions.
- **Networking**: a VPC with public and private subnets, plus the necessary security groups.

## Provisioning with Terraform in Python

The `python-terraform` package exposes a simple interface for executing Terraform commands from Python. The following example uses an object-oriented wrapper around the library. The class encapsulates init, plan, and apply steps.
>>>>>>> 7966420636c5eba71f9deaf1bc4b88c234ab703d

```python
from python_terraform import Terraform

<<<<<<< HEAD
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

=======
class AwsDeployer:
    def __init__(self, working_dir: str):
        self.terraform = Terraform(working_dir=working_dir)

    def deploy(self) -> None:
        self.terraform.init()
        return_code, stdout, stderr = self.terraform.plan()
        if return_code != 0:
            raise RuntimeError(f"Plan failed: {stderr}")
        return_code, stdout, stderr = self.terraform.apply(auto_approve=True)
        if return_code != 0:
            raise RuntimeError(f"Apply failed: {stderr}")
```

Use Terraform configuration files in the chosen `working_dir` to define each AWS resource. A minimal example could look like:

```hcl
resource "aws_s3_bucket" "agent_storage" {
  bucket = "agent-files"
}

resource "aws_dynamodb_table" "agent_sessions" {
  name         = "agent-sessions"
  billing_mode = "PAY_PER_REQUEST"
  hash_key     = "session_id"

  attribute {
    name = "session_id"
    type = "S"
  }
}
```

Instantiate the deployer with the directory containing these files:

```python
deployer = AwsDeployer("./terraform")
deployer.deploy()
```

This approach keeps infrastructure management fully scripted while retaining the readability of Python.
>>>>>>> 7966420636c5eba71f9deaf1bc4b88c234ab703d
