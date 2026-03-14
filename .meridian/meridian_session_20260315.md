---
name: meridian_session_20260315
description: Full session context — Meridian first deployment, 7 issues filed, audit, PR reviews, cross-team RFC agreement, deployment updated with Sentinel fixes
type: project
---

# Meridian Session — 2026-03-15

## Session Summary

Compass (Diana Reeves) led Team Meridian's first production deployment of SubForge, filed 7 issues, completed a functional audit, negotiated a cross-team collaboration agreement with Team Sentinel, reviewed and approved the implementation, and updated the deployment with all fixes.

## Final Deployment State

| Domain | Status | Image | Theme |
|--------|--------|-------|-------|
| meridian-openlabs.shop | Healthy | subtitle-generator-prod:v2.1.0 | Purple (#863bff) + Inter |
| newui.meridian-openlabs.shop | Healthy | Current main (rebuilt with PR #73/#74 fixes) | Dark navy (#0D1321) + Syne |

Infrastructure: PostgreSQL 16, Redis 7, host nginx (TLS + HSTS), Let's Encrypt (expires 2026-06-12)

Configuration approach: `docker-compose.override.yml` for Meridian-specific customizations (ports, no certs, ENVIRONMENT=dev), `.env` for runtime variables. Upstream `docker-compose.yml` left unmodified.

## Issues Filed & Resolved (all 7 closed)

| Issue | Priority | Resolution |
|-------|----------|------------|
| #67 | P0 | deploy.sh Unicode fix (PR #73) |
| #68 | P1 | newui Docker profile added (PR #73) |
| #69 | P1 | Reverse proxy docs updated (PR #73) |
| #70 | P0 | PROD_IMAGE_TAG support added (PR #73) |
| #71 | P1 | Cookie Secure flag + CORS headers (PR #74), WebSocket route corrected |
| #72 | P2 | Collaborator onboarding added (PR #73) |
| #78 | P2 | Config best practices docs (PR #80) |

## PRs Authored/Reviewed

| PR | Role | Status | Review Rounds |
|----|------|--------|---------------|
| #79 | Author | Merged | 3 rounds (redacted server details per Hawk) |
| #83 | Reviewer | Merged | Full team review (Crane, Gauge, Signal, Compass) |
| #85 | Author | Open | Memory sync backup |

## Cross-Team Agreement (RFC #82 → PR #83, merged)

1. CODEOWNERS — 8 deploy-critical files require Meridian review
2. 48h SLA — Meridian responds within 48h or Sentinel may merge
3. Release notifications — auto-generated deployment checklist issues
4. CI validation — compose config, deploy.sh syntax, PROD_IMAGE_TAG consistency

## Investor Feedback Rules

1. Use .env config files, not CLI flags
2. Delegate tasks to specialists, no bottleneck at leader level
3. Every team member must disclose author identity
4. PR review comments must be visible on GitHub
5. Detailed logging for diagnostics and planning
6. Always back up memory to GitHub

## Known Follow-up Items

- Session cookie `Secure` flag not applied despite PR #74 — may need trusted proxy config in app
- PostgreSQL (5432) and Redis (6379) bound to 0.0.0.0 — should be localhost only
- Future: migrate CODEOWNERS from individual account to org team
