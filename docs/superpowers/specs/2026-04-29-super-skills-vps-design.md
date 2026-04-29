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
| **Profile** | Foco atual, decisões pendentes, preferências | `~/.claude/CLAUDE.md` (user-level — carregado em TODA sessão, independentemente do diretório) | Mutável. < 50 linhas. Seção dedicada no fim do arquivo. |
| **Knowledge** | Fatos imutáveis: arquitetura, configs, runbooks | `CLAUDE.md` + `memory/project_*.md` + `memory/reference_*.md` | Atualizado via preserve. Consultado quando relevante. |
| **Session Log** | O que aconteceu numa sessão — contexto temporal | `CC-Session-Logs/` + `context-mode` FTS5 | Auto-salvo via compress. Buscável via ctx_search. |
| **Feedback** | Lições aprendidas, "do instead", padrões | `memory/feedback_*.md` + `.claude/napkin.md` | Acumulado ao longo do tempo. Napkin editado manualmente via `/end-session`. |

### Mudanças concretas

- `~/.claude/CLAUDE.md` — adicionar seção `## Profile Estratégico` com Foco Atual e Decisões Pendentes. Este arquivo é carregado em TODA sessão, independentemente do diretório de trabalho (user-level CLAUDE.md).
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
                Se sim → edita {project_root}/.claude/napkin.md diretamente (adiciona item com data + "Do instead")
                Nota: o napkin skill original não impõe limite de itens — "the agent designs the initial structure and adapts it to the project's domain". **Decisão de design:** o `/end-session` NÃO impõe limite artificial. O napkin skill já cura o conteúdo durante o trabalho.
                Se não → pula
                Nota: skill napkin (~/.claude/skills/napkin/) já lê o .claude/napkin.md a cada sessão e escreve continuamente durante o trabalho. O end-session só garante captura final se houver lição não registrada.

  3. [compress] Gera session log com tudo
                Dual-write: local (CC-Session-Logs/) + vault (Sessões/)
                Cria/atualiza daily note com link (já integrado no compress Step 5)

  4. [profile]  Atualiza ~/.claude/CLAUDE.md (seção Profile Estratégico) se houver mudança em foco ou decisões

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

**Arquivo:** `~/.claude/CLAUDE.md` (user-level — carregado em TODA sessão, independentemente do diretório)

Claude Code carrega memória por escopo de projeto (`~/.claude/projects/-home-lincoln-vps-setup/memory/` só é visível em `~/vps-setup/`). O user-level `~/.claude/CLAUDE.md` é o único mecanismo que é sempre carregado, em qualquer diretório. É o local correto para o profile estratégico global.

Adicionar seção ao final do `~/.claude/CLAUDE.md` existente:

```markdown
## Profile Estratégico

### Foco Atual
- [1-2 projetos/áreas ativos com contexto mínimo]

### Decisões Pendentes
- [Decisões abertas que futuras sessões precisam saber]

### Última Atualização: YYYY-MM-DD
```

### Governação

- `/end-session` atualiza automaticamente se houver mudanças em foco ou decisões
- Mantém < 50 linhas no total — itens resolvidos saem
- Seções vazias = sem mudança desde última atualização
- `user_profile.md` no memory de cada projeto mantém papel atual (preferências técnicas por-projeto) — não é afetado
- O profile em `~/.claude/CLAUDE.md` perde frontmatter/type metadata — aceitável pois é conteúdo estratégico, não queryável por tipo

---

## 4. Hook de Sugestão de Fim de Sessão

**Problema:** Não existe hook `SessionEnd` nativo no Claude Code.

**Alternativa:** Hook `UserPromptSubmit` com detecção heurística de padrões de saída.

**Arquivo:** `.claude/settings.json` (projeto) — adicionar ao array `hooks.UserPromptSubmit`

**Padrões detectados (regex unificado, ancorado ao final da mensagem):** `\b(tchau|bye\b.*|sair|encerrar|goodbye|fim|até\s+mais|done\s+for\s+today|isso\s+é\s+tudo|por\s+hoje\s+é\s+só)\s*[.!?]?\s*$` — todos os padrões ancorados com `$`, evitando falsos positivos como "fim de semana" ou "até que".

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
| 2 | Profile ampliado | `~/.claude/CLAUDE.md` (seção Profile Estratégico) | 15min |
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

## Notas de Correção

### Review v2

1. **Profile** → global (`~/.claude/projects/-home-lincoln/memory/user_profile.md`), não por-projeto. Amplia arquivo existente.
2. **`python main.py --pipeline daily`** → CLI args não verificados. Pipeline tem deps quebradas (`azure` module). Skill marcado com bloqueador.
3. **Napkin** → skill existe em `~/.claude/skills/napkin/` (lê/escreve `.claude/napkin.md` continuamente). `/end-session` só garante captura final.
4. **"Napkin re-priorizado a cada sessão"** → removido da tabela de buckets. Napkin é curado pelo skill durante o trabalho, não re-priorizado.
5. **Hook regex** → adicionado boundary e detecção no final da mensagem para evitar falsos positivos.
6. **Auto-archive** → referência explícita ao preserve Step 6 (CLAUDE-Archive.md).
7. **Vault Sessões/ path** → verificado, existe em `/home/lincoln/obsidian-vault/Áreas/Dev/Projetos/vps-setup/Sessões/`.

### Review v3

8. **Profile NÃO é global via memory/** → Claude Code carrega memória por escopo de projeto. `user_profile.md` em `-home-lincoln/memory/` é invisível em outros projetos. **Correção:** profile estratégico vive em `~/.claude/CLAUDE.md` (user-level), que é carregado em TODA sessão.
9. **Hook regex inconsistente** → dois patterns com ancoragem diferente. **Correção:** unificado com `\s*[.!?]?\s*$` em todos os padrões.
10. **Napkin "max 10 por categoria"** → não é regra do napkin skill original. **Correção:** removido o limite. Marcado como decisão de design explícita.
