# AWS Deployment Guide

<<<<<<< HEAD
This guide shows how to deploy basic AWS resources using the
``Infrastructure`` wrapper, which leverages the Terraform Python SDK
(``cdktf``).

## Example

```python
from infrastructure.aws_basic import BasicAwsInfrastructure

infra = BasicAwsInfrastructure("us-east-1")
infra.deploy()
```

The ``deploy`` method synthesizes Terraform configuration. You can then
run ``cdktf deploy`` to provision resources.
=======
This guide shows how to use the infrastructure helpers to provision a simple AWS stack.

```python
from infrastructure.aws_basic import deploy

# create an S3 bucket in us-east-1
deploy()
```

The :mod:`infrastructure` package wraps the `cdktf` library. `Infrastructure`
creates a CDK application and uses the `cdktf` CLI to deploy your stacks.

The example stack in `aws_basic.py` creates a single S3 bucket. You can extend
`BasicAwsStack` with additional AWS resources as needed.
>>>>>>> fdd01ee24c0cc5f74953ed08a44185415b3acc61
