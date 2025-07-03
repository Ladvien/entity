# AWS Deployment Guide

This guide outlines the core AWS services required to run the framework in production and demonstrates how to provision them using the Terraform Python SDK.

## Required Resources

- **Database**: either Amazon RDS for relational workloads or DynamoDB for serverless NoSQL.
- **Object Storage**: an S3 bucket for file and model storage.
- **Compute**: choose between ECS for containerized workloads or Lambda for serverless functions.
- **Networking**: a VPC with public and private subnets, plus the necessary security groups.

## Provisioning with Terraform in Python

The `python-terraform` package exposes a simple interface for executing Terraform commands from Python. The following example uses an object-oriented wrapper around the library. The class encapsulates init, plan, and apply steps.

```python
from python_terraform import Terraform

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
