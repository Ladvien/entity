# Cloud Deployment

Use the provided infrastructure helpers to deploy to your preferred cloud provider.

1. Define your infrastructure in `infrastructure/` using CDKTF.
2. Deploy the stack:
   ```bash
   python -m infrastructure.aws_basic deploy
   ```
3. Update the configuration file with the URLs or credentials for the cloud resources.
