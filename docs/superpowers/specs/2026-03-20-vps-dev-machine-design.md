# VPS Dev Machine na Nuvem — Design Spec

**Data:** 2026-03-20
**Status:** Aprovado
**Projeto:** /home/lincoln/vps-setup

---

## Contexto

Transformar um VPS Contabo (Ubuntu 24.04, 8GB RAM, 72GB disco) em uma máquina de desenvolvimento pessoal na nuvem, acessível exclusivamente via Tailscale. O VPS serve como second brain (Obsidian) e ambiente de desenvolvimento completo (VS Code), sem exposição pública.

---

## Requisitos

- Acesso ao Obsidian via browser em `obsidian.redlabsolutions.com.br` (Tailscale only)
- Acesso ao VS Code via browser em `code.redlabsolutions.com.br` (Tailscale only)
- Acesso ao VS Code via desktop nativo (VS Code Remote Tunnels)
- HTTPS válido nos subdomínios (Let's Encrypt via DNS-01)
- Isolamento total: sem portas públicas além de SSH temporário durante setup
- Obsidian vault persistido no host, sobrevive recriação de containers
- Workspace compartilhado entre code-server e Remote Tunnels

---

## Arquitetura

```
[Dispositivo do usuário]
  ↕ Tailscale VPN
[VPS Contabo — Ubuntu 24.04]
  ├── Tailscale (host, IP: 100.x.x.x)
  ├── Caddy (bind: 100.x.x.x:80/443)
  │   ├── code.redlabsolutions.com.br → code-server:8443
  │   └── obsidian.redlabsolutions.com.br → webtop:3000
  ├── Docker Compose
  │   ├── code-server (lscr.io/linuxserver/code-server)
  │   ├── webtop (lscr.io/linuxserver/webtop:alpine-xfce)
  │   └── caddy (imagem customizada com plugin godaddy DNS)
  └── code-tunnel.service (systemd, usuário lincoln)
```

### Fluxo de acesso

1. Usuário conecta ao Tailscale no dispositivo
2. DNS resolve `*.redlabsolutions.com.br` → 100.x.x.x (IP Tailscale do VPS)
3. Caddy recebe requisição, termina TLS, faz proxy para container
4. Para VS Code desktop: Remote Tunnels autentica via GitHub relay (independente do Tailscale)

---

## Componentes

### Tailscale
- Instalado no host (não em container)
- Auth key reutilizável configurada
- SSH acessível via IP Tailscale
- Porta 22 pública desabilitada após setup

### Caddy
- Imagem customizada: `caddy build --with github.com/caddy-dns/godaddy`
- Bind exclusivo no IP Tailscale (100.x.x.x)
- Certificados via DNS-01 challenge (GoDaddy API)
- Caddyfile define dois virtual hosts

### code-server
- Imagem: `lscr.io/linuxserver/code-server`
- Porta interna: 8443
- Volume: `/home/lincoln/workspace → /config/workspace`
- Autenticação: variável `PASSWORD` no `.env`
- restart: unless-stopped

### Webtop
- Imagem: `lscr.io/linuxserver/webtop:alpine-xfce`
- Porta interna: 3000 (KasmVNC)
- Volume: `/home/lincoln/obsidian-vault → /config/obsidian-vault`
- Obsidian instalado via AppImage após primeiro boot
- Alpine XFCE: ~250MB RAM em uso
- restart: unless-stopped

### VS Code Remote Tunnels
- Serviço systemd do usuário `lincoln`
- Executa: `code tunnel --accept-server-license-terms --name contabo-dev`
- Acessa `/home/lincoln/workspace`
- Autenticação via GitHub (primeira execução manual)
- WantedBy: default.target

---

## Estrutura de arquivos

```
/home/lincoln/
├── workspace/              # código e projetos (compartilhado entre code-server e tunnel)
├── obsidian-vault/         # vault Obsidian (persistido no host)
└── vps-setup/
    ├── docker-compose.yml
    ├── Caddyfile
    ├── Dockerfile.caddy    # build imagem caddy com plugin godaddy
    ├── .env                # GODADDY_API_KEY, GODADDY_API_SECRET, CODESERVER_PASSWORD, WEBTOP_PASSWORD
    └── .env.example        # template sem secrets
```

`.env` não deve ser commitado. Adicionar ao `.gitignore`.

---

## Segurança

| Aspecto | Decisão |
|---|---|
| Acesso externo | Apenas via Tailscale |
| Porta 22 pública | Desabilitada após setup completo |
| TLS | Let's Encrypt via DNS-01 (sem porta 80 pública) |
| Caddy bind | Exclusivo no IP Tailscale |
| Secrets | Apenas em `.env` local, nunca commitado |
| Containers | Rodam como usuário não-root (PUID/PGID = lincoln) |
| Remote Tunnels | Relay Microsoft — dados de sessão passam pelo relay |
| DNS records | IP Tailscale visível publicamente, mas inacessível fora da rede |

### Backup (fora de escopo desta fase)
O vault Obsidian fica apenas em disco local. Estratégia de backup deve ser definida em spec separada.

---

## Ordem de instalação

1. **Tailscale** — instalar, autenticar, anotar IP 100.x.x.x
2. **DNS GoDaddy** — criar registros A `code` e `obsidian` → IP Tailscale; gerar API Key
3. **Docker Engine** — instalar via script oficial; adicionar lincoln ao grupo docker
4. **Estrutura de diretórios** — criar `workspace/`, `obsidian-vault/`, configurar `.env`
5. **Caddy** — build imagem com plugin godaddy; subir container; validar certificado TLS
6. **Webtop** — subir container; acessar via browser; instalar Obsidian AppImage; configurar vault
7. **code-server** — subir container; validar acesso em `code.redlabsolutions.com.br`
8. **Remote Tunnels** — instalar VS Code CLI; criar unit systemd; autenticar via GitHub; validar no desktop
9. **Hardening SSH** — desabilitar acesso SSH público (porta 22 via IP público)

---

## Critérios de sucesso

- `https://obsidian.redlabsolutions.com.br` abre Webtop com Obsidian funcionando (apenas com Tailscale ativo)
- `https://code.redlabsolutions.com.br` abre code-server com workspace (apenas com Tailscale ativo)
- VS Code desktop consegue conectar via Remote Tunnels
- Certificados TLS válidos (sem warning no browser)
- Portas 80/443 inacessíveis via IP público do VPS
- Vault Obsidian persiste após `docker compose down && docker compose up`
