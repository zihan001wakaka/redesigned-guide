#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
SOURCE_DIR="$(cd "$SCRIPT_DIR/.." && pwd)"
TARGET_DIR="${TARGET_DIR:-$HOME/Code/daily_ai_brief}"
LABEL="com.daily-ai-brief.mvp"
PLIST_PATH="$HOME/Library/LaunchAgents/$LABEL.plist"

mkdir -p "$(dirname "$TARGET_DIR")"

if [ "$SOURCE_DIR" = "$TARGET_DIR" ]; then
  echo "Already in target directory: $TARGET_DIR"
  exit 0
fi

echo "[move] source=$SOURCE_DIR"
echo "[move] target=$TARGET_DIR"

launchctl unload "$PLIST_PATH" 2>/dev/null || true

mkdir -p "$TARGET_DIR"
rsync -a --delete \
  --exclude '.git/' \
  --exclude '.env' \
  --exclude 'config.local.json' \
  --exclude '__pycache__/' \
  --exclude '*.pyc' \
  "$SOURCE_DIR/" "$TARGET_DIR/"

chmod +x "$TARGET_DIR/scripts/"*.sh

cd "$TARGET_DIR"
"$TARGET_DIR/scripts/install_launchd.sh"

echo "[move] installed launchd from new target."
echo "[move] verify with:"
echo "  cd \"$TARGET_DIR\""
echo "  scripts/run_daily_brief.sh"
echo "  launchctl list | grep $LABEL"
echo ""
echo "[move] old source kept for safety:"
echo "  $SOURCE_DIR"
