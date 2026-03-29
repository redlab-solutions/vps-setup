---
name: 2026-03-29-vnc-playwright-autopilot-design
description: Piloto automático VNC + Playwright com checkpoint Telegram
type: projeto
data: 2026-03-29
projeto: vps-setup
---

# VNC Playwright Autopilot — Modo Checkpoint

## Meta

Autonomia do agente no browser do webtop: após usuário fazer login, agente assume controle via Playwright CLI, navega autonomamente,valida fluxos, coleta evidências. Checkpoint irreversível pausa e notifica via Telegram.

## Arquitetura

```
webtop:chromium (sessão :0, mesmo processo que usuário vê no VNC)
       │
       ├── playwright-cli via docker exec webtop
       │      └── captura screenshots, clicks, typing na sessão autenticada
       │
       └── gvncviewer --shared (usuário observa em tempo real)

Telegram bot: Oráculo (8571862614:AAGJVKyGCrMCAKQ5Cclb8KyoCoFvlzbMlRo)
       │
       └── checkpoint notifications + resume commands
```

**Ponto-chave:** Playwright CLI no container usa o mesmo processo chromium autenticado.

## Fluxo Operacional

```
1. Usuário: abre chromium no webtop → faz login em [serviço]
2. Usuário: me avisa "pronto" (Telegram ou conversa)
3. Agente: executa automações via docker exec playwright-cli
4. Agente: coleta evidências → debug-sessions/YYYY-MM-DD-[contexto]/
5. Checkpoint irreversível? → pausa + Telegram notification
6. Usuário: responde via Telegram (opção A/B/C ou "resume")
7. Agente: retoma ou cancela
8. Sessão expirou? → peço via Telegram, usuário reloga, me avisa
```

## Checkpoint — O que pausa

**Pausa em:**
- Confirmar pedido/pagamento
- Enviar mensagem em nome do usuário
- Excluir recurso (repo, arquivo, dado)
- Submeter formulário crítico (submit em forms importantes)
- Qualquer ação irreversível identificado pelo agente

**Não pausa:**
- Navegação comum (clicks, scroll, leitura)
- Preencher campos de input (sem submit)
- Abrir menus, dialogs de leitura
- Screenshots e coleta de evidências

## Componentes

### 1. Skill `vps-vnc`renovada

Adicionar subcomandos:

```bash
/vps-vnc playwright screenshot [url]          # screenshot da URL ou página atual
/vps-vnc playwright click [selector]           # clica elemento CSS
/vps-vnc playwright type [selector] [texto]    # digita em campo
/vps-vnc playwright evaluate [js]              # executa JS na página
/vps-vnc checkpoint [pergunta] [opções]        # pausa + notifica Telegram
/vps-vnc resume [checkpoint_id] [resposta]     # retoma do checkpoint
/vps-vnc evidence collect [contexto]           # coleta evidência automática
```

### 2. Telegram Bridge

- Bot: @lincolnqjunior_moltbot (ID: 8571862614:AAGJVKyGCrMCAKQ5Cclb8KyoCoFvlzbMlRo)
- Notificação checkpoint: "🛑 CHECKPOINT\n📍 [URL]\n[pergunta]\nOpções: [A] [B] [C]\n⏱ pausado"
- Resume: usuário responde com opção ou "/vps-vnc resume [id] [opção]"

### 3. Checkpoint Registry

Arquivo: `~/.vps-vnc/checkpoints.json`
```json
{
  "id": "ckpt_001",
  "url": "https://github.com/user/settings",
  "action": "delete repo",
  "selector": "button[data-target='delete']",
  "timestamp": "2026-03-29T17:00:00Z",
  "options": ["Cancelar", "Confirmar"],
  "status": "paused"
}
```

### 4. Auto-Evidence Collector

