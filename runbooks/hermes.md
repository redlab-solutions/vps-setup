# Hermes Agent Runbook

## Overview
Hermes Agent is an autonomous AI agent by Nous Research. Runs as a native Python process, accessible via Telegram 24/7. Uses Camofox for browser automation.

## Architecture
- **Process:** systemd service `hermes-agent`
- **LLM:** z.ai/GLM-5-turbo (configurable with `hermes model`)
- **Browser:** Camofox (`localhost:9377`, native Node.js process)
- **Interface:** Telegram bot
- **Workspace:** `/home/lincoln/workspace`
- **Config:** `~/.hermes/` (config.yaml, .env)

## Common Operations

### Check Status
```bash
sudo systemctl status hermes-agent
sudo systemctl status camofox
```

### View Logs
```bash
sudo journalctl -u hermes-agent -f           # Live tail
sudo journalctl -u hermes-agent --since "1h"  # Last hour
sudo journalctl -u camofox -f                 # Camofox logs
```

### Restart
```bash
sudo systemctl restart hermes-agent
sudo systemctl restart camofox
```

### Update
```bash
hermes update
sudo systemctl restart hermes-agent
```

### Switch Model
```bash
hermes model  # Interactive selection
# Or via Telegram: /model openrouter:hermes-3-llama-3.1-405b
```

## Troubleshooting

### Gateway not responding on Telegram
1. `sudo systemctl status hermes-agent`
2. `sudo journalctl -u hermes-agent --since "5m"`
3. Check if LLM provider is up: `hermes chat -q "test"`
4. Restart: `sudo systemctl restart hermes-agent`

### Browser tools not working
1. `sudo systemctl status camofox`
2. Check health: `curl -s http://localhost:9377/health`
3. Check Hermes config: `grep camofox ~/.hermes/config.yaml`
4. Restart: `sudo systemctl restart camofox`

### LLM errors
1. Check API key: `grep GLM_API_KEY ~/.hermes/.env`
2. Switch provider: `hermes model`
3. Check logs: `sudo journalctl -u hermes-agent --since "5m"`

## Config Location
- Main config: `~/.hermes/config.yaml`
- API keys: `~/.hermes/.env`
- Memories: `~/.hermes/memories/`
- Skills: `~/.hermes/skills/`
- Sessions: `~/.hermes/sessions/`
