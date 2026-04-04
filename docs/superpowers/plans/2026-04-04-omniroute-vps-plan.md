# OmniRoute VPS — Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Subir o OmniRoute como API gateway de LLM no VPS Contabo, exposto via Caddy em llm-proxy.redlabsolutions.com.br.

**Architecture:** OmniRoute em Docker na porta 20128 (localhost-only). Caddy faz reverse proxy e TLS via Cloudflare DNS-01. DATA_DIR persiste em volume no host.

**Tech Stack:** Docker, Caddy, OmniRoute (diegosouzapw/omniroute), Cloudflare DNS.

---

## Task 1: Criar docker-compose.omniroute.yml

**Files:**
- Create: `/home/lincoln/vps-setup/docker-compose.omniroute.yml`
- Modify: `.env.example`

- [ ] **Step 1: Criar o arquivo docker-compose.omniroute.yml**

```yaml
services:
  omniroute:
    image: diegosouzapw/omniroute:latest
    container_name: omniroute
    restart: unless-stopped
    ports:
      - "127.0.0.1:20128:20128"
    environment:
      - PORT=20128
      - INITIAL_PASSWORD=${OMNIROUTE_INITIAL_PASSWORD}
      - DATA_DIR=/data
      - APP_LOG_TO_FILE=true
    volumes:
      - ./data/omniroute:/data
    healthcheck:
      test: ["CMD", "wget", "--spider", "-q", "http://localhost:20128/api/health"]
      interval: 30s
      timeout: 10s
      retries: 3
      start_period: 40s
```

- [ ] **Step 2: Commit do compose**

```bash
git add docker-compose.omniroute.yml
git commit -m "feat: add OmniRoute docker-compose for VPS deployment"
```

---

## Task 2: Atualizar .env.example com variáveis do OmniRoute

**Files:**
- Modify: `/home/lincoln/vps-setup/.env.example`

- [ ] **Step 1: Adicionar variáveis OMNIROUTE_* ao .env.example**

Adicionar ao final do `.env.example`:

```env
# OmniRoute
OMNIROUTE_INITIAL_PASSWORD=change_me_change_me_change_me
```

- [ ] **Step 2: Commit**

```bash
git add .env.example
git commit -m "feat: add OmniRoute env vars to .env.example"
```

---

## Task 3: Atualizar Caddyfile com bloco llm-proxy

**Files:**
- Modify: `/home/lincoln/vps-setup/Caddyfile`

- [ ] **Step 1: Adicionar bloco llm-proxy ao Caddyfile**

Adicionar ANTES do último `}` (depois dos outros blocos de serviço):

```
llm-proxy.redlabsolutions.com.br {
    bind {env.TAILSCALE_IP}
    reverse_proxy http://localhost:20128
}
```

- [ ] **Step 2: Commit**

```bash
git add Caddyfile
git commit -m "feat: add llm-proxy Caddy route for OmniRoute"
```

---

## Task 4: Criar runbook de operações

**Files:**
- Create: `/home/lincoln/vps-setup/runbooks/omniroute.md`

- [ ] **Step 1: Escrever o runbook**

```markdown
# OmniRoute — Runbook de Operações

## URLs
- Dashboard: https://llm-proxy.redlabsolutions.com.br/
- API: https://llm-proxy.redlabsolutions.com.br/v1/chat/completions

## Subir / Parar

```bash
# Subir
docker compose -f docker-compose.omniroute.yml up -d

# Parar
docker compose -f docker-compose.omniroute.yml down

# Ver logs
docker compose -f docker-compose.omniroute.yml logs -f
```

## Update

```bash
docker compose -f docker-compose.omniroute.yml pull && docker compose -f docker-compose.omniroute.yml up -d
```

## Recarregar Caddy

```bash
docker compose restart caddy
```

## Backup

1. Abrir dashboard → Settings → Backup → Export
2. Salvar em `./backups/omniroute/YYYY-MM-DD.json`

## Restore

1. dashboard → Settings → Backup → Import
2. Selecionar arquivo de backup

## Verificar saúde

```bash
curl -H "Authorization: Bearer or_live_<SUA_KEY>" \
  https://llm-proxy.redlabsolutions.com.br/v1/models
