# VPS Dev Machine Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Transformar o VPS Contabo em máquina dev pessoal na nuvem com Obsidian (Webtop) e VS Code (code-server + Remote Tunnels), isolado via Tailscale.

**Architecture:** Tailscale isola o VPS da internet pública. Caddy (bind no IP Tailscale) faz reverse proxy com HTTPS automático via DNS-01/GoDaddy para code-server e Webtop. Remote Tunnels roda como systemd service para acesso via VS Code desktop.

**Tech Stack:** Ubuntu 24.04, Tailscale, Docker Compose, Caddy (caddy-dns/godaddy plugin), linuxserver/code-server, linuxserver/webtop:alpine-xfce, Obsidian AppImage, VS Code CLI, ufw

---

## Pré-requisitos (manual, fora do VPS)

Antes de começar, tenha em mãos:
- Acesso SSH ao VPS como `lincoln` (ou `root` para sudo)
- Acesso à conta GoDaddy: [developer.godaddy.com](https://developer.godaddy.com) → API Keys → Create New Key (tipo: Production)
- Conta GitHub (para autenticar o Remote Tunnels)
- Tailscale account em [login.tailscale.com](https://login.tailscale.com)

---

## Task 1: Tailscale

**Files:**
- `/etc/systemd/system/` (modificado pelo instalador)
- `/etc/tailscale/` (criado pelo instalador)

- [ ] **Step 1: Instalar Tailscale**

```bash
curl -fsSL https://tailscale.com/install.sh | sh
```

- [ ] **Step 2: Verificar instalação**

```bash
tailscale version
```
Esperado: versão impressa (ex: `1.80.x`)

- [ ] **Step 3: Autenticar no Tailscale**

```bash
sudo tailscale up
```
Abrirá URL no terminal. Abra no browser, faça login e autorize o dispositivo.

- [ ] **Step 4: Verificar IP Tailscale**

```bash
tailscale ip -4
```
Esperado: IP no formato `100.x.x.x`. **Anote este IP** — será usado em todos os passos seguintes.

- [ ] **Step 5: Verificar status**

```bash
tailscale status
```
Esperado: linha `contabo-dev` (ou hostname) com status `idle` ou `active`

- [ ] **Step 6: Commit**

```bash
cd /home/lincoln/vps-setup
echo "# VPS Dev Machine" > README.md
git add README.md
git commit -m "chore: tailscale instalado e autenticado"
```

---

## Task 2: DNS no GoDaddy

**Ação manual no painel GoDaddy** (sem arquivos de código)

- [ ] **Step 1: Gerar API Key GoDaddy**

  Acesse [developer.godaddy.com/keys](https://developer.godaddy.com/keys):
  - Clique em "Create New API Key"
  - Environment: **Production**
  - Anote `API Key` e `API Secret`

- [ ] **Step 2: Criar registro DNS `code`**

  No painel DNS do `redlabsolutions.com.br`:
  - Tipo: **A**
  - Nome: `code`
  - Valor: IP Tailscale anotado no Task 1 (100.x.x.x)
  - TTL: 600

- [ ] **Step 3: Criar registro DNS `obsidian`**

  - Tipo: **A**
  - Nome: `obsidian`
  - Valor: mesmo IP Tailscale
  - TTL: 600

- [ ] **Step 4: Verificar propagação DNS**

  Aguarde ~2 minutos, então execute (da sua máquina local com Tailscale ativo):
  ```bash
  dig code.redlabsolutions.com.br +short
  dig obsidian.redlabsolutions.com.br +short
  ```
  Esperado: ambos retornam o IP Tailscale `100.x.x.x`

---

## Task 3: Docker Engine

**Files:**
- `/etc/docker/daemon.json` (criado)
- `/home/lincoln/` (usuário adicionado ao grupo docker)

- [ ] **Step 1: Instalar Docker via script oficial**

```bash
curl -fsSL https://get.docker.com | sh
```

- [ ] **Step 2: Adicionar lincoln ao grupo docker**

```bash
sudo usermod -aG docker lincoln
```

- [ ] **Step 3: Verificar Docker**

Saia e reconecte ao SSH (para aplicar grupo), então:
```bash
docker --version
docker compose version
```
Esperado:
```
Docker version 27.x.x, build ...
Docker Compose version v2.x.x
```

- [ ] **Step 4: Testar sem sudo**

```bash
docker run --rm hello-world
```
Esperado: mensagem `Hello from Docker!`

- [ ] **Step 5: Commit**

```bash
cd /home/lincoln/vps-setup
git commit --allow-empty -m "chore: docker engine instalado"
```

---

## Task 4: Estrutura de arquivos e .env

**Files:**
- Create: `/home/lincoln/workspace/` (diretório)
- Create: `/home/lincoln/obsidian-vault/` (diretório)
- Create: `/home/lincoln/vps-setup/.env`
- Create: `/home/lincoln/vps-setup/.env.example`
- Create: `/home/lincoln/vps-setup/.gitignore`

- [ ] **Step 1: Criar diretórios de dados**

```bash
mkdir -p /home/lincoln/workspace
mkdir -p /home/lincoln/obsidian-vault
```

- [ ] **Step 2: Criar .gitignore**

```bash
cat > /home/lincoln/vps-setup/.gitignore << 'EOF'
.env
*.crt
*.key
caddy_data/
EOF
```

- [ ] **Step 3: Criar .env.example**

```bash
cat > /home/lincoln/vps-setup/.env.example << 'EOF'
# IP Tailscale do VPS (ex: 100.64.0.1)
TAILSCALE_IP=100.x.x.x

# GoDaddy API (https://developer.godaddy.com/keys)
GODADDY_API_KEY=your_key_here
GODADDY_API_SECRET=your_secret_here

# Senhas de acesso aos serviços
CODESERVER_PASSWORD=change_me_strong_password
WEBTOP_PASSWORD=change_me_strong_password

# UID/GID do usuário lincoln
PUID=1000
PGID=1000
EOF
```

- [ ] **Step 4: Criar .env com valores reais**

```bash
cp /home/lincoln/vps-setup/.env.example /home/lincoln/vps-setup/.env
nano /home/lincoln/vps-setup/.env
```
Preencha `TAILSCALE_IP`, `GODADDY_API_KEY`, `GODADDY_API_SECRET`, `CODESERVER_PASSWORD`, `WEBTOP_PASSWORD`.

Verifique o PUID/PGID correto de lincoln:
```bash
id lincoln
```
Anote uid e gid e ajuste no `.env` se necessário.

- [ ] **Step 5: Verificar que .env não está no git**

```bash
cd /home/lincoln/vps-setup
git status
```
Esperado: `.env` aparece em "Untracked files" ou não aparece (não deve aparecer em "Changes")

- [ ] **Step 6: Commit**

```bash
git add .gitignore .env.example
git commit -m "chore: estrutura de arquivos e env template"
```

---

## Task 5: Caddy (imagem customizada + Caddyfile)

**Files:**
- Create: `/home/lincoln/vps-setup/Dockerfile.caddy`
- Create: `/home/lincoln/vps-setup/Caddyfile`

- [ ] **Step 1: Criar Dockerfile.caddy**

```dockerfile
# /home/lincoln/vps-setup/Dockerfile.caddy
FROM caddy:builder AS builder
RUN xcaddy build \
    --with github.com/caddy-dns/godaddy

FROM caddy:latest
COPY --from=builder /usr/bin/caddy /usr/bin/caddy
```

- [ ] **Step 2: Criar Caddyfile**

O Caddyfile usa `{env.TAILSCALE_IP}` — o valor vem automaticamente do `.env` via Docker Compose. Não é necessária substituição manual.

```caddyfile
# /home/lincoln/vps-setup/Caddyfile
{
    email lincoln@redlabsolutions.com.br
    acme_dns godaddy {
        api_key {env.GODADDY_API_KEY}
        api_secret {env.GODADDY_API_SECRET}
    }
}

code.redlabsolutions.com.br {
    bind {env.TAILSCALE_IP}
    reverse_proxy code-server:8443 {
        transport http {
            tls_insecure_skip_verify
        }
    }
}

obsidian.redlabsolutions.com.br {
    bind {env.TAILSCALE_IP}
    reverse_proxy webtop:3000
}
```

- [ ] **Step 3: Verificar Dockerfile.caddy**

```bash
cat /home/lincoln/vps-setup/Dockerfile.caddy
```
Esperado: FROM caddy:builder com xcaddy build.

- [ ] **Step 4: Commit**

```bash
cd /home/lincoln/vps-setup
git add Dockerfile.caddy Caddyfile
git commit -m "feat: caddy dockerfile e caddyfile com godaddy dns"
```

---

## Task 6: Docker Compose

**Files:**
- Create: `/home/lincoln/vps-setup/docker-compose.yml`

- [ ] **Step 1: Criar docker-compose.yml**

```yaml
# /home/lincoln/vps-setup/docker-compose.yml
services:
  caddy:
    build:
      context: .
      dockerfile: Dockerfile.caddy
    container_name: caddy
    restart: unless-stopped
    ports:
      - "${TAILSCALE_IP}:80:80"
      - "${TAILSCALE_IP}:443:443"
      - "${TAILSCALE_IP}:443:443/udp"
    volumes:
      - ./Caddyfile:/etc/caddy/Caddyfile:ro
      - caddy_data:/data
      - caddy_config:/config
    environment:
      - GODADDY_API_KEY=${GODADDY_API_KEY}
      - GODADDY_API_SECRET=${GODADDY_API_SECRET}
      - TAILSCALE_IP=${TAILSCALE_IP}
    networks:
      - proxy

  code-server:
    image: lscr.io/linuxserver/code-server:latest
    container_name: code-server
    restart: unless-stopped
    environment:
      - PUID=${PUID}
      - PGID=${PGID}
      - TZ=America/Sao_Paulo
      - PASSWORD=${CODESERVER_PASSWORD}
      - HASHED_PASSWORD=
      - SUDO_PASSWORD=
    volumes:
      - /home/lincoln/workspace:/config/workspace
      - codeserver_config:/config
    networks:
      - proxy

  webtop:
    image: lscr.io/linuxserver/webtop:alpine-xfce
    container_name: webtop
    restart: unless-stopped
    security_opt:
      - seccomp:unconfined
    environment:
      - PUID=${PUID}
      - PGID=${PGID}
      - TZ=America/Sao_Paulo
      - PASSWORD=${WEBTOP_PASSWORD}
    volumes:
      - /home/lincoln/obsidian-vault:/config/obsidian-vault
      - webtop_config:/config
    shm_size: "1gb"
    networks:
      - proxy

volumes:
  caddy_data:
  caddy_config:
  codeserver_config:
  webtop_config:

networks:
  proxy:
    driver: bridge
```

- [ ] **Step 2: Validar sintaxe do compose**

```bash
cd /home/lincoln/vps-setup
docker compose config
```
Esperado: configuração expandida impressa sem erros.

- [ ] **Step 3: Build da imagem Caddy**

```bash
docker compose build caddy
```
Esperado: build termina com `Successfully built ...`

- [ ] **Step 4: Commit**

```bash
git add docker-compose.yml
git commit -m "feat: docker-compose com code-server, webtop e caddy"
```

---

## Task 7: Subir containers e validar Caddy/TLS

- [ ] **Step 1: Subir todos os containers**

```bash
cd /home/lincoln/vps-setup
docker compose up -d
```
Esperado: `[+] Running 3/3` — caddy, code-server, webtop criados.

- [ ] **Step 2: Verificar containers em execução**

```bash
docker compose ps
```
Esperado: todos com status `running`.

- [ ] **Step 3: Acompanhar logs do Caddy (aguardar certificado)**

```bash
docker compose logs -f caddy
```
Aguardar linhas como:
```
certificate obtained successfully
```
Pode levar 1-2 minutos (DNS-01 challenge). Ctrl+C para sair dos logs.

- [ ] **Step 4: Verificar certificado TLS do code-server**

Da sua máquina local (com Tailscale ativo):
```bash
curl -I https://code.redlabsolutions.com.br
```
Esperado: `HTTP/2 200` ou redirect, sem erros de certificado.

- [ ] **Step 5: Verificar certificado TLS do webtop**

```bash
curl -I https://obsidian.redlabsolutions.com.br
```
Esperado: `HTTP/2 200`, sem erros de certificado.

- [ ] **Step 6: Acessar code-server no browser**

Abra `https://code.redlabsolutions.com.br` com Tailscale ativo.
Esperado: tela de login do code-server. Digite a senha do `.env`.

- [ ] **Step 7: Commit**

```bash
cd /home/lincoln/vps-setup
git commit --allow-empty -m "feat: containers em execução, TLS validado"
```

---

## Task 8: Instalar Obsidian no Webtop (manual e interativo)

**Atenção:** Este é um passo manual dentro do browser. Não é automatizável.

- [ ] **Step 1: Acessar Webtop no browser**

Abra `https://obsidian.redlabsolutions.com.br` com Tailscale ativo.
Digite a senha do `.env`. Você verá o desktop Alpine XFCE.

- [ ] **Step 2: Abrir terminal dentro do Webtop**

Clique com botão direito no desktop → Terminal Emulator (ou ícone no painel).

- [ ] **Step 3: Baixar Obsidian AppImage**

Dentro do terminal do Webtop:
```bash
cd /config
wget -O Obsidian.AppImage "https://github.com/obsidianmd/obsidian-releases/releases/latest/download/Obsidian-$(curl -s https://api.github.com/repos/obsidianmd/obsidian-releases/releases/latest | grep -oP '"tag_name": "v\K[^"]+').AppImage"
chmod +x Obsidian.AppImage
```

- [ ] **Step 4: Criar atalho na área de trabalho**

Dentro do Webtop:
```bash
cat > /config/Desktop/obsidian.desktop << 'EOF'
[Desktop Entry]
Name=Obsidian
Exec=/config/Obsidian.AppImage --no-sandbox
Icon=obsidian
Type=Application
Categories=Office;
EOF
chmod +x /config/Desktop/obsidian.desktop
```

- [ ] **Step 5: Abrir Obsidian**

Dê duplo clique no ícone do Obsidian no desktop do Webtop.
Na tela inicial, selecione "Open folder as vault" → navegar para `/config/obsidian-vault`.

- [ ] **Step 6: Verificar persistência do vault**

No terminal do VPS (fora do Webtop):
```bash
ls /home/lincoln/obsidian-vault/
```
Após criar uma nota no Obsidian, o arquivo `.md` deve aparecer aqui.

---

## Task 9: VS Code Remote Tunnels (systemd)

**Files:**
- Create: `/home/lincoln/vps-setup/systemd/code-tunnel.service` (no repo — fonte da verdade)
- Copy to: `/home/lincoln/.config/systemd/user/code-tunnel.service` (destino systemd)

- [ ] **Step 1: Instalar VS Code CLI**

```bash
curl -fsSL "https://code.visualstudio.com/sha/download?build=stable&os=cli-linux-x64" -o /tmp/vscode-cli.tar.gz
tar -xzf /tmp/vscode-cli.tar.gz -C /usr/local/bin/
code --version
```
Esperado: versão impressa.

- [ ] **Step 2: Autenticar o tunnel (manual — requer browser)**

```bash
code tunnel --accept-server-license-terms --name contabo-dev
```
Na primeira execução: imprime uma URL para autenticação via GitHub. Abra no browser, autorize.

Após autorizar, o processo fica rodando (tunnel ativo). Pressione Ctrl+C para parar — a autenticação fica salva.

> **Nota:** Se o nome `contabo-dev` já existir na sua conta GitHub, acesse [github.com/settings/codespaces](https://github.com/settings/codespaces) → "Remote Tunnels" e remova o tunnel anterior antes deste passo.

- [ ] **Step 3: Criar unit systemd do usuário (salvo no repo e copiado)**

```bash
mkdir -p /home/lincoln/vps-setup/systemd
mkdir -p /home/lincoln/.config/systemd/user
cat > /home/lincoln/vps-setup/systemd/code-tunnel.service << 'EOF'
[Unit]
Description=VS Code Remote Tunnel
After=network-online.target
Wants=network-online.target

[Service]
Type=simple
ExecStart=/usr/local/bin/code tunnel --accept-server-license-terms --name contabo-dev
Restart=on-failure
RestartSec=5

[Install]
WantedBy=default.target
EOF
cp /home/lincoln/vps-setup/systemd/code-tunnel.service /home/lincoln/.config/systemd/user/code-tunnel.service
```

- [ ] **Step 4: Habilitar e iniciar o serviço**

```bash
systemctl --user daemon-reload
systemctl --user enable code-tunnel.service
systemctl --user start code-tunnel.service
```

Para o serviço sobreviver ao logout SSH:
```bash
sudo loginctl enable-linger lincoln
```

- [ ] **Step 5: Verificar status do serviço**

```bash
systemctl --user status code-tunnel.service
```
Esperado: `Active: active (running)`

- [ ] **Step 6: Testar no VS Code desktop**

No VS Code desktop da sua máquina local:
- Instale a extensão "Remote - Tunnels" (se não tiver)
- Ctrl+Shift+P → "Remote Tunnels: Connect to Tunnel"
- Selecione `contabo-dev`

Esperado: nova janela do VS Code conectada ao VPS, com `/home/lincoln/workspace` disponível.

- [ ] **Step 7: Commit**

```bash
cd /home/lincoln/vps-setup
git add systemd/code-tunnel.service
git commit -m "feat: remote tunnels configurado como serviço systemd"
```

---

## Task 10: Hardening — Firewall e SSH

**Atenção:** Execute este task SOMENTE após confirmar que consegue acessar o VPS via Tailscale IP (SSH e serviços funcionando).

- [ ] **Step 1: Verificar acesso SSH via Tailscale (pré-condição)**

Da sua máquina local:
```bash
ssh lincoln@$(tailscale ip -4)
```
Esperado: login bem-sucedido via IP Tailscale. Se falhar, **NÃO prossiga** com os próximos passos.

- [ ] **Step 2: Instalar e configurar ufw**

```bash
sudo apt install -y ufw
sudo ufw default deny incoming
sudo ufw default allow outgoing
```

- [ ] **Step 3: Permitir SSH apenas via Tailscale**

> **CRÍTICO — ordem importa:** Este passo DEVE ser executado ANTES do `ufw enable` (Step 5). Se inverter a ordem, o SSH via Tailscale ficará bloqueado e você perderá acesso ao VPS.
> **Rollback de emergência:** Se ficar bloqueado, use o console VNC/KVM do painel Contabo para acessar o VPS e executar `sudo ufw disable`.

```bash
sudo ufw allow in on tailscale0 to any port 22
```

- [ ] **Step 4: Bloquear portas públicas**

```bash
sudo ufw deny 22/tcp
sudo ufw deny 80/tcp
sudo ufw deny 443/tcp
```

- [ ] **Step 5: Habilitar firewall**

```bash
sudo ufw --force enable
sudo ufw status verbose
```
Esperado:
```
22/tcp    DENY IN     Anywhere
80/tcp    DENY IN     Anywhere
443/tcp   DENY IN     Anywhere
22 on tailscale0  ALLOW IN    Anywhere
```

- [ ] **Step 6: Verificar que SSH público foi bloqueado**

De uma máquina SEM Tailscale (ou desative Tailscale temporariamente):
```bash
timeout 5 ssh lincoln@<IP_PUBLICO_DO_VPS> 2>&1 || echo "Conexão recusada/timeout — correto"
```
Esperado: timeout ou connection refused.

- [ ] **Step 7: Verificar que SSH Tailscale ainda funciona**

Com Tailscale ativo:
```bash
ssh lincoln@$(tailscale ip -4) echo "SSH via Tailscale OK"
```
Esperado: `SSH via Tailscale OK`

- [ ] **Step 8: Commit final**

```bash
cd /home/lincoln/vps-setup
git commit --allow-empty -m "feat: hardening completo — ufw + ssh via tailscale only"
```

---

## Verificação Final

Todos os critérios de sucesso da spec devem ser atendidos:

- [ ] `https://obsidian.redlabsolutions.com.br` abre Webtop com Obsidian (Tailscale ativo)
- [ ] `https://code.redlabsolutions.com.br` abre code-server com workspace (Tailscale ativo)
- [ ] VS Code desktop conecta via Remote Tunnels (`contabo-dev`)
- [ ] Certificados TLS válidos (sem warning no browser)
- [ ] `curl https://code.redlabsolutions.com.br` falha sem Tailscale
- [ ] Vault persiste: `docker compose down && docker compose up -d` → Obsidian ainda tem as notas

```bash
# Teste de persistência do vault
cd /home/lincoln/vps-setup
docker compose down
docker compose up -d
# Aguardar containers subirem (~15s)
ls /home/lincoln/obsidian-vault/
# Esperado: arquivos de notas ainda presentes
```
