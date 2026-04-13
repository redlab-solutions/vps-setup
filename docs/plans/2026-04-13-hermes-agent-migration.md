# Hermes Agent Migration Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Replace webtop (3.9 GB RAM) with Hermes Agent (~250 MB) + Camofox browser container (~300 MB), gaining autonomous agent capabilities via Telegram while freeing ~3.3 GB RAM.

**Architecture:** Hermes Agent runs as a native Python process (systemd service), uses OmniRoute on localhost:20128 as LLM provider, and connects to Camofox container for browser automation. Telegram gateway provides 24/7 access. Webtop and its Caddy route are removed.

**Tech Stack:** Hermes Agent (Python 3.11, Node.js v22), Camofox (Docker container), OmniRoute (existing LLM gateway), Caddy (existing reverse proxy), systemd (process management)

---

## File Structure

| Action | File | Purpose |
|--------|------|---------|
| Modify | `docker-compose.yml` | Remove webtop service, add camofox service, remove webtop_config volume |
| Modify | `Caddyfile` | Remove obsidian.redlabsolutions.com.br block |
| Modify | `.env.example` | Remove WEBTOP_PASSWORD, add Hermes/Camofox vars |
| Modify | `CLAUDE.md` | Update services list, commands, gotchas |
| Create | `systemd/hermes-agent.service` | systemd unit for Hermes gateway process |
| Create | `runbooks/hermes.md` | Operational runbook for Hermes Agent |

---

## Task 1: Pre-Migration Safety Checks

**Files:** None (validation only)

- [ ] **Step 1: Verify swap exists or create it**

Hermes + existing services need a safety net. Check current swap:

```bash
swapon --show
```

If empty (no swap), create a 4 GB swap file:

```bash
sudo fallocate -l 4G /swapfile
sudo chmod 600 /swapfile
sudo mkswap /swapfile
sudo swapon /swapfile
echo '/swapfile none swap sw 0 0' | sudo tee -a /etc/fstab
```

Verify: `free -h` should show 4.0 Gi in swap row.

- [ ] **Step 2: Backup webtop data (if anything worth keeping)**

Check if any config inside webtop volume matters:

```bash
docker exec webtop ls /config/ 2>/dev/null || echo "webtop not accessible"
```

The obsidian-vault is a bind mount (not lost). The webtop_config volume only has desktop settings. If nothing important, skip backup.

- [ ] **Step 3: Verify OmniRoute is healthy and API-compatible**

```bash
docker compose exec omniroute wget -q -O- http://localhost:20128/ | head -5
```

OmniRoute must expose an OpenAI-compatible `/v1/chat/completions` endpoint for Hermes. Confirm:

```bash
docker compose exec omniroute wget -q -O- http://localhost:20128/v1/models 2>/dev/null | head -20
```

If this returns a model list, OmniRoute is OpenAI-compatible. If not, Hermes will use OpenRouter directly instead.

- [ ] **Step 4: Commit safety checkpoint**

```bash
git add -A && git commit -m "chore: pre-migration checkpoint before webtop removal"
```

---

## Task 2: Remove Webtop from Docker Compose

**Files:**
- Modify: `docker-compose.yml:34-51` (webtop service block)
- Modify: `docker-compose.yml:86` (webtop_config volume)

- [ ] **Step 1: Stop webtop gracefully**

```bash
docker compose stop webtop
```

Verify it stopped: `docker ps | grep webtop` should return nothing.

- [ ] **Step 2: Remove webtop service from docker-compose.yml**

Remove the entire webtop block (lines 34-51):

```yaml
# REMOVE THIS ENTIRE BLOCK:
  webtop:
    image: lscr.io/linuxserver/webtop:ubuntu-lxqt
    container_name: webtop
    restart: unless-stopped
    security_opt:
      - seccomp:unconfined
    ports:
      - "127.0.0.1:3000:3000"
      - "127.0.0.1:5900:5900"
    environment:
      - PUID=${PUID}
      - PGID=${PGID}
      - TZ=America/Sao_Paulo
      - PASSWORD=${WEBTOP_PASSWORD}
    volumes:
      - /home/lincoln/obsidian-vault:/config/obsidian-vault
      - webtop_config:/config
    shm_size: "1gb"
```

Remove `webtop_config:` from the `volumes:` section at the bottom.