```

## Reset de senha inicial

```bash
# Editar o .env e trocar OMNIROUTE_INITIAL_PASSWORD
# Depois recriar o container:
docker compose -f docker-compose.omniroute.yml up -d --force-recreate
```
```

- [ ] **Step 2: Commit**

```bash
git add runbooks/omniroute.md
git commit -m "docs: add OmniRoute operations runbook"
```

---

## Task 5: Verificar DNS no Cloudflare

**Files:**
- None (ação manual)

- [ ] **Step 1: Conferir registro DNS**

No dashboard Cloudflare (`dash.cloudflare.com`):
- Ir em DNS → Records
- Verificar que existe registro **A** para `llm-proxy.redlabsolutions.com.br` apontando para o IP do VPS
- Verificar que está **Proxied** (núvem laranja)

---

## Task 6: Deploy no VPS

**Files:**
- None (execução no VPS)

- [ ] **Step 1: Enviar arquivos atualizados ao VPS**

```bash
# No VPS (de dentro de /home/lincoln/vps-setup/):
git pull origin master
```

- [ ] **Step 2: Criar diretório de dados**

```bash
mkdir -p /home/lincoln/vps-setup/data/omniroute
```

- [ ] **Step 3: Copiar .env e ajustar senhas**

```bash
cp /home/lincoln/vps-setup/.env.example /home/lincoln/vps-setup/.env
# Editar OMNIROUTE_INITIAL_PASSWORD com senha forte
nano /home/lincoln/vps-setup/.env
```

- [ ] **Step 4: Subir OmniRoute**

```bash
docker compose -f docker-compose.omniroute.yml up -d
docker compose -f docker-compose.omniroute.yml logs -f
# Verificar que o container está healthy
docker compose -f docker-compose.omniroute.yml ps
```

- [ ] **Step 5: Validar acesso local**

```bash
curl -s http://localhost:20128/api/health
# Esperado: resposta JSON com status ok
```

- [ ] **Step 6: Atualizar Caddy e validar**

```bash
docker compose restart caddy
# Aguardar ~10s para TLS ser provisionado
curl -sk -I https://llm-proxy.redlabsolutions.com.br/ --resolve "llm-proxy.redlabsolutions.com.br:443:127.0.0.1"
# Esperado: HTTP 200 ou redirect
```

- [ ] **Step 7: Commit final de qualquer ajuste**

```bash
git add -A && git commit -m "chore: OmniRoute deployment complete on VPS"
```

---

## Task 7: Setup inicial do OmniRoute via Dashboard

**Files:**
- None (via browser)

- [ ] **Step 1: Login no dashboard**

1. Abrir https://llm-proxy.redlabsolutions.com.br/
2. Fazer login com usuário `admin` + `OMNIROUTE_INITIAL_PASSWORD` do `.env`
3. Trocar senha imediatamente

- [ ] **Step 2: Criar API Key**

1. Settings → API Keys → New Key
2. Copiar a chave gerada (começa com `or_live_`)
3. Armazenar no `.env` como `OMNIROUTE_API_KEY=or_live_...`

- [ ] **Step 3: Commit com a chave (opcional — ou guardar no vault)**

Se quiser versionar a chave no repo (criptografado ou no vault):
```bash
git add .env && git commit -m "chore: add OmniRoute API key"
```

- [ ] **Step 4: Testar API com a chave**

```bash
curl -X POST https://llm-proxy.redlabsolutions.com.br/v1/chat/completions \
  -H "Authorization: Bearer or_live_<SUA_KEY>" \
  -H "Content-Type: application/json" \
  -d '{"model":"gpt-4o-mini","messages":[{"role":"user","content":"Hello"}]}'
```
