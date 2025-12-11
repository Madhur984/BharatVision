#!/usr/bin/env bash
# Simple commit-and-push helper. Use carefully.
# Usage: ./scripts/commit_and_push.sh "Commit message"

set -euo pipefail

MSG="${1:-Update: install scripts and setup docs}"

git add .
git commit -m "$MSG" || {
  echo "No changes to commit or commit failed.";
}
git push origin main
