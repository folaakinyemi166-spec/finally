#!/usr/bin/env bash
# Build (if needed) and run the FinAlly container (PLAN.md §11).
# Usage: scripts/start_mac.sh [--build]
set -euo pipefail

cd "$(dirname "$0")/.."

IMAGE_NAME="finally"
CONTAINER_NAME="finally"
PORT="8000"

if [[ ! -f .env ]]; then
  echo "No .env file found. Copy .env.example to .env and set OPENROUTER_API_KEY first." >&2
  exit 1
fi

mkdir -p db

force_build=false
for arg in "$@"; do
  if [[ "$arg" == "--build" ]]; then
    force_build=true
  fi
done

if $force_build || ! docker image inspect "$IMAGE_NAME" >/dev/null 2>&1; then
  echo "Building $IMAGE_NAME image..."
  docker build -t "$IMAGE_NAME" .
fi

if docker ps -a --format '{{.Names}}' | grep -qx "$CONTAINER_NAME"; then
  echo "Removing existing $CONTAINER_NAME container..."
  docker rm -f "$CONTAINER_NAME" >/dev/null
fi

docker run -d \
  --name "$CONTAINER_NAME" \
  -p "${PORT}:8000" \
  -v "$(pwd)/db:/app/db" \
  --env-file .env \
  "$IMAGE_NAME"

echo "FinAlly is running at http://localhost:${PORT}"

if command -v open >/dev/null 2>&1; then
  sleep 1
  open "http://localhost:${PORT}" >/dev/null 2>&1 || true
fi
