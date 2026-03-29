# Shared VNC Session — VPS Dev Machine

**Date:** 2026-03-29
**Status:** Approved
**Type:** Infrastructure / Agent Tooling

---

## Goal

Habilitar sessão VNC compartilhada no webtop da VPS para que o agente possa actuar colaborativamente na mesma sessão do usuário — abrindo programas, fazendo debugging, validando fluxos autenticados, e executando runbooks de navegação.

---

## Architecture

```
┌─────────────────────────────────────────────────────┐
│                    VPS (host)                        │
│                                                     │
│  ┌──────────────┐    ┌──────────────────────────┐  │
│  │  Claude Code │    │   webtop container        │  │
│  │  (this agent)│    │   (KasmVNC server)        │  │
│  │              │    │   Display :1 — shared      │  │
│  │  gvncviewer ───────► :5900 (VNC)              │  │
│  │              │    │   Port 3000 (web)          │  │
│  └──────────────┘    └──────────────────────────┘  │
│         │                    │                     │
│         │      tailscale ssh  │                     │
│         └────────────────────┘                     │
│                                                     │
│  ┌──────────────┐                                 │
│  │  Caddy proxy  │  obsidian.redlabsolutions.com.br
│  │  (TLS + auth) │    → webtop:3000                │
│  └──────────────┘                                 │
└─────────────────────────────────────────────────────┘
         │
         │ Tailscale VPN
         ▼
┌─────────────────┐
│  User browser   │
│  (Chrome/Firefox│
│  OAuth + auth)  │
└─────────────────┘
```

**Nota:** O agente reside na mesma infraestrutura (VPS), então a conexão VNC é via `localhost:5900` — não precisa de Tailscale para o VNC em si. O Tailscale é usado para o túnel SSH caso seja necessário acesso remoto ao host.

---

## Changes Required

### 1. docker-compose.yml — Expor porta VNC

```yaml
webtop:
  image: lscr.io/linuxserver/webtop:ubuntu-lxqt
  ports:
    - "127.0.0.1:3000:3000"    # KasmVNC web (já existia)
    - "127.0.0.1:5900:5900"    # ← NOVO: VNC nativo (apenas localhost)
```

### 2. Host — Instalar cliente VNC

```bash
apt install -y gvncviewer   # ou xtigervnc-viewer
```

### 3. Validação — Testar conexão simultânea

```bash
# Usuario abre browser → acessa obsidian.redlabsolutions.com.br
# Agente conecta:
docker exec webtop gvncviewer localhost:5900 --shared
```

Ambas conexões devem ver o mesmo desktop e permitir interação.

---

## Operando a Sessão VNC Compartilhada

### Global Skill: `vps-vnc`

Todas as sessões futuras devem carregar uma skill `vps-vnc` que define o protocolo de operação.

**Localização:** `/home/lincoln/.claude/commands/vps-vnc.md`

**Conteúdo:**

```markdown
# VPS Shared VNC — Operating Protocol

## Quando usar

Quando o usuário pedir para:
- "Debugar algo no browser"
- "Validar um fluxo autenticado"
- "Fazer login em [site] e continuar de onde parei"
- "Verificar como [feature] aparece logado"
- Qualquer tarefa que requeira interação com UI web

## Protocolo de Execução

### 1. Conectar ao VNC

```bash
# убедиться que webtop está rodando
docker ps --filter name=webtop

# conectar ao VNC compartilhado
docker exec -it webtop gvncviewer localhost:5900 --shared
```

### 2. Captura de Evidência (OBRIGATÓRIO)

Após cada ação significativa, enviar screenshot:

```bash
# via VNC screenshot (usar ferramentas internas do gvncviewer)
# ou via docker exec no container
docker exec webtop scrot -o /tmp/evidence.png
docker cp webtop:/tmp/evidence.png /tmp/evidence.png
# exibir caminho do arquivo para o usuário
```

**Regra:** Nenhuma validação de UI sem screenshot como evidência.

### 3. Ferramentas Disponíveis no Container

```bash
# Browser via CLI
docker exec -it webtop firefox --screenshot  # se disponível
docker exec -it webtop chromium-browser --screenshot
docker exec -it webtop midori

