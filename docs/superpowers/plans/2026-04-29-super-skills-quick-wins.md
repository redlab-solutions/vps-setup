# Super Skills VPS Quick Wins — Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Consolidate fragmented memory/workflow systems into 4 quick wins: unified `/end-session` skill, global strategic profile, session-end hook, and personal-data-connectors integration skill.

**Architecture:** All changes are configuration-only (markdown skill files, CLAUDE.md edits, settings.json hooks). No new services, no code compilation. Skills are Claude Code custom commands (markdown files in `~/.claude/commands/`).

**Tech Stack:** Claude Code custom commands (`.md` with frontmatter), `~/.claude/settings.json` hooks, `~/CLAUDE.md` (user-level instructions).

---

## File Structure

| File | Action | Purpose |
|---|---|---|
| `~/.claude/commands/end-session.md` | Create | Orchestrator skill: preserve → napkin → compress → profile → summary |
| `~/CLAUDE.md` | Modify | Add `## Profile Estratégico` section at end |
| `~/.claude/settings.json` | Modify | Add `UserPromptSubmit` hook for session-end detection |
| `~/.claude/commands/context.md` | Create | Skill to run personal-data-connectors pipeline and index results |
| `~/vps-setup/CLAUDE.md` | Modify | Update session-end flow docs to reference `/end-session` |

**Key discovery:** User-level CLAUDE.md is at `/home/lincoln/CLAUDE.md` (NOT `~/.claude/CLAUDE.md`). Global settings at `~/.claude/settings.json`. Project settings at `~/vps-setup/.claude/settings.json`.

---

## Task 1: Create `/end-session` Skill

**Files:**
- Create: `/home/lincoln/.claude/commands/end-session.md`

**Reference files to read before implementing:**
- `/home/lincoln/.claude/commands/vault-preserve.md` — preserve logic to inline
- `/home/lincoln/.claude/commands/vault-compress.md` — compress logic to inline
- `/home/lincoln/vps-setup/.claude/napkin.md` — napkin format for this project

- [ ] **Step 1: Create the end-session skill file**

Write `/home/lincoln/.claude/commands/end-session.md` with this content:

```markdown
---
context: conversation
description: End-of-session workflow — preserve, napkin, compress, profile update (one command)
model: opus
allowed-tools: Read, Edit, Write, Glob, Bash, AskUserQuestion
---

# /end-session — Unified Session-End Workflow

Runs the full session-end pipeline: preserve → napkin → compress → profile update → summary.

## Instructions for Claude

When the user runs `/end-session`, execute these phases IN ORDER.

---

### Phase 1: Auto-Preserve (no questions)

Auto-detect what changed this session and update CLAUDE.md.

**Detection steps:**

1. Run `git diff --stat` to find modified files
2. Run `git log --oneline -10` to find recent commits
3. Check TaskList for completed/active tasks
4. Read current CLAUDE.md to understand existing structure

**Apply updates to CLAUDE.md:**

- Status changes (1 line each)
- Decisions + rationale (table row format)
- New directories/files (brief list)
- Next steps
- Use single-line entries, not paragraphs
- Target: CLAUDE.md under 280 lines

**If CLAUDE.md > 280 lines:**

1. Identify auto-archivable content: `## Session Notes (DATE)` sections older than 7 days, `## Completed Projects` section, sections marked `(ARCHIVABLE)`
2. Auto-archive to `{project_root}/CLAUDE-Archive.md` (append with date header)
3. Remove archived sections from CLAUDE.md
4. Never archive sections marked `(PROTECTED)` or core sections (Commands, Services, Gotchas, Paths, Structure)

**Report:**
```
CLAUDE.md updated (+X lines, now Y total)
Archived Z lines to CLAUDE-Archive.md
```

---

### Phase 2: Napkin Capture (1 question)

Ask the user:

**Question:** "Alguma lição desta sessão para o napkin?"

**Options:**
1. **Sim** — descreva a lição
2. **Não** — pular

