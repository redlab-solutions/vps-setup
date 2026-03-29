#!/usr/bin/env python3
"""
VPS VNC Helpers — checkpoint registry, evidence collection, Telegram notifications.
"""
import json
import os
import sys
import uuid
from datetime import datetime, timezone
from pathlib import Path

VPS_SETUP = Path("/home/lincoln/vps-setup")
DEBUG_SESSIONS = VPS_SETUP / "debug-sessions"
VPS_VNC_DIR = Path.home() / ".vps-vnc"
CHECKPOINTS_FILE = VPS_VNC_DIR / "checkpoints.json"
CONFIG_FILE = VPS_VNC_DIR / "config.json"

# ── Config ────────────────────────────────────────────────────────────────────

def load_config():
    """Load Telegram bot config. Creates default if missing."""
    VPS_VNC_DIR.mkdir(parents=True, exist_ok=True)
    if CONFIG_FILE.exists():
        return json.loads(CONFIG_FILE.read_text())
    default = {"bot_token": "8571862614:AAGJVKyGCrMCAKQ5Cclb8KyoCoFvlzbMlRo", "chat_id": ""}
    CONFIG_FILE.write_text(json.dumps(default, indent=2))
    return default

def save_config(config):
    VPS_VNC_DIR.mkdir(parents=True, exist_ok=True)
    CONFIG_FILE.write_text(json.dumps(config, indent=2))

# ── Checkpoint Registry ───────────────────────────────────────────────────────

def create_checkpoint(url, action, selector, options):
    """Create a paused checkpoint. Returns checkpoint dict."""
    VPS_VNC_DIR.mkdir(parents=True, exist_ok=True)
    checkpoints = load_checkpoints()
    ckpt = {
        "id": f"ckpt_{uuid.uuid4().hex[:8]}",
        "url": url,
        "action": action,
        "selector": selector,
        "options": options,
        "timestamp": datetime.now(timezone.utc).isoformat() + "Z",
        "status": "paused"
    }
    checkpoints.append(ckpt)
    CHECKPOINTS_FILE.write_text(json.dumps(checkpoints, indent=2))
    return ckpt

def load_checkpoints():
    if not CHECKPOINTS_FILE.exists():
        return []
    return json.loads(CHECKPOINTS_FILE.read_text())

def resolve_checkpoint(checkpoint_id, chosen_option):
    """Mark checkpoint as resolved."""
    checkpoints = load_checkpoints()
    for ckpt in checkpoints:
        if ckpt["id"] == checkpoint_id:
            ckpt["status"] = "resolved"
            ckpt["chosen_option"] = chosen_option
            ckpt["resolved_at"] = datetime.now(timezone.utc).isoformat() + "Z"
            break
    CHECKPOINTS_FILE.write_text(json.dumps(checkpoints, indent=2))

def get_active_checkpoint():
    """Return the most recent paused checkpoint."""
    checkpoints = load_checkpoints()
    for ckpt in reversed(checkpoints):
        if ckpt.get("status") == "paused":
            return ckpt
    return None

# ── Evidence Collection ──────────────────────────────────────────────────────

def init_session(contexto):
    """Create session directory and metadata.json."""
    session_dir = DEBUG_SESSIONS / f"{datetime.now(timezone.utc).strftime('%Y-%m-%d')}-{contexto}"
    session_dir.mkdir(parents=True, exist_ok=True)
    meta = {
        "session": contexto,
        "started": datetime.now(timezone.utc).isoformat() + "Z",
        "goal": "",
        "iterations": []
    }
    meta_file = session_dir / "metadata.json"
    meta_file.write_text(json.dumps(meta, indent=2))
    return session_dir

def log_iteration(session_dir, iteration_data):
    """Append iteration to metadata.json."""
    meta_file = session_dir / "metadata.json"
    meta = json.loads(meta_file.read_text())
    meta["iterations"].append(iteration_data)
    meta_file.write_text(json.dumps(meta, indent=2))

def next_iteration_n(session_dir):
    """Return next iteration number."""
    meta_file = session_dir / "metadata.json"
    if not meta_file.exists():
        return 1
    meta = json.loads(meta_file.read_text())
    return len(meta.get("iterations", [])) + 1