- [ ] **Step 3: Remove webtop container and volume**

```bash
docker compose rm -f webtop
docker volume rm vps-setup_webtop_config 2>/dev/null || echo "volume already gone"
```

- [ ] **Step 4: Commit**

```bash
git add docker-compose.yml
git commit -m "chore: remove webtop service from Docker Compose stack"
```

---

## Task 3: Update Caddyfile

**Files:**
- Modify: `Caddyfile:11-14` (obsidian block)

- [ ] **Step 1: Remove the obsidian Caddy route**

Delete lines 11-14:

```
# REMOVE THIS ENTIRE BLOCK:
obsidian.redlabsolutions.com.br {
    bind {env.TAILSCALE_IP}
    reverse_proxy localhost:3000
}
```

The final Caddyfile should be:

```
{
    email lincoln@redlabsolutions.com.br
    acme_dns cloudflare {env.CLOUDFLARE_API_TOKEN}
}

code.redlabsolutions.com.br {
    bind {env.TAILSCALE_IP}
    reverse_proxy http://localhost:8443
}

llm-proxy.redlabsolutions.com.br {
    reverse_proxy http://localhost:20128
}
```

- [ ] **Step 2: Reload Caddy**

```bash
docker compose restart caddy
```

Verify: `docker compose logs caddy --tail 5` should show clean reload, no errors.

- [ ] **Step 3: Commit**

```bash
git add Caddyfile
git commit -m "chore: remove obsidian/webtop Caddy route"
```

---

## Task 4: Add Camofox Container

**Files:**
- Modify: `docker-compose.yml` (add camofox service)
- Modify: `.env.example` (add CAMOFOX vars)

- [ ] **Step 1: Add camofox service to docker-compose.yml**

Add after the omniroute service, before `volumes:`:

```yaml
  camofox:
    image: jo-inc/camofox-browser
    container_name: camofox
    restart: unless-stopped
    network_mode: host
    environment:
      - CAMOFOX_PORT=9377
    logging:
      driver: "json-file"
      options:
        max-size: "10m"
        max-file: "3"
```

Note: `network_mode: host` is required so Hermes (native process) can reach Camofox on `localhost:9377`.

- [ ] **Step 2: Update .env.example**

Remove the line:
```
WEBTOP_PASSWORD=change_me_strong_password
```

Add after OmniRoute section:
```
# Camofox Browser (for Hermes Agent)
CAMOFOX_URL=http://localhost:9377
```

- [ ] **Step 3: Pull and start camofox**

```bash
docker compose pull camofox
docker compose up -d camofox
```

First run downloads ~300 MB (Camoufox browser). Verify:

```bash
docker compose logs camofox --tail 10
```

Should show server listening on port 9377.

- [ ] **Step 4: Verify Camofox health**

```bash
curl -s http://localhost:9377/health 2>/dev/null || echo "checking with wget"
```

If health endpoint returns OK, Camofox is ready.

- [ ] **Step 5: Commit**

```bash
git add docker-compose.yml .env.example
git commit -m "feat: add Camofox browser container for Hermes Agent"
```

---

## Task 5: Install Hermes Agent

**Files:** None (native installation)

- [ ] **Step 1: Run the Hermes installer**

```bash
curl -fsSL https://raw.githubusercontent.com/NousResearch/hermes-agent/main/scripts/install.sh | bash
```

This installs: uv, Python 3.11, Node.js v22, ripgrep, ffmpeg, clones the repo, creates venv, and sets up the `hermes` command.

- [ ] **Step 2: Reload shell and verify**

```bash
source ~/.bashrc
hermes version
```

Should print version info without errors.

- [ ] **Step 3: Run diagnostics**

```bash
hermes doctor
```

Should report what's configured and what's missing. Expect API keys to be missing (we configure those next).

---

## Task 6: Configure Hermes LLM Provider

**Files:**
- Modify: `~/.hermes/.env` (API keys)
- Modify: `~/.hermes/config.yaml` (provider config)

- [ ] **Step 1: Determine OmniRoute API compatibility**

From Task 1 Step 3 we know if OmniRoute exposes `/v1/chat/completions`. If yes:

Set Hermes to use OmniRoute as a custom OpenAI-compatible endpoint:

