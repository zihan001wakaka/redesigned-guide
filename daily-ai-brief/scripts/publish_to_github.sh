#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_DIR="$(cd "$SCRIPT_DIR/.." && pwd)"
REPO_URL="${REPO_URL:-https://github.com/zihan001wakaka/redesigned-guide.git}"
BRANCH_NAME="${BRANCH_NAME:-daily-ai-brief-stable-delivery-$(date '+%Y%m%d-%H%M%S')}"
WORK_DIR="${WORK_DIR:-/tmp/redesigned-guide-publish}"
TARGET_SUBDIR="daily-ai-brief"

echo "[publish] source=$PROJECT_DIR"
echo "[publish] repo=$REPO_URL"
echo "[publish] branch=$BRANCH_NAME"

rm -rf "$WORK_DIR"
git clone "$REPO_URL" "$WORK_DIR"

cd "$WORK_DIR"
git switch -c "$BRANCH_NAME"

mkdir -p "$TARGET_SUBDIR"
rsync -a --delete \
  --exclude '.git/' \
  --exclude '.env' \
  --exclude 'config.local.json' \
  --exclude '__pycache__/' \
  --exclude '*.pyc' \
  --exclude 'data/' \
  --exclude 'reports/' \
  --exclude 'outputs/' \
  --exclude 'logs/' \
  "$PROJECT_DIR/" "$TARGET_SUBDIR/"

git add "$TARGET_SUBDIR"

if git diff --cached --quiet; then
  echo "[publish] no changes to publish."
  exit 0
fi

git commit -m "Update daily AI brief automation"
git push -u origin "$BRANCH_NAME"

echo "[publish] pushed branch: $BRANCH_NAME"
echo "[publish] open PR:"
echo "https://github.com/zihan001wakaka/redesigned-guide/compare/main...$BRANCH_NAME"
