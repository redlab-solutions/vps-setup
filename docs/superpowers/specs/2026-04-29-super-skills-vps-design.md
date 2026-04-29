# Super Skills VPS — Design Spec

**Data:** 2026-04-29
**Status:** Draft
**Contexto:** Avaliação seletiva do sistema "Super Skills" (Jack Roberts) aplicado à VPS de desenvolvimento

## Premissa

A VPS já tem 80% do que o sistema de Super Skills propõe, mas de forma fragmentada: 4 sistemas de memória separados, skills genéricas sem contexto de domínio, e fluxo de fim-de-sessão manual com 3-4 chamadas redundantes. O objetivo é consolidar sem migrar — só governança e automação.

---

## 1. Modelo de Memória Unificado

### Buckets e donos

| Bucket | Conteúdo | Sistema | Regra |
|---|---|---|---|
| **Profile** | Foco atual, decisões pendentes, preferências | `memory/profile.md` | Lido toda sessão. Mutável. < 50 linhas. |
| **Knowledge** | Fatos imutáveis: arquitetura, configs, runbooks | `CLAUDE.md` + `memory/project_*.md` + `memory/reference_*.md` | Atualizado via preserve. Consultado quando relevante. |
| **Session Log** | O que aconteceu numa sessão — contexto temporal | `CC-Session-Logs/` + `context-mode` FTS5 | Auto-salvo via compress. Buscável via ctx_search. |
| **Feedback** | Lições aprendidas, "do instead", padrões | `memory/feedback_*.md` + `.claude/napkin.md` | Acumulado ao longo do tempo. Napkin re-priorizado a cada sessão. |

### Mudanças concretas

- `memory/MEMORY.md` — primeira entrada aponta para `profile.md`
- `memory/profile.md` — novo arquivo (Seção 3 abaixo)
- Nenhum sistema novo ou migração — só regras claras de governança

---

## 2. Skill `/end-session`

### Orquestra: preserve → napkin → compress (daily note incluída)

**Arquivo:** `~/.claude/commands/end-session.md`

### Fluxo

```
/end-session
  1. [preserve]  Auto-detecta mudanças (git diff, CLAUDE.md atual, tarefas)
                Preserva TUDO por default — só mostra resumo do que salvou
                Se CLAUDE.md > 280 linhas → auto-archive

  2. [napkin]   Pergunta: "Alguma lição desta sessão?"
                Se sim → adiciona ao napkin com data + "Do instead"
                Se não → pula

  3. [compress] Gera session log com tudo
                Dual-write: local (CC-Session-Logs/) + vault (Sessões/)
                Cria/atualiza daily note com link (já integrado no compress Step 5)

  4. [profile]  Atualiza profile.md se houver mudança em foco ou decisões

  5. [summary]  Mostra: "Preservado X em CLAUDE.md, Y no napkin, log em Z"
                Sugere: "Roda /compact quando estiver pronto"
```

### Princípios

- **Preserva tudo por default.** Zero perguntas sobre "o que preservar".
- **1 pergunta no total** (napkin), não 6+.
- **Daily note automática** via compress Step 5 — sem skill separado.
- **Compact não incluso** — é destrutivo, precisa de ação explícita.
- **Fallback:** cada skill individual permanece disponível para controle granular.

### Detecção automática (preserve)

O preserve auto-detecta sem perguntar:
- `git diff --stat` para arquivos modificados
- `git log --oneline` para commits da sessão
- Tarefas completadas (TaskList)
- Mudanças em configs ou infraestrutura
- Novos arquivos criados

---

## 3. Profile.md — Memória Estratégica

**Arquivo:** `/home/lincoln/.claude/projects/-home-lincoln-vps-setup/memory/profile.md`

```markdown
---
name: Perfil Estratégico
description: Foco atual, decisões pendentes, prioridades — lido toda sessão
type: user
---

## Foco Atual
- [1-2 projetos/áreas ativos com contexto mínimo]

## Decisões Pendentes
- [Decisões abertas que futuras sessões precisam saber]

## Preferências de Trabalho
- [Respostas a perguntas que o Claude faz toda sessão]

## Última Atualização: YYYY-MM-DD
```

### Governação

- `/end-session` atualiza automaticamente se houver mudanças
- Mantém < 50 linhas — itens resolvidos saem
- Referenciado no `MEMORY.md` como primeira entrada
- Seções vazias = sem mudança desde última atualização

---

## 4. Hook de Sugestão de Fim de Sessão

**Problema:** Não existe hook `SessionEnd` nativo no Claude Code.

**Alternativa:** Hook `UserPromptSubmit` com detecção heurística de padrões de saída.

**Arquivo:** `.claude/settings.json` (projeto) — adicionar ao array `hooks.UserPromptSubmit`

**Padrões detectados:** `tchau`, `bye`, `sair`, `fim`, `encerrar`, `até`, `goodbye`, `done for today`, `isso é tudo`, `por hoje é só`

**Comportamento:** Exibe mensagem sugerindo `/end-session`. Não bloqueia — o usuário pode ignorar.

**Limitação:** É heurística, não hook real. Falsos positivos possíveis. Cobre ~80% dos casos de uso.

---

## 5. Personal-Data-Connectors como Skill `/context`

**Problema:** Pipeline em `/home/lincoln/personal-data-connectors/` agrega Calendar, Gmail, Trello, GitHub — mas o Claude não consulta em tempo real.

### Nível 1 — Skill `/context` (implementar agora)

**Arquivo:** `~/.claude/commands/context.md`

```
/context
  1. Roda python main.py --pipeline daily no personal-data-connectors
  2. Lê os .md gerados em /home/lincoln/obsidian-vault/.raw/
  3. Indexa no context-mode FTS5 (ctx_index)
  4. Confirma: "Dados indexados. Use ctx_search para consultar."
```

**Dados disponíveis via ctx_search:**
- Reuniões e transcripts (`/raw/meetings/`)
- Emails processados
- Cards do Trello (`/raw/trello/`)
- Eventos do Google Calendar
- Atividade GitHub (`/raw/github-redlab-solutions/`)

**Vantagens:** Zero mudança no pipeline existente. Reutiliza infra do context-mode. Dados ficam buscáveis dentro da sessão.

### Nível 2 — MCP Server (futuro)

Transformar o personal-data-connectors num MCP server com tools: `search_calendar`, `search_email`, `get_trello_board`. Exige refatoração completa do projeto. Fica para quando o pipeline estabilizar.

---

## Quick Wins — Ordem de Implementação

| # | O quê | Arquivo | Esforço |
|---|---|---|---|
| 1 | `/end-session` skill | `~/.claude/commands/end-session.md` | 1-2h |
| 2 | `profile.md` | `memory/profile.md` + `MEMORY.md` update | 15min |
| 3 | Hook de sugestão | `.claude/settings.json` hooks | 15min |
| 4 | `/context` skill | `~/.claude/commands/context.md` | 30min |

---

## Fora de Escopo

- Migração para Pinecone ou vector DB
- Skills específicas de domínio/negócio (próximo ciclo)
- MCP server para personal-data-connectors (Nível 2)
- Loop explícito de self-improvement de skills
- Integração com Hermes Agent
