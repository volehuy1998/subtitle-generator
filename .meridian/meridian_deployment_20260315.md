---
name: meridian_deployment_20260315
description: Team Meridian first production deployment session — meridian-openlabs.shop + newui subdomain, issues filed, workarounds applied
type: project
---

# Meridian Deployment Session — 2026-03-15

## Deployment Summary

Deployed SubForge to production with two-domain setup:

| Domain | Container | Image | Port | Purpose |
|--------|-----------|-------|------|---------|
| meridian-openlabs.shop | subtitle-generator (cpu) | `subtitle-generator-prod:v2.1.0` (pinned) | 127.0.0.1:8000 | Production — old stable UI |
| newui.meridian-openlabs.shop | subtitle-generator-newui | Current main build | 127.0.0.1:8001 | Preview — new Enterprise Slate theme |

**Infrastructure:** PostgreSQL 16, Redis 7, host nginx (TLS termination + reverse proxy), Let's Encrypt certs (expire 2026-06-12)

## Workarounds Applied

1. **deploy.sh Unicode bug** → manual deployment following script steps
2. **Missing newui profile** → added newui service to docker-compose.yml manually
3. **ENVIRONMENT=prod redirect loop** → set containers to ENVIRONMENT=dev, nginx handles TLS
4. **Cert permission denied** → removed cert volume mounts, nginx terminates TLS
5. **Both domains showed same UI** → built v2.1.0 Docker image, pinned cpu profile to it
6. **No HSTS** → added HSTS header at nginx level
7. **Directory permissions** → chmod 777 on uploads/outputs/logs

## Issues Filed

| Issue | Severity | Assigned To | Status |
|-------|----------|-------------|--------|
| #67 | P0-critical | — | deploy.sh Unicode crash |
| #68 | P1-high | — | Missing newui Docker profile |
| #69 | P1-high | — | ENVIRONMENT=prod redirect loop behind proxy |
| #70 | P0-critical | — | PROD_IMAGE_TAG not used in docker-compose |
| #71 | P1-high | — | CLAUDE.md wrong API routes, missing WebSocket, cookie/CORS gaps |
| #72 | P2-medium | — | Missing collaborator onboarding docs |
| #78 | P2-medium | — | deploy.sh lacks config file best-practice guidance |

## Key Learnings

- deploy.sh only accepts CLI flags, no config file support
- .env file is for Docker Compose runtime, not for deploy.sh options
- When running behind nginx proxy, app must be ENVIRONMENT=dev (nginx handles TLS/HSTS)
- cpu profile must use pinned image tag, NOT build from source, to preserve stable UI
- GitHub `gh issue create --label` silently fails without collaborator permissions
