# VPS Setup (Contabo)

Docker Compose infra: Caddy reverse proxy + code-server + OmniRoute (LLM gateway). Hermes Agent + Camofox run as native systemd services.

## Commands

```bash
docker compose up -d             # Start all services
docker compose logs -f           # Tail logs
docker compose restart caddy     # Reload Caddy config after Caddyfile changes
docker compose pull omniroute && docker compose up -d omniroute  # Update OmniRoute

# Hermes Agent
systemctl --user status hermes-gateway    # Check gateway status
journalctl --user -u hermes-gateway -f    # Tail gateway logs
systemctl --user restart hermes-gateway   # Restart gateway
hermes doctor                         # Run diagnostics
hermes chat -q "message"              # One-off chat (CLI)
hermes model                          # Switch LLM provider/model
hermes tools                          # Configure toolsets
hermes update                         # Update to latest version

# Camofox Browser
sudo systemctl status camofox         # Check browser server
sudo systemctl restart camofox        # Restart browser server
```

## Services

- **caddy**: Reverse proxy (`network_mode: host`) — reads `Caddyfile`, Cloudflare DNS-01 TLS
- **code-server**: VS Code in browser — port `127.0.0.1:8443`, Tailscale-only (`bind {env.TAILSCALE_IP}`)
- **omniroute**: LLM API gateway — port `127.0.0.1:20128`, exposed publicly via `llm-proxy.redlabsolutions.com.br` (no bind = all interfaces, Cloudflare Proxy)
- **hermes-agent**: Autonomous AI agent — native Python process (systemd service `hermes-agent`), Telegram gateway, uses z.ai/GLM-5-turbo as LLM provider
- **camofox**: Browser automation — native Node.js process (systemd service `camofox`), anti-detection Firefox for Hermes Agent, port `localhost:9377`

## Gotchas

- Caddy uses `CLOUDFLARE_API_TOKEN` for DNS-01 TLS challenge — must be set in `.env`
- `TAILSCALE_IP` must be set for Caddy to bind correctly on Tailscale interface
- `.env` exists (gitignored); `.env.example` is the template
- OmniRoute healthcheck uses `/` (root), not `/api/health` (requires auth → 401)
- UFW allows 80/443 on all interfaces (Cloudflare needs public access for llm-proxy)
- code-server remains Tailscale-only (bind TAILSCALE_IP)
- OmniRoute v3.5.5+ required — v3.5.1 had bug corrupting payload after fallbacks (400 "Improperly formed request" on Kiro provider)
- OmniRoute ModelSync returns 400 for Kiro connections at startup — this is normal (Kiro has no model listing endpoint), requests still work
- OmniRoute log retention: `APP_LOG_RETENTION_DAYS=3`, `CALL_LOG_MAX_ENTRIES=200` — prevents unbounded growth (was 873 MB in 4 days)
- Docker logs use `json-file` driver with rotation (`max-size: 10m`, `max-file: 3`)
- `data/`, `debug-sessions/`, `.env.save` are gitignored
- Hermes config lives in `~/.hermes/` (not in this repo) — `.env` there has API keys
- Hermes manages its own user-level systemd service (`hermes-gateway`) — use `systemctl --user` to manage, NOT system-level
- Hermes workspace is `/home/lincoln/workspace` — same as code-server
- Camofox runs natively on port 9377 — Hermes browser tools route through it
- Camofox runs natively on port 9377 — Hermes browser tools route through it
- Camofox idle memory: ~50 MB. Launches browser on demand, auto-shuts down after 5 min idle
- Camofox needs Node.js v22+ (uses nvm v24 at `/home/lincoln/.nvm/versions/node/v24.14.0/bin/node`)
- Hermes uses z.ai/GLM-5-turbo as LLM provider (configurable with `hermes model`)
- `TELEGRAM_BOT_TOKEN` is in `~/.hermes/.env` — Hermes Telegram bot is separate from the Claude Code Telegram plugin

## Vault
Sessões em: /home/lincoln/obsidian-vault/Áreas/Dev/Projetos/vps-setup/Sessões/

## Paths principais
- Workspace: /home/lincoln/vps-setup/
- Vault hub: /home/lincoln/obsidian-vault/Áreas/Dev/Projetos/vps-setup/vps-setup.md
- Runbook OmniRoute: `runbooks/omniroute.md`
- Runbook Hermes: `runbooks/hermes.md`
- OmniRoute data: `./data/omniroute/`
