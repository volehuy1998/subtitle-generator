---
name: meridian_server
description: Team Meridian server details — IP, OS, hardware, domains, container layout, nginx config paths
type: reference
---

# Meridian Server Reference

## Server

| Attribute | Value |
|-----------|-------|
| Public IP | 124.197.31.140 |
| OS | Ubuntu 22.04.5 LTS |
| CPUs | 8 |
| RAM | 15.6 GB |
| Disk | 49 GB (44 GB free at deploy) |
| GPU | None |

## Domains

| Domain | DNS | Purpose |
|--------|-----|---------|
| meridian-openlabs.shop | A → 124.197.31.140 | Production (stable v2.1.0 UI) |
| newui.meridian-openlabs.shop | A → 124.197.31.140 | Preview (current main build) |

## TLS Certificates

| Domain | Path | Expires |
|--------|------|---------|
| meridian-openlabs.shop | /etc/letsencrypt/live/meridian-openlabs.shop/ | 2026-06-12 |
| newui.meridian-openlabs.shop | /etc/letsencrypt/live/newui.meridian-openlabs.shop/ | 2026-06-12 |

Auto-renewal via certbot.timer. Renewal hook at `/etc/letsencrypt/renewal-hooks/deploy/subforge-reload.sh` reloads nginx.

## Key Paths

| Path | Purpose |
|------|---------|
| /opt/subtitle-generator/ | Deployment install directory |
| /opt/subtitle-generator/.env | Docker Compose environment config |
| /opt/subtitle-generator/docker-compose.yml | Container orchestration (modified for two-domain setup) |
| /etc/nginx/sites-available/subforge | nginx reverse proxy config |
| /root/subtitle-generator/ | Source repo clone (for building images) |

## Container Layout

| Container | Image | Ports | Profile |
|-----------|-------|-------|---------|
| postgres | postgres:16-alpine | 0.0.0.0:5432 | (always) |
| redis | redis:7-alpine | 0.0.0.0:6379 | (always) |
| subtitle-generator | subtitle-generator-prod:v2.1.0 | 127.0.0.1:8000 | cpu |
| subtitle-generator-newui | built from current main | 127.0.0.1:8001 | newui |

## Management Commands

```bash
# Logs
docker compose -f /opt/subtitle-generator/docker-compose.yml --profile cpu --profile newui logs -f

# Restart production
docker compose -f /opt/subtitle-generator/docker-compose.yml --profile cpu restart

# Restart preview
docker compose -f /opt/subtitle-generator/docker-compose.yml --profile newui restart

# Rebuild preview from latest code
cd /opt/subtitle-generator && git pull && docker compose --profile newui up -d --build

# Test cert renewal
sudo certbot renew --dry-run
```