**If yes:** Edit `{project_root}/.claude/napkin.md` — add item with format:
```
N. **[YYYY-MM-DD] {brief title}**
   Do instead: {what to do differently}
```

Add to the appropriate category (or create new one). Do NOT impose item limits — the napkin skill curates during work.

**If no:** Skip.

---

### Phase 3: Compress (no questions — auto-detect everything)

Generate session log and dual-write.

1. **Generate topic name** from session content (3-5 words, lowercase, hyphens). Show suggestion, accept confirmation or alternative.

2. **Generate session log** with this structure:

```markdown
---
tipo: sessao-dev
data: {YYYY-MM-DD}
projeto: {project_name}
status: concluido
tags: [{confidence keywords, max 3}]
---

# Session Log: {DD-MM-YYYY HH:MM} - {topic-name}

## Quick Reference (for AI scanning)
**Confidence keywords:** {keywords}
**Projects:** {project_name}
**Outcome:** {1-sentence summary}

## Decisions Made
- {auto-detected decisions}

## Key Learnings
- {auto-detected learnings}

## Files Modified
- `{path}`: {what changed}

## Pending Tasks
- {any unfinished work}

## Quick Resume Context
{2-3 sentences for future sessions}

---
## Raw Session Log
{FULL CONVERSATION}
```

3. **Detect project root:** Walk up from pwd looking for CLAUDE.md or .git

4. **Dual-write:**
   - `{project_root}/CC-Session-Logs/{filename}`
   - `/home/lincoln/obsidian-vault/Áreas/Dev/Projetos/{project_name}/Sessões/{filename}`

5. **Update daily note:**
   - Path: `/home/lincoln/obsidian-vault/Calendário/Diário/{YYYY-MM-DD}.md`
   - If doesn't exist, create with `diario-op` frontmatter
   - Append to `## Sessões de hoje` section:
     `- [[Áreas/Dev/Projetos/{project_name}/Sessões/{filename_without_ext}]]`

**Filename format:** `{DD-MM-YYYY}-{HH_MM}-{topic-name}.md`

---

### Phase 4: Profile Update

Read `/home/lincoln/CLAUDE.md` and check if `## Profile Estratégico` section exists.

**If it exists:** Update `### Foco Atual` and `### Decisões Pendentes` if anything changed this session. Update `### Última Atualização` date. Keep total profile section under 50 lines — remove resolved items.

**If it doesn't exist:** Create the section at the end of `/home/lincoln/CLAUDE.md`:
```markdown
## Profile Estratégico

### Foco Atual
- {current focus from session}

### Decisões Pendentes
- {any open decisions}

### Última Atualização: {YYYY-MM-DD}
```

---

### Phase 5: Summary

Output:

```markdown
## Session Ended

| Phase | Status |
|---|---|
| CLAUDE.md | Updated (Y lines) |
| Napkin | {added N items / skipped} |
| Session Log | {local path} + {vault path} |
| Daily Note | Updated |
| Profile | {updated / no changes} |

**Next:** Run `/compact` when ready to clear the context window.
```

---

## Guidelines

- **Preserve everything by default.** The only question is the napkin.
- **Auto-detect, don't ask.** Git diff, task list, and conversation provide all the signal.
- **Compact is NEVER automatic.** Only suggest it.
- **Fallback:** Individual skills (`/vault-preserve`, `/vault-compress`) remain available for granular control.
- **Use the Edit tool** for CLAUDE.md and napkin.md modifications (read first, then edit).
- **Use the Write tool** for session log files (new files each time).
- **Use the Bash tool** only for `git diff`, `git log`, `wc -l`, `mkdir -p`.
```

- [ ] **Step 2: Verify the skill file was created correctly**

Run: `cat ~/.claude/commands/end-session.md | head -5`
Expected: Shows the frontmatter with `description: End-of-session workflow`

- [ ] **Step 3: Commit**

```bash
cd /home/lincoln/vps-setup
git add -f ~/.claude/commands/end-session.md
git commit -m "feat: add /end-session unified session-end skill"
```

Note: If `~/.claude/commands/` is outside the repo, commit only the plan/spec. The skill file lives in the user's home directory.

---

## Task 2: Add Profile Estratégico to User-Level CLAUDE.md

**Files:**
- Modify: `/home/lincoln/CLAUDE.md` (append section at end)

**Reference:** Read `/home/lincoln/CLAUDE.md` first to find the exact end of file.

- [ ] **Step 1: Read current CLAUDE.md end**

Run: `wc -l /home/lincoln/CLAUDE.md`
Expected: ~98 lines (from the file read earlier)

- [ ] **Step 2: Append Profile Estratégico section**

Use Edit to append after the last line (`- Pacotes que precisam de chave GPG via curl → usar ...`). Add:

```markdown