Pós-ação significativa:
- Screenshot automático → `debug-sessions/YYYY-MM-DD-[contexto]/evidence_NNN_[ação].png`
- Console log (se aplicável) → `.log`
- Metadata → `metadata.json` (URL, timestamp, action taken)

## Infra Existente (não mexer)

- ✅ webtop container com porta 5900 exposta (VNC --shared)
- ✅ gvncviewer instalado no host
- ✅ Skill `vps-vnc` em `~/.claude/commands/vps-vnc.md`
- ✅ Repo `redlab-solutions/vps-setup` no GitHub
- ✅ Runbooks em `vps-setup/runbooks/`
- ✅ `debug-sessions/` estruturado

## Validação

```
1. Usuário abre GitHub logado no chromium do webtop
2. Avisa "pronto"
3. Agente: screenshot da página, clica Settings, coleta evidência
4. Checkpoint: "Deletar repo?" → usuário responde via Telegram
5. Agente: executa ou cancela
6. Evidências salvas em debug-sessions/
```

## TODO

- [ ] Atualizar skill `vps-vnc` com subcomandos playwright e checkpoint
- [ ] Criar Telegram bridge para notifications
- [ ] Criar checkpoint registry (`~/.vps-vnc/checkpoints.json`)
- [ ] Criar auto-evidence collector
- [ ] Testar fluxo completo: login → autonomous navigation → checkpoint
- [ ] Commit e push no repo `redlab-solutions/vps-setup`

## Integração com Autoresearch — Loop de Iteração

Inspirado em [autoresearch](https://github.com/uditgoenka/autoresearch) (Karpathy's autoresearch), o piloto automático é um loop contínuo Modify → Verify → Keep/Discard.

### Loop de Iteração

```
LOOP (até task completa ou checkpoint):
  1. REVIEW     — ler estado atual + histórico em debug-sessions/
  2. MODIFY     — playwright-cli: click, type, navigate
  3. COMMIT     — git commit antes da verificação
  4. VERIFY     — screenshot + DOM evaluate (mesma sessão autenticada)
  5. KEEP/DISCARD — se melhorou → avançar; se piorou → reverter
  6. LOG        — salvar em debug-sessions/YYYY-MM-DD-[contexto]/
  7. CHECKPOINT — se ação irreversível → pausar + Telegram
  8. REPEAT
```

### Estrutura de Evidência por Iteração

```
debug-sessions/
  2026-03-29-github-autoresearch/
    metadata.json        ← log de todas as iterações (TSV-like)
    evidence_001.png     ← screenshot iteracão 1
    evidence_002.png     ← screenshot iteracão 2
    dom_state_002.json   ← DOM snapshot pós-iteracão 2
    checkpoint_001.json  ← checkpoint se houve pausa
```

### metadata.json — Log de Iteração

```json
{
  "session": "github-autoresearch",
  "started": "2026-03-29T17:00:00Z",
  "goal": "Verificar todas as settings do repositório",
  "iterations": [
    {
      "n": 1,
      "action": "navigate",
      "url": "https://github.com/user/repo/settings",
      "selector": null,
      "result": "ok",
      "screenshot": "evidence_001.png",
      "timestamp": "2026-03-29T17:01:00Z"
    },
    {
      "n": 2,
      "action": "click",
      "selector": "button[data-target='danger']",
      "result": "checkpoint",
      "checkpoint_id": "ckpt_001",
      "timestamp": "2026-03-29T17:02:00Z"
    }
  ]
}
```

### Checkpoint como Iteração Especial

Quando o agente pausa:
- Iteraćão com `result: "checkpoint"` e `checkpoint_id` referenciando `checkpoint_001.json`
- Log guardado, não perdido
- Resume após resposta do usuário

### Evolução Contínua

Cada sessão acumula evidência + log. O histórico de iterações serve como:
- **Autoria:** prova de ações executadas
- **Reversão:** permite entender o que foi feito antes de um checkpoint
- **Métricas:** conta iterações, tempo por ação, checkpoints por sessão
