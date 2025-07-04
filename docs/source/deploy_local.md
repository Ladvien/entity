# Local Deployment

Run the agent directly on your machine during development.

1. Install dependencies:
   ```bash
   pip install -e .
   ```
2. Start the HTTP adapter:
   ```bash
   python -m entity.cli --config config/dev.yaml
   ```
3. Send messages to `http://localhost:8000` to interact with the agent.