## Profile Estratégico

### Foco Atual
- vps-setup: infraestrutura e consolidação de workflow

### Decisões Pendentes
- (nenhuma)

### Última Atualização: 2026-04-29
```

- [ ] **Step 3: Verify the section was added**

Run: `tail -12 /home/lincoln/CLAUDE.md`
Expected: Shows the Profile Estratégico section with 3 subsections.

- [ ] **Step 4: Update the session-end flow docs in CLAUDE.md**

In `/home/lincoln/CLAUDE.md`, find the existing `**Fluxo fim de sessão (sempre nesta ordem):**` section (lines 75-78) and update it:

**Old content:**
```
**Fluxo fim de sessão (sempre nesta ordem):**
1. /vault-preserve → aprendizados permanentes no CLAUDE.md do projeto
2. /vault-compress → salva log local + no vault + link na nota do dia
3. /compact  → limpa context window (SEMPRE por último)
```

**New content:**
```
**Fluxo fim de sessão:**
- `/end-session` → preserva tudo + napkin + compress + profile (um comando)
- Skills individuais (`/vault-preserve`, `/vault-compress`) continuam disponíveis para controle granular
- `/compact` → limpa context window (SEMPRE por último, manual)
```

- [ ] **Step 5: Commit the CLAUDE.md change**

The file `/home/lincoln/CLAUDE.md` is outside the git repo. No git commit needed — just verify the file was saved.

Verify: `grep -c "Profile Estratégico" /home/lincoln/CLAUDE.md`
Expected: 1

---

## Task 3: Update Project CLAUDE.md Session Flow

**Files:**
- Modify: `/home/lincoln/vps-setup/CLAUDE.md` — no changes needed to this file (it doesn't have session flow instructions). The session flow is in the user-level `~/CLAUDE.md` which was updated in Task 2.

**However**, update the VPS project's CLAUDE.md to mention `/end-session` as the recommended way to end a session.

- [ ] **Step 1: Check if vps-setup CLAUDE.md has session flow docs**

Run: `grep -n "vault-preserve\|vault-compress\|end-session" /home/lincoln/vps-setup/CLAUDE.md`

If no matches, the project CLAUDE.md doesn't reference session flow — nothing to change. Skip this task.

If matches found, update references from individual skills to `/end-session`.

- [ ] **Step 2: Commit (if changes were made)**

```bash
git add CLAUDE.md
git commit -m "docs: reference /end-session in session flow"
```

---

## Task 4: Add Session-End Hook

**Files:**
- Modify: `/home/lincoln/.claude/settings.json` — add to `hooks.UserPromptSubmit` array
- Create: `/home/lincoln/.claude/hooks/session-end-reminder.sh` — the hook script

**Reference:** Current `UserPromptSubmit` hooks in `~/.claude/settings.json` (lines 31-39):
```json
"UserPromptSubmit": [
  {
    "hooks": [
      {
        "type": "command",
        "command": "npx -y ccstatusline@latest --hook"
      }
    ]
  }
]
```

- [ ] **Step 1: Create the hook script**

Write `/home/lincoln/.claude/hooks/session-end-reminder.sh`:

```bash
#!/usr/bin/env bash
# Detects farewell patterns in user messages and suggests /end-session
# Hook: UserPromptSubmit — reads user message from stdin

