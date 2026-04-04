---
tipo: sessao-dev
data: 2026-04-04
projeto: vps-setup
status: concluido
tags: [omniroute, docker, caddy, vps]
---

# Session Log: 04-04-2026 11:15 - omniroute-vps-deploy

## Quick Reference (for AI scanning)
**Confidence keywords:** omniroute, llm-gateway, docker-compose, caddy, caddyfile, cloudflare, dns-01, ufw, firewall, healthcheck, tailscale, bind, network_mode, host, proxy, reverse-proxy
**Projects:** vps-setup, omniroute
**Outcome:** OmniRoute v3.5.1 deployed on VPS as LLM API gateway via Caddy, publicly accessible via Cloudflare.

## Decisions Made
- OmniRoute added to `docker-compose.yml` principal (unified management, no orphan warnings)
- OmniRoute Caddy route uses NO `bind` directive → listens on all interfaces (public via Cloudflare Proxy)
- code-server e webtop mantidos com `bind {env.TAILSCALE_IP}` → só Tailscale
- UFW aberto para 80/443 em todas as interfaces (Cloudflare precisa de acesso público)
- OmniRoute healthcheck usa `http://localhost:20128/` (root path retorna 200 sem auth)

## Key Learnings
- `/api/health` do OmniRoute retorna 401 Unauthorized (requer auth)
- UFW `allow 80/tcp` e `allow 443/tcp` sem interface específica abre para todas as interfaces
- Caddy em `network_mode: host` escuta em todas as interfaces quando não há `bind` explícito
- DNS-01 TLS via Cloudflare precisa de UFW aberto na interface pública (eth0), não só tailscale0
- OmniRoute gera secrets automaticamente na primeira vez (JWT_SECRET, STORAGE_ENCRYPTION_KEY, API_KEY_SECRET)

## Solutions & Fixes
- Container conflict `omniroute` já existe → `sudo docker rm -f omniroute`
- healthcheck unhealthy (401) → mudar de `/api/health` para `/`
- Caddy não logava erros de TLS para llm-proxy → restart forçou re-obtenção de certificado
- Timeout de conexão (ERR_CONNECTION_TIMED_OUT) → UFW `allow 80/tcp` + `allow 443/tcp` (sem interface)
- bind TAILSCALE_IP no bloco llm-proxy impedia acesso via Cloudflare público → remover bind

## Files Modified
- `docker-compose.yml`: added `omniroute` service (image, port 20128 localhost, DATA_DIR volume, healthcheck)
- `Caddyfile`: added `llm-proxy.redlabsolutions.com.br` route (reverse_proxy localhost:20128, sem bind)
- `.env.example`: added `OMNIROUTE_INITIAL_PASSWORD` var
- `runbooks/omniroute.md`: created with start/stop/update/backup/restore/health commands
- `docs/superpowers/specs/2026-04-04-omniroute-vps-design.md`: created
- `docs/superpowers/plans/2026-04-04-omniroute-vps-plan.md`: created
- `CLAUDE.md`: updated with OmniRoute service, gotchas, commands

## Setup & Config
- OmniRoute image: `diegosouzapw/omniroute:latest` (v3.5.1)
- OmniRoute port: `127.0.0.1:20128` (localhost only)
- DATA_DIR: `./data/omniroute` no host
- API endpoint: `https://llm-proxy.redlabsolutions.com.br/v1/chat/completions`
- Dashboard: `https://llm-proxy.redlabsolutions.com.br/`
- INITIAL_PASSWORD: set via `OMNIROUTE_INITIAL_PASSWORD` in `.env`
- TAILSCALE_IP: `100.99.233.11`
- VPS public IP: `217.216.86.113`
- DNS: `llm-proxy.redlabsolutions.com.br` → `217.216.86.113` (Cloudflare Proxy = proxied)
- UFW rules added: `allow 80/tcp`, `allow 443/tcp` (all interfaces)
- Caddy TLS: DNS-01 via Cloudflare, ZeroSSL fallback

## Pending Tasks
- Fazer primeiro login e trocar senha no dashboard
- Criar API Key no dashboard OmniRoute
- Testar chamada de API com Bearer token
- Configurar Claude Code para usar OmniRoute como provider

