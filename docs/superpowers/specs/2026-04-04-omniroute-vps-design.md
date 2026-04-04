# OmniRoute no VPS — Design de Implantação

> **Goal:** Substituir o uso direto de múltiplos provedores LLM por um gateway unificado (OmniRoute) exposto via Caddy, com dashboard e API protegidos.

---

## 1. Arquitetura

```
Internet → Cloudflare → Caddy (:443)
                              ↓
                    llm-proxy.redlabsolutions.com.br
                              ↓
                       OmniRoute (:20128 localhost)
                              ↓
                    DATA_DIR → ./data/omniroute (host)
```

- OmniRoute roda em **Docker** (imagem oficial `diegosouzapw/omniroute`)
- Porta `20128` **nunca exposta ao exterior** — acessível só via Caddy (localhost)
- TLS终止 no Caddy (Cloudflare DNS-01 via `CLOUDFLARE_API_TOKEN`)
- `DATA_DIR` em volume host para persistência e backup

---

## 2. Segurança

### 2.1 Acesso ao Dashboard

- OmniRoute gera credenciais iniciais na primeira subida (fallback: `admin` / `123456` se `INITIAL_PASSWORD` não definido)
- Após login, o operador deve **trocar a senha** e configurar uma **API Key** para acesso programático
- Dashboard acessível em `https://llm-proxy.redlabsolutions.com.br/`

### 2.2 Acesso à API (OpenAI-compatible)

Todos os clientes usam **Bearer Token (API Key)**:

```
Authorization: Bearer or_live_<key>
```

OmniRoute permite:
- **Filtrar modelos** por API Key (cada chave vê só os modelos autorizados)
- **Criar múltiplas chaves** com roles diferentes (ex: uma só leitura, outra com gasto alto)
- **Rate limits** por chave

### 2.3 Acesso ao Caddy (rede)

- `bind {env.TAILSCALE_IP}` — exposto só via Tailscale (mesmo padrão dos outros serviços)
- Cloudflare Proxy ativo (IPs laranja) — proteção DDoS + WAF
- Acesso público pela internet via Cloudflare (domínio `redlabsolutions.com.br`)

### 2.4 Boas práticas operacionais

- API keys nunca em código — via variável de ambiente `OMNIROUTE_API_KEY`
- `APP_LOG_TO_FILE=true` para audit trail em `DATA_DIR/logs/`
- Backup do `DATA_DIR` (export/import nativo do OmniRoute)

---

## 3. Arquivos

| Arquivo | Ação |
|---|---|
| `docker-compose.omniroute.yml` | Criar — compose standalone |
| `Caddyfile` | Modificar — adicionar bloco `llm-proxy` |
| `.env.example` | Modificar — vars `OMNIROUTE_*` |
| `docs/superpowers/specs/2026-04-04-omniroute-vps-design.md` | Este arquivo |
| `runbooks/omniroute.md` | Criar — runbook de operações |

---

## 4. Variáveis de Ambiente

| Variável | Valor | Sensível? |
|---|---|---|
| `PORT` | `20128` | Não |
| `INITIAL_PASSWORD` | `(você define)` | Sim |
| `DATA_DIR` | `/data` | Não |
| `APP_LOG_TO_FILE` | `true` | Não |
| `CLOUDFLARE_API_TOKEN` | `(já existe)` | Sim |
| `OMNIROUTE_API_KEY` | `(gerado no dashboard)` | Sim |

---

## 5. Fluxo de Subida

1. Gerar `docker-compose.omniroute.yml` com imagem oficial + volumes
2. Criar diretório `./data/omniroute` no host
3. Subir: `docker compose -f docker-compose.omniroute.yml up -d`
4. Abrir dashboard em `http://localhost:20128` (acesso local temporário)
5. Trocar senha inicial, criar API Key
6. Atualizar Caddyfile com bloco do `llm-proxy`
7. `docker compose -f docker-compose.caddy.yml restart caddy`
8. Validar acesso externo em `https://llm-proxy.redlabsolutions.com.br/`

---

## 6. Operações Diárias (Runbook)

- **Update:** `docker compose -f docker-compose.omniroute.yml pull && up -d`
- **Logs:** `docker compose -f docker-compose.omniroute.yml logs -f`
- **Backup:** Export via dashboard (Settings → Backup) → salvar em `./backups/omniroute/`
- **Restore:** Import via dashboard
- **Verificar saúde:** GET `https://llm-proxy.redlabsolutions.com.br/api/v1/models` (requer API Key)

---

## 7. Pré-requisitos

- Docker Engine 24+ instalado no VPS
- `CLOUDFLARE_API_TOKEN` já configurado no `.env` do vps-setup
- Domínio `llm-proxy.redlabsolutions.com.br` criado no Cloudflare (tipo A, proxied)
