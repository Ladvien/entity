#!/usr/bin/env bash
set -euo pipefail

docker compose -f tests/docker-compose.yml up -d
trap 'docker compose -f tests/docker-compose.yml down -v' EXIT

PYTHONPATH=src pytest "$@"
