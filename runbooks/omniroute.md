# OmniRoute — Runbook de Operações

## URLs
- Dashboard: https://llm-proxy.redlabsolutions.com.br/
- API: https://llm-proxy.redlabsolutions.com.br/v1/chat/completions

## Subir / Parar

```bash
# Subir
docker compose up -d omniroute

# Parar
docker compose stop omniroute

# Ver logs
docker compose logs -f omniroute
```

## Update

```bash
docker compose pull omniroute && docker compose up -d omniroute
```

## Recarregar Caddy

```bash
docker compose restart caddy
```

## Backup

1. Abrir dashboard → Settings → Backup → Export
2. Salvar em `./backups/omniroute/YYYY-MM-DD.json`

## Restore

1. dashboard → Settings → Backup → Import
2. Selecionar arquivo de backup

## Verificar saúde

```bash
curl -H "Authorization: Bearer or_live_<SUA_KEY>" \
  https://llm-proxy.redlabsolutions.com.br/v1/models
```

## Reset de senha inicial

```bash
# Editar o .env e trocar OMNIROUTE_INITIAL_PASSWORD
# Depois recriar o container:
docker compose up -d --force-recreate omniroute
```
