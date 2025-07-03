# AWS Deployment Guide

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
