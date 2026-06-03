#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_DIR="$(cd "$SCRIPT_DIR/.." && pwd)"

cd "$PROJECT_DIR"

if [ ! -f .env ]; then
  echo "[error] .env is missing. Create it from .env.example and fill Feishu values."
  exit 1
fi

missing=0
for key in FEISHU_APP_ID FEISHU_APP_SECRET FEISHU_FOLDER_TOKEN FEISHU_RECEIVE_ID FEISHU_RECEIVE_ID_TYPE; do
  value="$(grep -E "^${key}=" .env | tail -n 1 | cut -d= -f2- || true)"
  if [ -z "$value" ]; then
    echo "[missing] $key"
    missing=1
  else
    echo "[ok] $key"
  fi
done

if [ "$missing" -ne 0 ]; then
  echo "[error] Feishu config is incomplete."
  exit 1
fi

echo "[ok] Feishu config looks complete."
