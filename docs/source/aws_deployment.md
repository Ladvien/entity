# AWS Deployment Guide

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
