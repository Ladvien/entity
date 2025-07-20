#!/usr/bin/env bash
set -euo pipefail

command -v docker >/dev/null 2>&1 || {
	echo "Docker is required for integration tests" >&2
	exit 1
}

docker compose up -d
trap 'docker compose down -v' EXIT

PYTHONPATH=src pytest "$@"
