---
name: meridian_session_20260315
description: Full session context — Meridian first deployment, issues filed, audit completed, investor feedback received, memory system established
type: project
---

# Meridian Session — 2026-03-15

## Session Summary

Compass (Diana Reeves) led the first production deployment of SubForge for Team Meridian.

## What Happened (chronological)

1. **Restored Sentinel memory** from `.sentinel/` backup to `.claude/projects/` memory
2. **Pulled latest code** — 24 files changed including Router.tsx, post-commit hook, DEPLOY.md expansion
3. **Ran deploy.sh** — crashed at step 5 due to Unicode ellipsis bug (line 277) → filed #67
4. **Manual deployment** — followed deploy.sh steps manually:
   - Installed system packages, Docker 29.3.0, certbot
   - Obtained Let's Encrypt certs for both domains (expire 2026-06-12)
   - Discovered missing newui Docker Compose profile → filed #68
   - Hit ENVIRONMENT=prod redirect loop behind nginx → filed #69, set containers to dev mode
   - Hit cert permission denied in container → removed cert mounts, nginx terminates TLS
   - Both domains showed same new UI → filed #70, built v2.1.0 pinned image
   - Added HSTS at nginx level
5. **Comprehensive functional audit** — tested all 95 API routes via OpenAPI spec
   - Found CLAUDE.md documents wrong `/api/` route prefixes
   - WebSocket `/ws` documented but returns 404
   - Session cookie missing `Secure` flag
   - CORS missing `Access-Control-Allow-Headers`
   - Filed #71 with full audit
6. **Collaborator permission issue** — `gh issue create --label` silently failed, needed to accept collaborator invite → filed #72
7. **Investor feedback received:**
   - Use `.env` config files, not CLI flags → filed #78
   - Delegate tasks to specialists, no bottleneck at leader level
   - All team members must disclose author identity on all content
8. **Memory system established** — created `.meridian/` backup, PR #79 opened

## Issues Filed This Session

| Issue | Title | Priority | Specialist |
|-------|-------|----------|------------|
| #67 | deploy.sh Unicode crash | P0-critical | Dockhand |
| #68 | Missing newui Docker profile | P1-high | Dockhand |
| #69 | ENVIRONMENT=prod redirect loop | P1-high | Crane |
| #70 | PROD_IMAGE_TAG not used | P0-critical | Dockhand |
| #71 | Audit: wrong routes, missing WS, cookie/CORS | P1-high | Signal + Vault |
| #72 | Missing collaborator onboarding | P2-medium | Compass |
| #78 | deploy.sh config best-practice docs | P2-medium | Compass |

## Current Deployment State

- Production: `https://meridian-openlabs.shop` — healthy, v2.1.0 pinned image, old stable UI
- Preview: `https://newui.meridian-openlabs.shop` — healthy, current main build, Enterprise Slate theme
- Infrastructure: PostgreSQL 16 + Redis 7 + host nginx (TLS termination, HSTS)
- All 4 Docker containers healthy

## Open PR

- PR #79: `.meridian/` memory backup (on branch `chore/meridian-memory-backup`)

## Investor Feedback Rules (saved to memory)

1. **Config over CLI** — always use `.env` files, not inline flags
2. **Delegate, no bottleneck** — assign every task to a specialist
3. **Author disclosure** — every team member must identify themselves on all content
4. **PR transparency** — engineer comments must be visible before merging (from Sentinel)
5. **Detailed logging** — investor values thorough logs for diagnostics and planning (from Sentinel)

## Next Steps for Team

- **Gauge** (Tomás): investigate Prometheus metrics integration, log aggregation
- **Rudder** (Kenji): document PostgreSQL fresh setup, Alembic bootstrap, backup
- **Ballast** (Eliot): resource sizing guide, concurrency tuning for 8-CPU/15GB server
- **Dockhand** (Priya): follow up on #67, #68, #70 fixes from Sentinel team
- **Crane** (Marcus): follow up on #69, document nginx proxy best practices
- **Signal** (Fiona) + **Vault** (Anya): follow up on #71, test WebSocket, CORS, cookie fixes
