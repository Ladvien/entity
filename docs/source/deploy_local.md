# Local Deployment

Run the agent directly on your machine during development.

1. Install dependencies with Poetry (ensures `httpx==0.27.*`):
   ```bash
   poetry install --with dev
   ```
2. Start the HTTP adapter:
   ```bash
   python -m entity.cli --config config/dev.yaml
   ```
3. Send messages to `http://localhost:8000` to interact with the agent.
