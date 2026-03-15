---
name: project_pending_work
description: Open work items as of 2026-03-15 (end of session 5) — all PRs cleared, Meridian removed, remaining backlog
type: project
---

**Why:** Tracking open items so future sessions continue from the right state without re-discovering completed work.

**How to apply:** Check this list at the start of each session to understand what's in flight.

## All PRs cleared (session 5)

- **0 open PRs**
- **v2.3.0 released**
- All Meridian references removed from repo, labels, issues, PRs, releases, branches

## Production deployment blocker

`hash_api_key()` in `app/services/auth.py` changed from bare SHA-256 to HMAC-SHA256(JWT_SECRET). Any existing API key records in the `api_keys` DB table will fail validation after deploy. Needs migration script or force-revoke before deploying to production.

## Remaining backlog

- **Distributed system deployment** — 5-server plan (sub-ctrl, sub-api-1/2, sub-data, sub-worker-1) not yet started
- **API key hash migration** — required before prod deploy of PR #86
- **Pin TruffleHog action SHA** — `@main` works but `@v3.x.x` more reproducible
- **process_video() refactoring** — 514 lines → step functions, deferred
- **SLOs** — not yet defined
- **mypy/pyright** — not yet in CI
- **PR #86 CodeQL residual annotations** — 7 remaining annotations (export.py path injection, validation.py script regex, test_sprint11.py startswith assertions) — not blocking merge but should be addressed

## CI infrastructure in place

- ci.yml: Lint + Test + Build (required checks: Lint, Test)
- codeql.yml: CodeQL analysis (actions, JS/TS, Python)
- secret-scan.yml: TruffleHog + 16-pattern custom scanner
- pr-attributes.yml: 6-attribute PR validation
- memory-backup.yml: .sentinel/ backup integrity + diff-only sensitive data scan
- deploy-validate: compose config, bash syntax, PROD_IMAGE_TAG
- release-notify.yml: deployment checklist on release (Sentinel only)
- CODEOWNERS: Sentinel-only review for all files including deploy-critical
