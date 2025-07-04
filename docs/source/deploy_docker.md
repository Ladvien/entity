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
