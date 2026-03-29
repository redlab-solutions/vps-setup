#!/bin/bash
# vps-vnc-evidence.sh — Collect screenshot evidence from webtop container
# Usage: ./vps-vnc-evidence.sh <session_dir_name> <label>
#
# Captures the EXISTING authenticated X11 session (:0) using xwd + imagemagick.
# This IS the desktop the user sees in VNC — not a new headless browser instance.
#
# Requires: xwd and imagemagick (convert) on host

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
TMP_XWD="/tmp/evidence_${TIMESTAMP}.xwd"
DEST_FILE="${EVIDENCE_DIR}/${LABEL}_${TIMESTAMP}.png"

# Capture existing X11 session (:0) as user abc — this is the authenticated desktop
sudo docker exec --user abc webtop bash -c "DISPLAY=:0 xwd -root -screen -out ${TMP_XWD}" 2>/dev/null

# Convert XWD to PNG on host (imagemagick)
if [ -f "/tmp/${TMP_XWD}" ] || sudo docker cp "webtop:${TMP_XWD}" "${TMP_XWD}" 2>/dev/null; then
    # Ensure we have the file locally
    sudo docker cp "webtop:${TMP_XWD}" "${TMP_XWD}" 2>/dev/null || true
    /usr/bin/convert "${TMP_XWD}" "${DEST_FILE}" 2>/dev/null && sudo rm -f "${TMP_XWD}" || true
    echo "${DEST_FILE}"
else
    echo "ERROR: xwd capture failed" >&2
    exit 1
fi
