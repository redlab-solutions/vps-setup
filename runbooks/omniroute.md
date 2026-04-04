# OmniRoute — Runbook de Operações

## URLs
- Dashboard: https://llm-proxy.redlabsolutions.com.br/
- API: https://llm-proxy.redlabsolutions.com.br/v1/chat/completions

## Subir / Parar

```bash
# Subir
docker compose -f docker-compose.omniroute.yml up -d

# Parar
docker compose -f docker-compose.omniroute.yml down

# Ver logs
docker compose -f docker-compose.omniroute.yml logs -f
```

## Update

```bash
docker compose -f docker-compose.omniroute.yml pull && docker compose -f docker-compose.omniroute.yml up -d
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
docker compose -f docker-compose.omniroute.yml up -d --force-recreate
```
