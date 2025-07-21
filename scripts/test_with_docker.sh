#!/usr/bin/env bash
set -euo pipefail

command -v docker >/dev/null 2>&1 || {
	echo "Docker is required for integration tests" >&2
	exit 1
}

docker compose down -v --remove-orphans >/dev/null 2>&1 || true
docker compose up --build -d
trap 'docker compose down -v --remove-orphans' EXIT

PYTHONPATH=src pytest "$@"