INPUT="$(cat)"
# Check if message matches farewell patterns (anchored to end of message)
if echo "$INPUT" | grep -qiE '\b(tchau|bye|sair|encerrar|goodbye|fim|até\s+mais|done\s+for\s+today|isso\s+é\s+tudo|por\s+hoje\s+é\s+só)\s*[.!?]?\s*$'; then
  echo ""
  echo "💡 Sugestão: rode /end-session antes de sair para preservar o contexto desta sessão."
  echo ""
fi
```

- [ ] **Step 2: Make the hook script executable**

Run: `chmod +x /home/lincoln/.claude/hooks/session-end-reminder.sh`

- [ ] **Step 3: Add hook to settings.json**

Read `/home/lincoln/.claude/settings.json` first (needed for Edit). Then add a new entry to the `UserPromptSubmit` array.

**Current** (lines 31-39):
```json
    "UserPromptSubmit": [
      {
        "hooks": [
          {
            "type": "command",
            "command": "npx -y ccstatusline@latest --hook"
          }
        ]
      }
    ],
```

**New:**
```json
    "UserPromptSubmit": [
      {
        "hooks": [
          {
            "type": "command",
            "command": "npx -y ccstatusline@latest --hook"
          }
        ]
      },
      {
        "hooks": [
          {
            "type": "command",
            "command": "/home/lincoln/.claude/hooks/session-end-reminder.sh"
          }
        ]
      }
    ],
```

- [ ] **Step 4: Verify the hook was added correctly**

Run: `python3 -c "import json; d=json.load(open('/home/lincoln/.claude/settings.json')); print(len(d['hooks']['UserPromptSubmit']))"`
Expected: 2 (original + new)

- [ ] **Step 5: Test the hook script manually**

Run: `echo "tchau!" | /home/lincoln/.claude/hooks/session-end-reminder.sh`
Expected: Shows the suggestion message.

Run: `echo "vamos continuar trabalhando" | /home/lincoln/.claude/hooks/session-end-reminder.sh`
Expected: No output (no match).

- [ ] **Step 6: Commit the hook script**

```bash
git add -f /home/lincoln/.claude/hooks/session-end-reminder.sh
git commit -m "feat: add session-end reminder hook for farewell pattern detection"
```

Note: The settings.json is outside the repo. The hook script can be committed if tracked, or left in place.

---

## Task 5: Create `/context` Skill (Personal-Data-Connectors)

**Files:**
- Create: `/home/lincoln/.claude/commands/context.md`

**Blocker:** The `personal-data-connectors` project has broken dependencies (`ModuleNotFoundError: No module named 'azure'`). This task creates the skill structure with a pre-flight check, so it gracefully handles the blocker.

**Reference:** Pipeline lives at `/home/lincoln/personal-data-connectors/`. Output goes to `/home/lincoln/obsidian-vault/.raw/`.

- [ ] **Step 1: Create the context skill file**

Write `/home/lincoln/.claude/commands/context.md`:

```markdown
---
context: conversation
description: Index personal data (calendar, email, trello, github) into context-mode for search
model: opus
allowed-tools: Bash, Read, Write, Glob
---

# /context — Index Personal Data into Session

Runs the personal-data-connectors pipeline and indexes results into context-mode FTS5 for search within the current session.

## Instructions for Claude

### Step 1: Pre-flight Check

Check if personal-data-connectors is operational:

```bash
cd /home/lincoln/personal-data-connectors && python3 -c "import azure.storage.blob" 2>&1
```

**If this fails** (ModuleNotFoundError or ImportError):

Output:
```
⚠️ personal-data-connectors has missing dependencies.
Fix: cd /home/lincoln/personal-data-connectors && pip install -r requirements.txt

Once fixed, run /context again.
```

Stop here. Do not attempt to run the pipeline.

### Step 2: Run the Pipeline

