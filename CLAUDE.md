# VPS Setup (Contabo)

Docker Compose infra: Caddy reverse proxy + code-server + webtop + OmniRoute (LLM gateway).

## Commands

```bash
docker compose up -d             # Start all services
docker compose logs -f           # Tail logs
docker compose restart caddy     # Reload Caddy config after Caddyfile changes
docker compose pull omniroute && docker compose up -d omniroute  # Update OmniRoute
```

## Services

- **caddy**: Reverse proxy (`network_mode: host`) — reads `Caddyfile`, Cloudflare DNS-01 TLS
- **code-server**: VS Code in browser — port `127.0.0.1:8443`, Tailscale-only (`bind {env.TAILSCALE_IP}`)
- **webtop**: Ubuntu LXQt desktop — port `127.0.0.1:3000`, Tailscale-only, mounts `obsidian-vault`
- **omniroute**: LLM API gateway — port `127.0.0.1:20128`, exposed publicly via `llm-proxy.redlabsolutions.com.br` (no bind = all interfaces, Cloudflare Proxy)

## Gotchas

- Caddy uses `CLOUDFLARE_API_TOKEN` for DNS-01 TLS challenge — must be set in `.env`
- `TAILSCALE_IP` must be set for Caddy to bind correctly on Tailscale interface
- Webtop needs `shm_size: "1gb"` — don't remove it
- `.env` exists (gitignored); `.env.example` is the template
- OmniRoute healthcheck uses `/` (root), not `/api/health` (requires auth → 401)
- UFW allows 80/443 on all interfaces (Cloudflare needs public access for llm-proxy)
- code-server and webtop remain Tailscale-only (bind TAILSCALE_IP)

## Vault
Sessões em: /home/lincoln/obsidian-vault/Áreas/Dev/Projetos/vps-setup/Sessões/

## Paths principais
- Workspace: /home/lincoln/vps-setup/
- Vault hub: /home/lincoln/obsidian-vault/Áreas/Dev/Projetos/vps-setup/vps-setup.md
- Runbook OmniRoute: `runbooks/omniroute.md`
- OmniRoute data: `./data/omniroute/`
