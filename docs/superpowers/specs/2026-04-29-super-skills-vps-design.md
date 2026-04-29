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
| **Profile** | Foco atual, decisões pendentes, preferências | Global: `~/.claude/projects/-home-lincoln/memory/user_profile.md` (ampliar seção existente) | Lido toda sessão. Mutável. < 50 linhas. |
| **Knowledge** | Fatos imutáveis: arquitetura, configs, runbooks | `CLAUDE.md` + `memory/project_*.md` + `memory/reference_*.md` | Atualizado via preserve. Consultado quando relevante. |
| **Session Log** | O que aconteceu numa sessão — contexto temporal | `CC-Session-Logs/` + `context-mode` FTS5 | Auto-salvo via compress. Buscável via ctx_search. |
| **Feedback** | Lições aprendidas, "do instead", padrões | `memory/feedback_*.md` + `.claude/napkin.md` | Acumulado ao longo do tempo. Napkin editado manualmente via `/end-session`. |

### Mudanças concretas

- `~/.claude/projects/-home-lincoln/memory/user_profile.md` — ampliar com seções de Foco Atual e Decisões Pendentes
- `~/.claude/projects/-home-lincoln/memory/MEMORY.md` — adicionar entrada para o profile ampliado
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
                Se CLAUDE.md > 280 linhas → auto-archive (move seções antigas para CLAUDE-Archive.md conforme lógica do preserve Step 6)

  2. [napkin]   Pergunta: "Alguma lição desta sessão?"
                Se sim → edita {project_root}/.claude/napkin.md diretamente (adiciona item com data + "Do instead", mantém max 10 por categoria, remove itens mais antigos se cheio)
                Se não → pula
                Nota: skill napkin (~/.claude/skills/napkin/) já lê o .claude/napkin.md a cada sessão e escreve continuamente durante o trabalho. O end-session só garante captura final se houver lição não registrada.

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

## 3. Profile — Memória Estratégica Global

**Arquivo:** `/home/lincoln/.claude/projects/-home-lincoln/memory/user_profile.md` (já existe, ampliar)

O profile é **global** (não por-projeto). Toda sessão em qualquer projeto lê o mesmo profile. Já existe com conteúdo básico — ampliar com seções estratégicas.

```markdown
---
name: user_profile
description: Lincoln's role, preferences, and strategic focus — read every session
type: user
---

## Perfil
[conteúdo existente: desenvolvedor, VPS Contabo, português BR, etc.]

## Foco Atual
- [1-2 projetos/áreas ativos com contexto mínimo]

## Decisões Pendentes
- [Decisões abertas que futuras sessões precisam saber]

## Última Atualização: YYYY-MM-DD
```

### Governação

- `/end-session` atualiza automaticamente se houver mudanças em foco ou decisões
- Mantém < 50 linhas — itens resolvidos saem
- Referenciado no `MEMORY.md` global (`~/.claude/projects/-home-lincoln/memory/MEMORY.md`)
- Seções vazias = sem mudança desde última atualização
- **Não é por-projeto** — decisões de foco são globais, afetam todos os projetos

---

## 4. Hook de Sugestão de Fim de Sessão

**Problema:** Não existe hook `SessionEnd` nativo no Claude Code.

**Alternativa:** Hook `UserPromptSubmit` com detecção heurística de padrões de saída.

**Arquivo:** `.claude/settings.json` (projeto) — adicionar ao array `hooks.UserPromptSubmit`

**Padrões detectados (regex com boundary, final da mensagem):** `\b(tchau|bye|sair|encerrar|goodbye)\s*[.!?]?\s*$` e `\b(fim|até mais|done for today|isso é tudo|por hoje é só)\b` — detecta apenas padrões de despedida no final da mensagem, evitando falsos positivos como "fim de semana" ou "até que".

**Comportamento:** Exibe mensagem sugerindo `/end-session`. Não bloqueia — o usuário pode ignorar.

**Limitação:** É heurística, não hook real. Falsos positivos possíveis. Cobre ~80% dos casos de uso.

---

## 5. Personal-Data-Connectors como Skill `/context`

**Problema:** Pipeline em `/home/lincoln/personal-data-connectors/` agrega Calendar, Gmail, Trello, GitHub — mas o Claude não consulta em tempo real.

### Nível 1 — Skill `/context` (implementar agora)

**Arquivo:** `~/.claude/commands/context.md`

**Bloqueador conhecido:** `personal-data-connectors` tem `ModuleNotFoundError: No module named 'azure'`. Antes de implementar o skill, é preciso:
1. Verificar CLI args reais com `python main.py --help` (após fixar deps)
2. Confirmar quais pipelines existem e seus nomes

```
/context
  1. Verifica se personal-data-connectors está operacional (deps instaladas)
  2. Roda o pipeline de contexto diário (CLI args TBD — verificar após fix deps)
  3. Lê os .md gerados em /home/lincoln/obsidian-vault/.raw/
  4. Indexa no context-mode FTS5 (ctx_index)
  5. Confirma: "Dados indexados. Use ctx_search para consultar."
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
| 2 | Profile ampliado | `~/.claude/projects/-home-lincoln/memory/user_profile.md` + `MEMORY.md` update | 15min |
| 3 | Hook de sugestão | `.claude/settings.json` hooks | 15min |
| 4 | `/context` skill | `~/.claude/commands/context.md` | 30min |

---

## Fora de Escopo

- Migração para Pinecone ou vector DB
- Skills específicas de domínio/negócio (próximo ciclo)
- MCP server para personal-data-connectors (Nível 2)
- Loop explícito de self-improvement de skills
- Integração com Hermes Agent

---

## Notas de Correção (Review v2)

Correções aplicadas após review do usuário:

1. **Profile** → global (`~/.claude/projects/-home-lincoln/memory/user_profile.md`), não por-projeto. Amplia arquivo existente.
2. **`python main.py --pipeline daily`** → CLI args não verificados. Pipeline tem deps quebradas (`azure` module). Skill marcado com bloqueador.
3. **Napkin** → skill existe em `~/.claude/skills/napkin/` (lê/escreve `.claude/napkin.md` continuamente). `/end-session` só garante captura final.
4. **"Napkin re-priorizado a cada sessão"** → removido da tabela de buckets. Napkin é curado pelo skill durante o trabalho, não re-priorizado.
5. **Hook regex** → adicionado boundary e detecção no final da mensagem para evitar falsos positivos.
6. **Auto-archive** → referência explícita ao preserve Step 6 (CLAUDE-Archive.md).
7. **Vault Sessões/ path** → verificado, existe em `/home/lincoln/obsidian-vault/Áreas/Dev/Projetos/vps-setup/Sessões/`.
