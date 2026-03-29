# Runbooks — Navegação Autenticada

Repositório de runbooks para sessões VNC compartilhadas no webtop da VPS.

Cada arquivo = um site/serviço com steps de login e validação.

## Formato
Ver `template.md` para modelo completo.

## Runbooks existentes
(nenhum ainda — adicionar conforme necessidade)

## Como usar

1. Ler runbook do serviço desejado
2. Conectar ao VNC: `docker exec -it webtop gvncviewer localhost:5900 --shared`
3. Executar passos do runbook
4. Capturar screenshot a cada passo (OBRIGATÓRIO)
5. Salvar evidências em `debug-sessions/YYYY-MM-DD-[contexto]/`

## Estrutura de evidências

```
debug-sessions/
  2026-03-29-github-oauth/
    evidence_001_login_page.png
    evidence_002_2fa_page.png
    evidence_003_dashboard.png
    runbook_used.md
```

## Criando novo runbook

1. Copiar `template.md` para `[serviço]-[contexto].md`
2. Preencher URL, seletores, steps
3. Testar o runbook na sessão VNC
4. Commitar: `git add runbooks/ && git commit -m "feat(runbook): add [serviço] login runbook"`