```bash
hermes config set LLM_PROVIDER openai_compatible
hermes config set OPENAI_BASE_URL http://localhost:20128/v1
hermes config set OPENAI_API_KEY "$(grep OMNIROUTE_INITIAL_PASSWORD /home/lincoln/vps-setup/.env | cut -d= -f2)"
```

If OmniRoute is NOT OpenAI-compatible, use OpenRouter instead:

```bash
hermes config set OPENROUTER_API_KEY your_openrouter_key_here
hermes model
# Select: openrouter -> hermes-3-llama-3.1-405b (or preferred model)
```

- [ ] **Step 2: Verify LLM connection**

```bash
hermes chat -q "Hello, what model are you?"
```

Should get a response. If timeout or error, check the provider config.

- [ ] **Step 3: Configure workspace**

```bash
hermes config set WORKSPACE /home/lincoln/workspace
```

This tells Hermes where to operate for file-related tasks.

---

## Task 7: Configure Hermes Browser + Camofox

**Files:**
- Modify: `~/.hermes/.env` (CAMOFOX_URL)

- [ ] **Step 1: Set Camofox URL**

```bash
echo 'CAMOFOX_URL=http://localhost:9377' >> ~/.hermes/.env
```

- [ ] **Step 2: Enable browser toolset**

```bash
hermes tools
# Select: enable browser toolset
```

Or set via config:

```bash
hermes config set toolsets '["hermes-cli", "browser"]'
```

- [ ] **Step 3: Test browser automation**

```bash
hermes chat -q "Navigate to https://example.com and tell me what you see"
```

Should use Camofox, navigate, and return page content. If it falls back to web_search, check `CAMOFOX_URL` is set correctly.

- [ ] **Step 4: Test vision/screenshot**

```bash
hermes chat -q "Take a screenshot of https://example.com and describe it"
```

Should use `browser_vision` tool, take screenshot, and describe the page visually.

---

## Task 8: Configure Telegram Gateway

**Files:**
- Modify: `~/.hermes/config.yaml` (Telegram config)
- Modify: `~/.hermes/.env` (TELEGRAM_BOT_TOKEN)

- [ ] **Step 1: Create a new Telegram bot**

Talk to @BotFather on Telegram:
1. Send `/newbot`
2. Name: `Hermes VPS Agent`
3. Username: `hermes_vps_agent` (or similar)
4. Copy the bot token returned

- [ ] **Step 2: Configure Telegram in Hermes**

```bash
hermes gateway setup
# Select: Telegram
# Paste bot token when prompted
```

Or manually:

```bash
hermes config set TELEGRAM_BOT_TOKEN your_bot_token_here
```

- [ ] **Step 3: Set allowed users (security)**

Get your Telegram user ID (talk to @userinfobot on Telegram).

```bash
hermes config set TELEGRAM_ALLOWED_USERS '["your_telegram_user_id"]'
```

This prevents anyone else from commanding your VPS via the bot.

- [ ] **Step 4: Set home platform**

```bash
hermes config set HOME_PLATFORM telegram
```

This makes Telegram the primary interface (reports, cron results go there).

- [ ] **Step 5: Test Telegram gateway**

Start the gateway interactively first:

```bash
hermes gateway start
```

Send a message to the bot on Telegram. It should respond. Ctrl+C to stop.

---

## Task 9: Create systemd Service

**Files:**
- Create: `systemd/hermes-agent.service`

- [ ] **Step 1: Create the service file**

Find the hermes binary path first:

```bash
which hermes
# Expected: /home/lincoln/.local/bin/hermes
```

Create `/home/lincoln/vps-setup/systemd/hermes-agent.service`:

```ini
[Unit]
Description=Hermes Agent Telegram Gateway
After=network-online.target docker.service
Wants=network-online.target

[Service]
Type=simple
User=lincoln
EnvironmentFile=/home/lincoln/.hermes/.env
ExecStart=/home/lincoln/.local/bin/hermes gateway start
Restart=on-failure
RestartSec=10
StandardOutput=journal
StandardError=journal

# Security hardening
NoNewPrivileges=true
ProtectSystem=strict
ReadWritePaths=/home/lincoln /tmp
PrivateTmp=true

[Install]
WantedBy=multi-user.target
```

- [ ] **Step 2: Install and enable the service**

