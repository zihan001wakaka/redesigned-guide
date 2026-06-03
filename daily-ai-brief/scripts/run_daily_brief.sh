#!/usr/bin/env bash
set -u
set -o pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_DIR="$(cd "$SCRIPT_DIR/.." && pwd)"
LOG_DIR="$PROJECT_DIR/logs"
RUN_TS="$(date '+%Y%m%d-%H%M%S')"
LOG_FILE="$LOG_DIR/daily-ai-brief-$RUN_TS.log"
LATEST_LOG="$LOG_DIR/latest.log"
CONFIG_PATH="${CONFIG_PATH:-config.local.json}"

mkdir -p "$LOG_DIR"
cd "$PROJECT_DIR" || exit 1

if [ ! -f "$CONFIG_PATH" ]; then
  CONFIG_PATH="config.example.json"
fi

{
  echo "[run] started_at=$(date '+%Y-%m-%d %H:%M:%S %Z')"
  echo "[run] project_dir=$PROJECT_DIR"
  echo "[run] config=$CONFIG_PATH"
  python3 -m src.main --config "$CONFIG_PATH"
  status=$?
  echo "[run] finished_at=$(date '+%Y-%m-%d %H:%M:%S %Z')"
  echo "[run] exit_code=$status"
  exit "$status"
} 2>&1 | tee "$LOG_FILE"

status=${PIPESTATUS[0]}
ln -sf "$LOG_FILE" "$LATEST_LOG"
exit "$status"
