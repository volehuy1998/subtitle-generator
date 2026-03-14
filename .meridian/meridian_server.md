---
name: meridian_server
description: Team Meridian server details — OS, hardware, domains, container layout (sensitive details redacted for public repo)
type: reference
---

# Meridian Server Reference

> **Note:** Sensitive infrastructure details (IP addresses, port bindings, absolute paths) are redacted in this public backup. The unredacted version is maintained in the local `.claude/projects/` memory only, accessible on the deployment server.

## Server

| Attribute | Value |
|-----------|-------|
| Public IP | `<server-ip>` |
| OS | Ubuntu 22.04.5 LTS |
| CPUs | 8 |
| RAM | 15.6 GB |
| Disk | 49 GB (44 GB free at deploy) |
| GPU | None |

## Domains

| Domain | Purpose |
|--------|---------|
| meridian-openlabs.shop | Production (stable v2.1.0 UI) |
| newui.meridian-openlabs.shop | Preview (current main build) |

## TLS Certificates

Both domains use Let's Encrypt certificates, auto-renewed via `certbot.timer`. A renewal hook reloads nginx after each renewal. Certificates expire 2026-06-12.

## Container Layout

| Container | Image | Binding | Profile |
|-----------|-------|---------|---------|
| postgres | postgres:16-alpine | localhost only | (always) |
| redis | redis:7-alpine | localhost only | (always) |
| subtitle-generator | subtitle-generator-prod:v2.1.0 | 127.0.0.1:8000 | cpu |
| subtitle-generator-newui | built from current main | 127.0.0.1:8001 | newui |

## Management Commands

```bash
# Logs
docker compose --profile cpu --profile newui logs -f

# Restart production
docker compose --profile cpu restart

# Restart preview
docker compose --profile newui restart

# Rebuild preview from latest code
git pull && docker compose --profile newui up -d --build

# Test cert renewal
sudo certbot renew --dry-run
```
