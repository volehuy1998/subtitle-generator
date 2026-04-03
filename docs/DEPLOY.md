# Deployment Guide

## Environments

| Environment | Domain | Docker Profile | Branch Source |
|-------------|--------|---------------|---------------|
| Production | openlabs.club | `cpu` | `PROD_BRANCH` (currently `prod-editorial-nav`) |
| Staging | newui.openlabs.club | `newui` | `NEWUI_BRANCH` (set in `.env`) |

Both run on the same server. Nginx reverse proxies each domain to its container.

## Docker Deployment (Recommended)

### Quick Start

```bash
cp .env.example .env          # configure environment
./scripts/deploy-profile.sh cpu      # production
./scripts/deploy-profile.sh newui    # staging
```

### deploy-profile.sh

Handles branch checkout, Docker build, health verification, and restore.

```bash
# Production from PROD_BRANCH
./scripts/deploy-profile.sh cpu

# Production with git tag for rollback auditing
./scripts/deploy-profile.sh cpu --tag

# Staging from NEWUI_BRANCH
./scripts/deploy-profile.sh newui

# Staging from a specific branch
./scripts/deploy-profile.sh newui feat/my-feature

# GPU mode (manual)
docker compose --profile gpu up --build -d
```

### Container Layout

| Container | Profile | Port | Domain |
|-----------|---------|------|--------|
| subtitle-generator | cpu | 8000 | openlabs.club |
| subtitle-newui | newui | 8001 | newui.openlabs.club |

### Health Check

```bash
curl -s http://127.0.0.1:8000/health
curl -s http://127.0.0.1:8001/health
```

## Bare-Metal Deployment

### One-Command Install

```bash
# Development (HTTP only)
sudo bash scripts/deploy.sh --mode dev

# Production (HTTPS via Let's Encrypt)
sudo bash scripts/deploy.sh --domain example.com --email admin@example.com

# Production with Docker
sudo bash scripts/deploy.sh --domain example.com --email admin@example.com --docker
```

### Requirements

- Ubuntu 22.04 or 24.04 LTS
- Root / sudo access
- Public IP + DNS pointing to server (production)
- Ports 80 and 443 open (production)

The script installs Python 3, ffmpeg, git, certbot, and Docker as needed.

### Systemd Management (bare-metal)

```bash
sudo journalctl -u subforge -f        # live logs
sudo systemctl restart subforge       # restart
sudo systemctl status subforge        # status
```

## Nginx + TLS

### TLS Certificates

**Let's Encrypt** (recommended):
```bash
sudo bash scripts/deploy.sh --domain example.com --email admin@example.com
```
Auto-renewal via `certbot.timer`. Test with: `sudo certbot renew --dry-run`

**Bring your own**:
```bash
sudo bash scripts/deploy.sh --domain example.com \
  --cert /etc/ssl/certs/fullchain.pem \
  --key /etc/ssl/private/privkey.pem
```

### Nginx Config (two-domain setup)

```nginx
server {
    listen 443 ssl;
    server_name openlabs.club;
    ssl_certificate /etc/letsencrypt/live/openlabs.club/fullchain.pem;
    ssl_certificate_key /etc/letsencrypt/live/openlabs.club/privkey.pem;
    location / { proxy_pass http://127.0.0.1:8000; }
}

server {
    listen 443 ssl;
    server_name newui.openlabs.club;
    ssl_certificate /etc/letsencrypt/live/openlabs.club/fullchain.pem;
    ssl_certificate_key /etc/letsencrypt/live/openlabs.club/privkey.pem;
    location / { proxy_pass http://127.0.0.1:8001; }
}
```

For SSE/WebSocket, add to each `location` block:
```nginx
proxy_set_header Connection '';
proxy_http_version 1.1;
proxy_buffering off;
proxy_cache off;
chunked_transfer_encoding off;
```

## Environment Variables

All configuration goes in `.env` (not CLI flags). See [`.env.example`](../.env.example) for the full list.

**Critical variables**:

| Variable | Purpose |
|----------|---------|
| `ENVIRONMENT` | `dev` (HTTP) or `prod` (HTTPS + HSTS) |
| `DATABASE_URL` | PostgreSQL connection string |
| `API_KEYS` | Comma-separated API keys (secret) |
| `PRELOAD_MODEL` | Whisper model to warm-start (`large` recommended for prod) |
| `REDIS_URL` | Redis for pub/sub, rate limiting |
| `PROD_BRANCH` | Branch for production Docker build |
| `NEWUI_BRANCH` | Branch for staging Docker build |

**Never**: hardcode secrets in `docker-compose.yml`, pass secrets as CLI flags, or commit `.env`.

## GPU Support

```bash
# Bare-metal
sudo bash scripts/deploy.sh --domain example.com --email admin@example.com --gpu

# Docker
docker compose --profile gpu up --build -d
```

Bare-metal installs `nvidia-driver-550` + CUDA toolkit. Docker installs NVIDIA Container Toolkit. A reboot may be required after bare-metal driver install.

## Deployment Workflow

1. Develop on feature branch
2. Set `NEWUI_BRANCH=feat/my-feature` in `.env`
3. Deploy to staging: `./scripts/deploy-profile.sh newui`
4. Verify: `curl -s http://127.0.0.1:8001/health`
5. Get investor approval on `newui.openlabs.club`
6. Merge to `main`, update `PROD_BRANCH`
7. Deploy to production: `./scripts/deploy-profile.sh cpu --tag`

**Never deploy to production without approval on staging first.**

## Fail2ban (Optional)

```bash
sudo apt-get install -y fail2ban
sudo cp scripts/fail2ban/filter.d/subtitle-generator.conf /etc/fail2ban/filter.d/
sudo cp scripts/fail2ban/jail.d/subtitle-generator.conf /etc/fail2ban/jail.d/
sudo systemctl enable --now fail2ban
```

## Post-Deployment URLs

| URL | Purpose |
|-----|---------|
| `https://example.com` | Application |
| `https://example.com/docs` | Swagger API docs |
| `https://example.com/status` | Public status page |
| `https://example.com/health` | Health check (JSON) |
