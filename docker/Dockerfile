FROM python:3.12-slim

# Install dependencies and node.js
RUN apt-get update && \
    apt-get install -y --no-install-recommends git curl nodejs npm && \
    rm -rf /var/lib/apt/lists/*

# Install poetry
RUN curl -sSL https://install.python-poetry.org | POETRY_HOME=/opt/poetry python3 - && \
    ln -s /opt/poetry/bin/poetry /usr/local/bin/poetry

WORKDIR /app

# Copy project metadata and install dependencies
COPY pyproject.toml poetry.lock* ./
RUN poetry install --no-interaction --no-root

# Copy the rest of the code
COPY . .

# Run programmatic checks during build
RUN poetry run black src tests && \
    poetry run isort src tests && \
    poetry run flake8 src tests && \
    poetry run mypy src && \
    bandit -r src && \
    python -m src.entity_config.validator --config config/dev.yaml && \
    python -m src.entity_config.validator --config config/prod.yaml && \
    python -m src.registry.validator && \
    pytest

CMD ["poetry", "run", "pytest"]
