---
name: project_pending_work
description: Open work items as of 2026-03-15 (end of second session)
type: project
---

As of 2026-03-15 (end of session 2), security work complete, PRs pending CI.

## PRs in flight (queued for auto-merge)

- **PR #86** — 30 CodeQL security fixes (queued, CI running)
- **PR #87** — Automated secret scanning: TruffleHog + custom IP scanner (queued, CI running)

## Production deployment blocker

Before deploying PR #86 to production servers:
- `hash_api_key()` in `auth.py` changed from bare SHA-256 to HMAC-SHA256(JWT_SECRET)
- Any existing API key records in the database will fail validation after this change
- Need a migration script to re-hash existing `api_keys` table entries, OR force-revoke all existing keys and issue new ones
- **Do not deploy PR #86 without addressing this migration**

## Open items

- **PR #81** — release-please 2.3.0 (auto-generated, will auto-merge on next version tag)
- **API key hash migration** — required before prod deploy of PR #86
- **Forge's future note** — CODEOWNERS should migrate from `@volehuy15061998` (individual) to GitHub org team when Meridian grows
- **Distributed system deployment** — 5-server plan (sub-ctrl, sub-api-1/2, sub-data, sub-worker-1) not yet started
- **process_video() refactoring** — 514 lines → step functions, deferred
- **SLOs** — not yet defined
- **mypy/pyright** — not yet in CI
- **Pin TruffleHog action SHA** — Bolt flagged this; `@main` is functional but `@v3.x.x` is more reproducible

## Cross-team automation in place

- CODEOWNERS: 8 deploy-critical files require Meridian co-review (48h SLA)
- release-notify.yml: joint deployment checklist issue on every release
- ci.yml deploy-validate: compose config, bash syntax, PROD_IMAGE_TAG consistency
- secret-scan.yml: TruffleHog + public IP/credential scanner on every PR
- 3 new labels: deployment, sentinel, meridian