# ── Telegram Notifications ───────────────────────────────────────────────────

def send_telegram(message):
    """Send message via Telegram bot using Python urllib."""
    import urllib.request
    import urllib.parse

    config = load_config()
    token = config.get("bot_token", "")
    chat_id = config.get("chat_id", "")

    if not token or not chat_id:
        return {"ok": False, "error": "chat_id not configured. Run: vps-vnc-helpers.py config set chat_id <id>"}

    url = f"https://api.telegram.org/bot{token}/sendMessage"
    data = urllib.parse.urlencode({"chat_id": chat_id, "text": message, "parse_mode": "Markdown"}).encode()

    try:
        req = urllib.request.Request(url, data=data)
        with urllib.request.urlopen(req, timeout=10) as resp:
            return json.loads(resp.read())
    except Exception as e:
        return {"ok": False, "error": str(e)}

def send_checkpoint_notification(checkpoint):
    """Send checkpoint alert to Telegram."""
    msg = (
        f"🛑 *CHECKPOINT*\n\n"
        f"📍 {checkpoint.get('url', 'N/A')}\n"
        f"⚠️ {checkpoint.get('action', 'Action required')}\n"
        f"🔘 Opções: {', '.join(checkpoint.get('options', []))}\n\n"
        f"⏱ Pausado — aguandando resposta"
    )
    return send_telegram(msg)

# ── CLI ──────────────────────────────────────────────────────────────────────

if __name__ == "__main__":
    cmd = sys.argv[1] if len(sys.argv) > 1 else "help"

    if cmd == "checkpoint":
        url = sys.argv[2] if len(sys.argv) > 2 else ""
        action = sys.argv[3] if len(sys.argv) > 3 else ""
        selector = sys.argv[4] if len(sys.argv) > 4 else ""
        options = sys.argv[5].split(",") if len(sys.argv) > 5 else []
        ckpt = create_checkpoint(url, action, selector, options)
        send_checkpoint_notification(ckpt)
        print(f"checkpoint:{ckpt['id']}")

    elif cmd == "resolve":
        ckpt_id = sys.argv[2] if len(sys.argv) > 2 else ""
        option = sys.argv[3] if len(sys.argv) > 3 else ""
        resolve_checkpoint(ckpt_id, option)
        print(f"resolved:{ckpt_id}:{option}")

    elif cmd == "active":
        ckpt = get_active_checkpoint()
        print(json.dumps(ckpt or {}, indent=2))

    elif cmd == "init-session":
        contexto = sys.argv[2] if len(sys.argv) > 2 else "default"
        session_dir = init_session(contexto)
        print(str(session_dir))

    elif cmd == "log":
        session_dir = Path(sys.argv[2]) if len(sys.argv) > 2 else Path(".")
        n = int(sys.argv[3]) if len(sys.argv) > 3 else 1
        action = sys.argv[4] if len(sys.argv) > 4 else ""
        url = sys.argv[5] if len(sys.argv) > 5 else ""
        selector = sys.argv[6] if len(sys.argv) > 6 else ""
        result = sys.argv[7] if len(sys.argv) > 7 else "ok"
        screenshot = sys.argv[8] if len(sys.argv) > 8 else ""
        log_iteration(session_dir, {
            "n": n, "action": action, "url": url, "selector": selector,
            "result": result, "screenshot": screenshot,
            "timestamp": datetime.now(timezone.utc).isoformat() + "Z"
        })
        print(f"logged:iteration:{n}")

    elif cmd == "config":
        config = load_config()
        key = sys.argv[2] if len(sys.argv) > 2 else ""
        value = sys.argv[3] if len(sys.argv) > 3 else ""
        if key and value:
            config[key] = value
            save_config(config)
            print(f"config:{key}={value}")
        else:
            print(json.dumps(config, indent=2))

    elif cmd == "notify":
        msg = sys.argv[2] if len(sys.argv) > 2 else ""
        result = send_telegram(msg)
        print(json.dumps(result))

    else:
        print("Commands: checkpoint, resolve, active, init-session, log, config, notify")