# Download/Upload
docker cp arquivo.txt webtop:/tmp/
docker cp webtop:/tmp/resultado.txt .

# Network debugging
docker exec -it webtop curl -v https://...
docker exec -it webtop wget -O /tmp/page.html https://...
```

### 4. Playwright-CLI para Validações Agênticas

Para validações programáticas (não visuais), usar `playwright-cli`:

```bash
# instalar no container webtop (se não existir)
docker exec webtop bash -c "cd /tmp && npx playwright-cli@latest install chromium"

#Exemplo: validar que elemento existe após login
docker exec webtop npx playwright-cli screenshot https://example.com/logged-in --selector '.dashboard'
```

### 5. Runbooks de Navegação

Repositório de runbooks: `/home/lincoln/vps-setup/runbooks/`

Estrutura:
```
runbooks/
  github-login.md
  google-oauth.md
  supabase-dashboard.md
  aws-console.md
  [...]
```

Cada runbook descreve:
- URL alvo e estado esperado
- Seletores CSS/XPath dos elementos de login
- Passos de autenticação
- Cookies/sessão a persistir
- Validações pós-login

---

## Runbooks — Formato Padrão

```markdown
# Runbook: [Serviço] — Login e Validação

## URL
https://example.com/login

## Pré-condição
Usuário não está logado.

## Passos

### 1. Login
1. Abrir `https://example.com/login`
2. Inserir email: `{{EMAIL}}`
3. Inserir senha: `{{PASSWORD}}`
4. Clicar em `[data-testid="login-btn"]`
5. Esperar redirect para dashboard

### 2. Validação
- Confirmar URL: `https://example.com/dashboard`
- Confirmar elemento: `#user-profile` visível
- Screenshot: `evidence_post_login.png`

### 3. Persistência
Salvar cookies para reutilização:
```bash
docker exec webtop node -e "
const fs = require('fs');
// extrair cookies do browser state
"
```

## Notas
- Timeout de login: 30s
- MFA: requer interação do usuário
```

---

## Fluxo: Debugging Colaborativo

1. **Usuário** acessa `https://obsidian.redlabsolutions.com.br`, faz login OAuth (Google/GitHub/etc)
2. **Agente** conecta via VNC `docker exec -it webtop gvncviewer localhost:5900 --shared`
3. **Agente** vê a mesma tela, pode:
   - Abrir DevTools do browser (Ctrl+Shift+I)
   - Inspecionar elementos
   - Executar JavaScript no console
   - Navegar para outras páginas autenticadas
   - Fazer screenshots a cada passo
4. **Evidências** são salvas em `/home/lincoln/vps-setup/debug-sessions/YYYY-MM-DD-[contexto]/`
5. **Runbooks** atualizados com novos sites autenticados

---

## Portas e Segurança

| Porta | Bind | Uso | Exposição Pública |
|--------|------|-----|-------------------|
| 3000 | 127.0.0.1 | KasmVNC web | NÃO (via Caddy + Tailscale) |
| 5900 | 127.0.0.1 | VNC nativo | NÃO (mesmo host) |
| 443 | TAILSCALE_IP | Caddy TLS | NÃO (Tailscale only) |

**Zero portas expostas ao público.** Tudo passa pelo Tailscale VPN + Caddy reverse proxy.

---

## Validação Pós-Deploy

1. `docker compose up -d webtop`
2. Usuário acessa `https://obsidian.redlabsolutions.com.br` → OK
3. `docker exec webtop gvncviewer localhost:5900 --shared` → conecta e vê mesmo desktop → OK
4. Usuário e agente interagem simultaneamente sem conflito → OK
5. Screenshot capturado e entregue ao usuário → OK

---

## Dependências

- Docker + docker-compose (já existente)
- Tailscale (já instalado e configurado)
- Caddy com plugin GoDaddy (já configurado)
- `gvncviewer` (a instalar: `apt install gvncviewer`)
- Container webtop com KasmVNC (já em uso)
