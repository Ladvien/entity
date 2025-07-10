# From Development to Production

Use the same configuration file from your laptop to the cloud. Start locally,
containerize when ready, then deploy to AWS.

## 1. Local prototyping

Install dependencies and run the agent:

```bash
poetry install --with dev
poetry run entity-cli --config config/dev.yaml
```

## 2. Containerize

Build a Docker image to package your code and configuration:

```bash
docker build -t entity-agent .
docker run -p 8000:8000 entity-agent
```

## 3. Deploy to AWS

Use `AwsDeployer` or Terraform scripts to launch the container on AWS. See
[AWS deployment](deploy_aws.md) for details.