```bash
sudo cp /home/lincoln/vps-setup/systemd/hermes-agent.service /etc/systemd/system/
sudo systemctl daemon-reload
sudo systemctl enable hermes-agent
sudo systemctl start hermes-agent
```

- [ ] **Step 3: Verify it's running**

```bash
sudo systemctl status hermes-agent
```

Should show `active (running)`. Test via Telegram - send a message to the bot.

- [ ] **Step 4: Check logs**

```bash
sudo journalctl -u hermes-agent -f
```

Should show gateway startup and Telegram polling. Ctrl+C to stop watching.

- [ ] **Step 5: Commit**

```bash
git add systemd/hermes-agent.service
git commit -m "feat: add systemd service for Hermes Agent gateway"
```

---

## Task 10: Update Documentation

**Files:**
- Modify: `CLAUDE.md`
- Create: `runbooks/hermes.md`

- [ ] **Step 1: Update CLAUDE.md services section**

Replace the webtop entry and add Hermes/Camofox entries:

```markdown
## Services

- **caddy**: Reverse proxy (`network_mode: host`) — reads `Caddyfile`, Cloudflare DNS-01 TLS
- **code-server**: VS Code in browser — port `127.0.0.1:8443`, Tailscale-only (`bind {env.TAILSCALE_IP}`)
- **omniroute**: LLM API gateway — port `127.0.0.1:20128`, exposed publicly via `llm-proxy.redlabsolutions.com.br` (no bind = all interfaces, Cloudflare Proxy)
- **camofox**: Browser automation — port `localhost:9377` (`network_mode: host`), anti-detection Firefox for Hermes Agent
- **hermes-agent**: Autonomous AI agent — native Python process (systemd), Telegram gateway, uses OmniRoute as LLM provider
```

- [ ] **Step 2: Update CLAUDE.md commands section**

Add Hermes commands:

```markdown
## Commands

```bash
# Docker Compose
docker compose up -d             # Start all services
docker compose logs -f           # Tail logs
docker compose restart caddy     # Reload Caddy config after Caddyfile changes
docker compose pull omniroute && docker compose up -d omniroute  # Update OmniRoute

# Hermes Agent
sudo systemctl status hermes-agent    # Check gateway status
sudo journalctl -u hermes-agent -f    # Tail gateway logs
sudo systemctl restart hermes-agent   # Restart gateway
hermes doctor                         # Run diagnostics
hermes chat -q "message"              # One-off chat (CLI)
hermes model                          # Switch LLM provider/model
hermes tools                          # Configure toolsets
hermes update                         # Update to latest version
```
```

- [ ] **Step 3: Update CLAUDE.md gotchas**

Add these entries:

```markdown
- Hermes uses OmniRoute at `http://localhost:20128/v1` as LLM provider — if OmniRoute is down, Hermes falls back to error (or configure OpenRouter as backup)
- Camofox runs on `network_mode: host` so Hermes can reach it on `localhost:9377`
- Hermes config lives in `~/.hermes/` (not in this repo) — `.env` there has API keys
- Hermes Telegram gateway runs as systemd service `hermes-agent` — not in Docker
- Hermes workspace is `/home/lincoln/workspace` — same as code-server
- `data/`, `debug-sessions/`, `.env.save` are gitignored
```

- [ ] **Step 4: Create runbooks/hermes.md**

```markdown
# Hermes Agent Runbook

## Overview
Hermes Agent is an autonomous AI agent by Nous Research. Runs as a native Python process on this VPS, accessible via Telegram 24/7.

## Architecture
- **Process:** systemd service `hermes-agent`
- **LLM:** OmniRoute (`http://localhost:20128/v1`) or OpenRouter
- **Browser:** Camofox container (`localhost:9377`)
- **Interface:** Telegram bot
- **Workspace:** `/home/lincoln/workspace`
- **Config:** `~/.hermes/`

## Common Operations

### Check Status
```bash
sudo systemctl status hermes-agent
```

### View Logs
```bash
sudo journalctl -u hermes-agent -f           # Live tail
sudo journalctl -u hermes-agent --since "1h"  # Last hour
```

### Restart
```bash
sudo systemctl restart hermes-agent
```

### Update
```bash
hermes update
sudo systemctl restart hermes-agent
```

### Switch Model
```bash
hermes model  # Interactive selection
# Or via Telegram: /model openrouter:hermes-3-llama-3.1-405b
```

