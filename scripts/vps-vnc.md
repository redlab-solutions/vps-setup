# VPS Shared VNC — Operating Protocol

**Scope:** Esta skill se aplica apenas ao projeto `vps-setup` em `/home/lincoln/vps-setup/`.

## Quando usar

Usar quando o usuário pedir para:
- "Debugar algo no browser"
- "Validar um fluxo autenticado"
- "Fazer login em [site] e continuar de onde parei"
- "Verificar como [feature] aparece logado"
- "Inspecionar elemento na página"
- Qualquer tarefa que requeira interação com UI web ou debugging de páginas autenticadas

## Como conectar ao VNC

```bash
# Verificar que webtop está rodando
sudo docker ps --filter name=webtop

# Conectar ao VNC compartilhado (mesma sessão do usuário)
# gvncviewer está no HOST, não no container
gvncviewer localhost:5900 --shared
```

**Nota:** `--shared` permite múltiplas conexões simultâneas na mesma sessão do desktop.

**Importante:** Usar `--shared` para permitir múltiplas conexões simultâneas na mesma sessão.

## Captura de Evidência (OBRIGATÓRIO)

Após cada ação significativa, capturar screenshot:

```bash
# Screenshot via docker exec no container
docker exec webtop scrot -o /tmp/evidence.png
docker cp webtop:/tmp/evidence.png /tmp/evidence_$(date +%Y%m%d_%H%M%S).png
```

Exibir sempre o caminho do arquivo para o usuário.

**Regra:** Nenhuma validação de UI sem screenshot como evidência.

## Ferramentas disponíveis no container

```bash
# Browser via CLI
docker exec -it webtop firefox --screenshot /tmp/shot.png https://url.com
docker exec -it webtop chromium-browser --screenshot /tmp/shot.png https://url.com

# Download/Upload
docker cp arquivo.txt webtop:/tmp/
docker cp webtop:/tmp/resultado.txt .

# Network debugging
docker exec -it webtop curl -v https://...
docker exec -it webtop wget -O /tmp/page.html https://...

# DevTools - abrir no browser do container
docker exec -it webtop xdg-open http://localhost:3000
```

## Playwright-CLI para validações agênticas

Para validações programáticas (não visuais):

```bash
# Instalar no container (se não existir)
docker exec webtop bash -c "cd /tmp && npm install -g playwright-cli 2>/dev/null || npx playwright-cli@latest"

# Exemplo: screenshot de página autenticada
docker exec webtop npx playwright-cli screenshot https://example.com/dashboard --output /tmp/pw_shot.png

# Copiar resultado
docker cp webtop:/tmp/pw_shot.png .
```

## Runbooks de navegação

Repositório: `/home/lincoln/vps-setup/runbooks/`

Formato: cada arquivo = um site/serviço com steps de login e validação.
Ver `runbooks/README.md` e `runbooks/template.md` para modelo.

## Evidências de sessão

Salvar em: `/home/lincoln/vps-setup/debug-sessions/YYYY-MM-DD-[contexto]/`

Estrutura:
```
debug-sessions/
  2026-03-29-oauth-github/
    evidence_001_login.png
    evidence_002_dashboard.png
    runbook_used.md
```

## Portas e segurança

| Porta | Bind | Uso |
|--------|------|-----|
| 3000 | 127.0.0.1 | KasmVNC web |
| 5900 | 127.0.0.1 | VNC nativo |

Tudo exposto apenas em localhost — acesso público é bloqueado.

## Playwright CLI — Modo Autônomo (PRINCIPAL)

Usar playwright-cli para automação na sessão autenticada existente (:0).
**Usa a mesma instância chromium que o usuário vê no VNC.**

```bash
# Navegar para URL
docker exec webtop npx playwright-cli navigate https://url.com

# Screenshot (captura sessão autenticada existente)
docker exec webtop npx playwright-cli screenshot https://url.com --output /tmp/shot.png

# Clicar elemento CSS
docker exec webtop npx playwright-cli click "button.submit"

# Digitar em campo
docker exec webtop npx playwright-cli type "input[name='email']" "user@example.com"

# Extrair DOM/JS
docker exec webtop npx playwright-cli evaluate "document.title" --output /tmp/dom.txt

# Copiar resultado (sempre fazer após comando)
docker cp webtop:/tmp/shot.png .
docker cp webtop:/tmp/dom.txt .
```

## Iteração com Checkpoint — Autoresearch Loop

Loop Modify → Verify → Keep/Discard:

```
1. MODIFY  — playwright-cli: click, type, navigate
2. COMMIT  — git commit antes da verificação
3. VERIFY  — screenshot + DOM evaluate
4. KEEP    — se funcionou → avançar
5. DISCARD — se falhou → reverter git
6. LOG     — metadata.json + screenshot em debug-sessions/
7. CHECKPOINT — se irreversível → pausar + Telegram
8. REPEAT
```

## Checkpoint — Quando Pausar

**Pausa em:**
- Confirmar pedido/pagamento
- Enviar mensagem em nome do usuário
- Excluir recurso (repo, arquivo, dado)
- Submeter formulário crítico

**Não pausa:**
- Navegação comum (clicks, scroll, leitura)
- Preencher campos (sem submit)
- Screenshots e coleta de evidências

## Checkpoint — Comandos

```bash
# Pausar e notificar Telegram
python3 /home/lincoln/vps-setup/scripts/vps-vnc-helpers.py checkpoint "[URL]" "[ação]" "[selector]" "[Opção1,Opção2]"

# Resolver checkpoint após resposta do usuário
python3 /home/lincoln/vps-setup/scripts/vps-vnc-helpers.py resolve <checkpoint_id> <opção_escolhida>

# Ver checkpoint ativo
python3 /home/lincoln/vps-setup/scripts/vps-vnc-helpers.py active

# Notificação Telegram avulsa
python3 /home/lincoln/vps-setup/scripts/vps-vnc-helpers.py notify "Mensagem livre"
```

## Evidência — Auto-Collection

```bash
# Iniciar sessão de evidência
python3 /home/lincoln/vps-setup/scripts/vps-vnc-helpers.py init-session [contexto]
# Retorna: /home/lincoln/vps-setup/debug-sessions/YYYY-MM-DD-[contexto]/

# Logar iteração
python3 /home/lincoln/vps-setup/scripts/vps-vnc-helpers.py log <session_dir> <n> <action> <url> <selector> <result> <screenshot>

# Coleta rápida de screenshot (playwright-cli na sessão autenticada)
bash /home/lincoln/vps-setup/scripts/vps-vnc-evidence.sh [session_dir_name] [label]
```

## Configuração Telegram

```bash
# Definir chat ID (obter via @userinfobot no Telegram primeiro)
python3 /home/lincoln/vps-setup/scripts/vps-vnc-helpers.py config set chat_id <seu_chat_id>

# Testar notificação
python3 /home/lincoln/vps-setup/scripts/vps-vnc-helpers.py notify "Teste OK"
```

## Scripts versionados

- Helper: `/home/lincoln/vps-setup/scripts/vps-vnc-helpers.py`
- Evidence: `/home/lincoln/vps-setup/scripts/vps-vnc-evidence.sh`
- Versão master: https://github.com/redlab-solutions/vps-setup
