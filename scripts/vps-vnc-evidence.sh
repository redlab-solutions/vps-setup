#!/bin/bash
# vps-vnc-evidence.sh — Collect screenshot evidence from webtop container
# Usage: ./vps-vnc-evidence.sh <session_dir_name> <label>
#
# IMPORTANT: Uses playwright-cli which captures the EXISTING authenticated
# chromium session (:0), NOT a new headless instance.
#
# Requires: playwright-cli installed in webtop container

set -e

SESSION_DIR="$1"
LABEL="$2"

if [ -z "$SESSION_DIR" ] || [ -z "$LABEL" ]; then
    echo "Usage: vps-vnc-evidence.sh <session_dir_name> <label>"
    echo "Example: vps-vnc-evidence.sh 2026-03-29-github-test login_button"
    exit 1
fi

EVIDENCE_DIR="/home/lincoln/vps-setup/debug-sessions/${SESSION_DIR}"
mkdir -p "$EVIDENCE_DIR"

TIMESTAMP=$(date +%Y%m%d_%H%M%S)
TMP_FILE="/tmp/evidence_${TIMESTAMP}.png"
DEST_FILE="${EVIDENCE_DIR}/${LABEL}_${TIMESTAMP}.png"

# playwright-cli captures the EXISTING authenticated chromium session (:0)
# This is what the user sees in VNC — not a headless new instance
docker exec webtop npx playwright-cli screenshot "about:blank" --output "$TMP_FILE" 2>/dev/null

if [ -f "/proc/$(docker inspect --format '{{.State.Pid}}' webtop)/root${TMP_FILE}" ] || docker exec test -f "$TMP_FILE" 2>/dev/null; then
    docker cp "webtop:$TMP_FILE" "$DEST_FILE"
    echo "$DEST_FILE"
else
    echo "ERROR: playwright-cli screenshot failed" >&2
    exit 1
fi
