# Docker Deployment

Containerize the system to run anywhere Docker is available.

1. Build the image:
   ```bash
   docker build -t entity-agent .
   ```
2. Run the container:
   ```bash
   docker run -p 8000:8000 entity-agent
   ```
3. Connect to `http://localhost:8000` just as you would locally.
4. *(Optional)* Install **Node.js** in the container if you plan to use the
   Terraform CDK-based infrastructure plugin.