```bash
cd /home/lincoln/personal-data-connectors && python3 main.py --help
```

Based on the output, determine the correct CLI arguments for the daily context pipeline and run it.

**If --help fails**, output the error and stop.

### Step 3: Index Generated Files

Find all `.md` files in `/home/lincoln/obsidian-vault/.raw/`:

```bash
find /home/lincoln/obsidian-vault/.raw/ -name "*.md" -newer /tmp/context-last-run 2>/dev/null || find /home/lincoln/obsidian-vault/.raw/ -name "*.md"
```

For each file, use `ctx_index(path: "/home/lincoln/obsidian-vault/.raw/{relative_path}", source: "personal-data: {category}")`.

Categories based on subdirectory:
- `.raw/meetings/` → `personal-data: meetings`
- `.raw/trello/` → `personal-data: trello`
- `.raw/github-redlab-solutions/` → `personal-data: github`
- `.raw/gmail/` or `.raw/email/` → `personal-data: email`
- Other → `personal-data: misc`

Create a marker file for incremental indexing:
```bash
touch /tmp/context-last-run
```

### Step 4: Confirm

Output:
```
✅ Personal data indexed.

Search with ctx_search(queries: ["reunião hoje", "trello card", "email from X"])

Sources indexed:
- meetings: N files
- trello: N files
- github: N files
- email: N files
```

## Guidelines

- **Never attempt to install deps.** Just report the issue and stop.
- **Use ctx_index** to index files — do not read file contents into context.
- **Incremental:** Only index files newer than last run (using /tmp/context-last-run marker).
- **Source labels** must use `personal-data:` prefix for easy filtering via ctx_search(source: "personal-data").
```

- [ ] **Step 2: Verify the skill file was created correctly**

Run: `cat ~/.claude/commands/context.md | head -5`
Expected: Shows the frontmatter with `description: Index personal data`

- [ ] **Step 3: Commit**

```bash
git add -f ~/.claude/commands/context.md
git commit -m "feat: add /context skill for personal-data-connectors indexing"
```

Note: If the file is outside the repo, just verify it exists. No git commit needed.

---

## Task 6: Update Session Flow in VPS Project CLAUDE.md

**Files:**
- Modify: `/home/lincoln/vps-setup/CLAUDE.md` — update Vault section if it references individual skills

- [ ] **Step 1: Check if vps-setup CLAUDE.md has Vault session flow**

Run: `grep -n "Vault\|Sessões\|vault-preserve\|vault-compress" /home/lincoln/vps-setup/CLAUDE.md`

The file has a `## Vault` section at the end. If it references individual skills, update to reference `/end-session`.

Current content (last lines):
```
## Vault
Sessões em: /home/lincoln/obsidian-vault/Áreas/Dev/Projetos/vps-setup/Sessões/
```

This is just a path reference — no session flow instructions. No changes needed.

- [ ] **Step 2: Verify no changes needed**

If grep shows only the Vault path line, skip this task. No commit needed.

---

## Post-Implementation Verification

After all tasks are complete, run these checks:

- [ ] **Verify all files exist:**

```bash
ls -la ~/.claude/commands/end-session.md
ls -la ~/.claude/commands/context.md
ls -la ~/.claude/hooks/session-end-reminder.sh
grep "Profile Estratégico" ~/CLAUDE.md
```

Expected: All files exist, Profile section found.

- [ ] **Verify hook is registered:**

```bash
python3 -c "import json; d=json.load(open('/home/lincoln/.claude/settings.json')); print('UserPromptSubmit hooks:', len(d['hooks']['UserPromptSubmit']))"
```

Expected: 2 hooks registered.

- [ ] **Verify session-end flow in user CLAUDE.md:**

```bash
grep -A5 "Fluxo fim de sessão" ~/CLAUDE.md
```

Expected: Shows `/end-session` reference instead of individual skills.

- [ ] **Final commit (if any uncommitted changes):**

```bash
git status
```

Commit any remaining changes.
