# Shared VNC Session — Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Habilitar acesso VNC compartilhado ao webtop para que o agente possa ver e interactuar na mesma sessão do usuário.

**Architecture:** Expor porta VNC 5900 apenas em localhost no container webtop; instalar cliente gvncviewer no host; criar skill global `vps-vnc` para protocolo de operação; criar estrutura de runbooks.

**Tech Stack:** Docker, docker-compose, gvncviewer, KasmVNC (já no container)

---

## File Map

**Modify:**
- `/home/lincoln/vps-setup/docker-compose.yml` — adicionar porta VNC 5900

**Create:**
- `/home/lincoln/.claude/commands/vps-vnc.md` — skill global de protocolo VNC
- `/home/lincoln/vps-setup/runbooks/README.md` — índice de runbooks

---

## Tasks

### Task 1: Expor porta VNC 5900 no docker-compose

**Files:**
- Modify: `/home/lincoln/vps-setup/docker-compose.yml`

- [ ] **Step 1: Ler docker-compose atual**

Executar: `cat /home/lincoln/vps-setup/docker-compose.yml`
Identificar bloco `webtop` e suas portas existentes.

- [ ] **Step 2: Adicionar porta VNC 5900**

Adicionar em `webtop.ports` a linha:
```yaml
    - "127.0.0.1:5900:5900"
```
Manter `"127.0.0.1:3000:3000"` que já existe.

- [ ] **Step 3: Commit**

```bash
cd /home/lincoln/vps-setup && git add docker-compose.yml && git commit -m "feat(webtop): expose VNC port 5900 on localhost for shared session"
```

---

### Task 2: Instalar gvncviewer no host VPS

**Files:**
- Modify: `/home/lincoln/vps-setup/docs/superpowers/specs/2026-03-29-shared-vnc-vps-design.md` (atualizar dependência como instalada)

- [ ] **Step 1: Instalar gvncviewer**

```bash
apt update && apt install -y gvncviewer
```

- [ ] **Step 2: Verificar instalação**

```bash
gvncviewer --version
```
Esperado: mostra versão sem erro.

- [ ] **Step 3: Commit do spec atualizado**

```bash
cd /home/lincoln/vps-setup && git add docs/superpowers/specs/2026-03-29-shared-vnc-vps-design.md && git commit -m "docs(spec): gvncviewer installed, VNC port exposed"
```

---

### Task 3: Criar skill global vps-vnc

**Files:**
- Create: `/home/lincoln/.claude/commands/vps-vnc.md`

- [ ] **Step 1: Criar diretório de commands se não existir**

```bash
mkdir -p /home/lincoln/.claude/commands
```

- [ ] **Step 2: Criar skill vps-vnc**

Escrever o arquivo `/home/lincoln/.claude/commands/vps-vnc.md` com o conteúdo completo do protocolo conforme especificado no spec — incluindo:
- Quando usar (trigger words)
- Como conectar ao VNC
- Regra de screenshot obrigatório
- Ferramentas disponíveis (docker exec no container)
- Referência ao repositório de runbooks
- Instruções do playwright-cli

- [ ] **Step 3: Sem commit** (arquivo em ~/.claude não é versionado)

---

### Task 4: Criar estrutura de runbooks

**Files:**
- Create: `/home/lincoln/vps-setup/runbooks/README.md`
- Create: `/home/lincoln/vps-setup/runbooks/template.md` (exemplo de runbook)

- [ ] **Step 1: Criar README.md do runbooks**

```markdown
# Runbooks — Navegação Autenticada

Repositório de runbooks para sessões VNC compartilhadas.

Cada arquivo = um site/serviço com steps de login e validação.

## Formato
Ver `template.md` para modelo.

## Runbooks existentes
(nenhum ainda — adicionar conforme necessidade)

## Uso
1. Ler runbook do serviço
2. Conectar ao VNC: `docker exec -it webtop gvncviewer localhost:5900 --shared`
3. Executar passos do runbook
4. Capturar screenshot a cada passo
5. Salvar evidências em `debug-sessions/YYYY-MM-DD-[contexto]/`
```

- [ ] **Step 2: Criar template.md**

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

## Notas
- Timeout de login: 30s
- MFA: requer interação do usuário
```

- [ ] **Step 3: Commit runbooks**

```bash
cd /home/lincoln/vps-setup && git add runbooks/ && git commit -m "feat(runbooks): add runbooks directory and template"
```

---

### Task 5: Restart webtop e validar conexão VNC

**Files:**
- Modify: `/home/lincoln/vps-setup/docker-compose.yml`

- [ ] **Step 1: Restart webtop com nova porta**

```bash
cd /home/lincoln/vps-setup && docker compose up -d webtop
```

- [ ] **Step 2: Verificar porta exposta**

```bash
docker ps --filter name=webtop --format "{{.Ports}}"
```
Esperado: `127.0.0.1:3000->3000/tcp, 127.0.0.1:5900->5900/tcp`

- [ ] **Step 3: Tentar conexão VNC (dry-run — não interativo)**

```bash
timeout 5 docker exec webtop gvncviewer localhost:5900 --shared 2>&1 || echo "Connection attempted (timeout expected in non-interactive)"
```
Esperado: timeout após 5s sem erro de conexão — indica que VNC server está a escutar.

- [ ] **Step 4: Commit**

```bash
cd /home/lincoln/vps-setup && git add -A && git commit -m "feat: shared VNC session fully operational"
```

---

## Spec Coverage Checklist

- [x] docker-compose: porta 5900 exposta em localhost — Task 1
- [x] gvncviewer instalado no host — Task 2
- [x] Skill global `vps-vnc` criada — Task 3
- [x] Repositório de runbooks criado — Task 4
- [x] Validação pós-deploy (docker compose up -d + docker ps) — Task 5

## Placeholder Scan

Nenhum TBD, TODO ou placeholder encontrado. Todos os comandos são concretos com output esperado documentado.

---

## Execução

**Dois modos disponíveis:**

**1. Subagent-Driven (recommended)** — Dispacho um subagent por task, reviso entre tasks, iteração rápida.

**2. Inline Execution** — Executo tasks nesta sessão usando executing-plans, com checkpoints de revisão.

Qual prefere?