### Enable/Disable Tools
```bash
hermes tools  # Interactive toggle
```

## Troubleshooting

### Gateway not responding on Telegram
1. Check service: `sudo systemctl status hermes-agent`
2. Check logs: `sudo journalctl -u hermes-agent --since "5m"`
3. Check OmniRoute: `docker compose ps omniroute`
4. Restart: `sudo systemctl restart hermes-agent`

### Browser tools not working
1. Check Camofox: `docker compose ps camofox`
2. Check health: `curl -s http://localhost:9377/health`
3. Check Hermes env: `grep CAMOFOX_URL ~/.hermes/.env`
4. Restart Camofox: `docker compose restart camofox`

### LLM errors
1. Check OmniRoute: `docker compose logs omniroute --tail 20`
2. If OmniRoute down: `docker compose up -d omniroute`
3. Switch to OpenRouter backup: `hermes model` → select OpenRouter

### Memory/skills full
1. Check disk: `du -sh ~/.hermes/memories/ ~/.hermes/skills/`
2. Hermes auto-manages with FTS5, but manual cleanup:
   ```bash
   ls ~/.hermes/memories/
   ls ~/.hermes/skills/
   ```

## Config Location
- Main config: `~/.hermes/config.yaml`
- API keys: `~/.hermes/.env`
- Memories: `~/.hermes/memories/`
- Skills: `~/.hermes/skills/`
- Sessions: `~/.hermes/sessions/`
- Logs: journalctl (systemd) + `~/.hermes/logs/`
```

- [ ] **Step 5: Commit**

```bash
git add CLAUDE.md runbooks/hermes.md
git commit -m "docs: update CLAUDE.md for Hermes Agent + add runbook"
```

---

## Task 11: Final Validation

**Files:** None (testing only)

- [ ] **Step 1: Verify all Docker services are healthy**

```bash
docker compose ps
```

Expected: caddy (Up), code-server (Up), omniroute (Up or Unhealthy — healthcheck bug is known), camofox (Up). webtop should NOT appear.

- [ ] **Step 2: Verify RAM savings**

```bash
free -h
```

Expected: ~3-4 GB more available RAM compared to before migration. Target: <3 GB used.

- [ ] **Step 3: Verify Hermes via Telegram**

Send a message to the Hermes bot on Telegram:
- "What's the current disk usage?" — should use shell tools
- "Navigate to https://example.com and take a screenshot" — should use Camofox
- "What tools do you have available?" — should list 47 tools

- [ ] **Step 4: Verify Hermes survives reboot**

```bash
sudo systemctl is-enabled hermes-agent
```

Should print `enabled`. This means it auto-starts on boot.

- [ ] **Step 5: Verify code-server still works**

Open code-server via Tailscale (code.redlabsolutions.com.br). Confirm workspace loads and files are accessible.

- [ ] **Step 6: Final commit**

```bash
git add -A
git commit -m "chore: complete Hermes Agent migration — webtop removed, Hermes + Camofox added"
```

---

## Rollback Plan

If something goes wrong and you need webtop back:

1. Stop Hermes: `sudo systemctl disable --now hermes-agent`
2. Revert the git commits:
   ```bash
   git log --oneline -10  # find the pre-migration commit
   git revert HEAD~N..HEAD  # revert migration commits
   ```
3. Or manually restore webtop block in docker-compose.yml and Caddyfile from git history
4. `docker compose up -d` brings webtop back
5. Uninstall Hermes: `rm -rf ~/hermes-agent/ ~/.hermes/ ~/.local/bin/hermes`

---

## Notes

- **OmniRoute as LLM provider:** This is the biggest assumption. If OmniRoute doesn't expose an OpenAI-compatible API at `/v1/chat/completions`, Hermes will need OpenRouter instead (adds external dependency but works reliably).
- **Camofox vs Browserbase:** Camofox is self-hosted (free, local). Browserbase is cloud (paid, more features). Start with Camofox, upgrade if needed.
- **Hermes memory growth:** Hermes auto-manages memory with FTS5 and summarization, but `~/.hermes/` will grow over time. Monitor with `du -sh ~/.hermes/`.
- **systemd hardening:** The service file uses `ProtectSystem=strict` with `ReadWritePaths=/home/lincoln`. Hermes can only write to the home directory and /tmp.
