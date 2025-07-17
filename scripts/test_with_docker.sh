#!/usr/bin/env bash
set -euo pipefail

command -v docker >/dev/null 2>&1 || {
	echo "Docker is required for integration tests" >&2
	exit 1
}

docker compose -f tests/docker-compose.yml up -d
trap 'docker compose -f tests/docker-compose.yml down -v' EXIT

PYTHONPATH=src pytest "$@"