## Errors & Workarounds
- **Error:** `Error response from daemon: Conflict. The container name "/omniroute" is already in use` → `sudo docker rm -f omniroute`
- **Error:** healthcheck unhealthy (HTTP 401 on /api/health) → healthcheck usa `/`
- **Error:** ERR_CONNECTION_TIMED_OUT no browser (acesso externo) → UFW `allow 80/tcp`, `allow 443/tcp` (sem interface específica)
- **Error:** TLS `No such authorization` no Let's Encrypt → restart Caddy, ZeroSSL DNS-01 via Cloudflare funcionou

## Key Exchanges
- Usuario perguntou se OmniRoute deveria estar no compose principal → sim, migrou para lá
- Usuario perguntou sobre risco de segurança de expor publicamente (opção B) → explicado que é seguro com auth + API keys
- UFW só tinha regras para interface tailscale0 → tráfego Cloudflare chega por eth0, precisou abrir

## Custom Notes
- Configuração do OmniRoute aplicada em `/home/lincoln/.claude/settings.json` pelo usuário
- OmniRoute v3.5.1 deployed com sucesso

---

## Quick Resume Context

OmniRoute v3.5.1 foi deployado no VPS Contabo como gateway unificado de LLMs. Está rodando em Docker (porta 20128, localhost), exposto publicamente via Caddy em `llm-proxy.redlabsolutions.com.br` com TLS DNS-01 Cloudflare. Dashboard acessível em `https://llm-proxy.redlabsolutions.com.br/`. Próximos passos: login no dashboard, criar API Key e testar chamada.

---

## Raw Session Log

### User: Omniroute como API única do VPS
- Usuario: "gostaria de usar o omniroute como api unica aqui no vps. Qual instalação recomendada para atualizações e gestão? https://github.com/diegosouzapw/OmniRoute"
- Explorado README e VM Deployment Guide do OmniRoute
- Recomendações: Docker Compose para VPS (facilita updates/rollback)
- Design aprovado: OmniRoute em Docker, porta 20128 localhost, Caddy reverse proxy, DATA_DIR em volume host
- Spec escrita em `docs/superpowers/specs/2026-04-04-omniroute-vps-design.md`
- Plano escrito em `docs/superpowers/plans/2026-04-04-omniroute-vps-plan.md`

### Tarefas implementadas (código)
1. `docker-compose.omniroute.yml` criado → depois migrado para compose principal
2. `.env.example` atualizado com `OMNIROUTE_INITIAL_PASSWORD`
3. `Caddyfile` atualizado com bloco `llm-proxy.redlabsolutions.com.br`
4. `runbooks/omniroute.md` criado

### Deploy no VPS
- Usuario tentou `docker compose -f docker-compose.omniroute.yml up -d` → container conflict
- Corrigido: `sudo docker rm -f omniroute`
- Healthcheck mostra "unhealthy" → healthcheck usava `/api/health` (401 Unauthorized)
- Corrigido: healthcheck usa `/` (root path, retorna 200 sem auth)
- Commits feitos localmente, push para origin/master

### Decisão bind vs. público
- Usuario perguntou se deveria estar no compose principal → sim, migrado
- Usuario perguntou sobre risco de segurança de expor publicamente (opção B sem bind) → sem risco relevante com auth + API keys
- `bind {env.TAILSCALE_IP}` removido do bloco llm-proxy
- Commit: `f76f2c1 fix: remove Tailscale bind from llm-proxy to expose via Cloudflare`

### Problema ERR_CONNECTION_TIMED_OUT
- Caddy escutava em `*:443` (todas interfaces)
- UFW só tinha regras para `tailscale0` → tráfego Cloudflare chega por eth0
- Corrigido: `sudo ufw allow 80/tcp && sudo ufw allow 443/tcp`
- OmniRoute acessível publicamente em `https://llm-proxy.redlabsolutions.com.br/`

### Update para v3.5.1
- Usuario mencionou update disponível v3.5.1
- Comando: `sudo docker compose pull omniroute && sudo docker compose up -d omniroute`

### vault-preserve
- CLAUDE.md atualizado com OmniRoute service, gotchas, commands
- Commit: `6aaa9a9 docs: update CLAUDE.md with OmniRoute service and gotchas`

### Configuração settings.json
- Usuario aplicou configuração em `/home/lincoln/.claude/settings.json`
