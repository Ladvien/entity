# Production Deployment

This project can run entirely on your machine, but you can containerize the services for a reproducible environment.

1. Build the `ollama` image provided in the repository:

```bash
docker compose build ollama
```

2. Start the stack in the background:

```bash
docker compose up -d
```

3. Run agents or tests as needed while the services are running.

4. When finished, shut everything down and remove volumes:

```bash
docker compose down -v
```

See `install_docker.sh` for a quick installation script on Ubuntu.
