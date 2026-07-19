#!/usr/bin/env bash
# Stop and remove the FinAlly container. Does NOT remove db/finally.db —
# your portfolio/watchlist/trade history is preserved (PLAN.md §11).
set -euo pipefail

CONTAINER_NAME="finally"

if docker ps -a --format '{{.Names}}' | grep -qx "$CONTAINER_NAME"; then
  echo "Stopping and removing $CONTAINER_NAME..."
  docker rm -f "$CONTAINER_NAME" >/dev/null
  echo "Stopped. Your data in db/finally.db is preserved."
else
  echo "$CONTAINER_NAME is not running."
fi
