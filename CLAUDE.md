# VPS Setup (Contabo)

Docker Compose infra: Caddy reverse proxy + code-server + webtop.

## Commands

```bash
docker compose up -d             # Start all services
docker compose logs -f           # Tail logs
docker compose restart caddy     # Reload Caddy config after Caddyfile changes
```

## Services

- **caddy**: Reverse proxy (`network_mode: host`) — reads `Caddyfile`, Cloudflare DNS-01 TLS, Tailscale IP
- **code-server**: VS Code in browser — port `127.0.0.1:8443`, mounts `/home/lincoln/workspace`
- **webtop**: Ubuntu LXQt desktop — port `127.0.0.1:3000`, mounts `obsidian-vault`

## Gotchas

- Caddy uses `CLOUDFLARE_API_TOKEN` for DNS-01 TLS challenge — must be set in `.env`
- `TAILSCALE_IP` must be set for Caddy to bind correctly on Tailscale interface
- Webtop needs `shm_size: "1gb"` — don't remove it
- `.env` exists (gitignored); `.env.example` is the template

## Vault
Sessões em: /home/lincoln/obsidian-vault/Áreas/Dev/Projetos/vps-setup/Sessões/

## Paths principais
- Workspace: /home/lincoln/vps-setup/
- Vault hub: /home/lincoln/obsidian-vault/Áreas/Dev/Projetos/vps-setup/vps-setup.md
