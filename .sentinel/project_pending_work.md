---
name: project_pending_work
description: Open work items as of 2026-03-15 (end of third session)
type: project
---

As of 2026-03-15 (end of session 3), both security PRs are merged to main. CI fully green.

## Completed this session (2026-03-15 session 3)

- **PR #86 MERGED** — 30 CodeQL security fixes across 8 vulnerability categories
  - Last batch: export.py path injection, validation.py script regex, test_sprint11.py CSP assertions
- **PR #87 MERGED** — Automated sensitive data scanning (TruffleHog + custom 16-pattern scanner)

## Production deployment blocker

Before deploying to production servers:
- `hash_api_key()` in `auth.py` changed from bare SHA-256 to HMAC-SHA256(JWT_SECRET)
- Any existing API key records in the database will fail validation after this change
- Need a migration script to re-hash existing `api_keys` table entries, OR force-revoke all existing keys and issue new ones
- **Do not deploy without addressing this migration**

## Open items

- **PR #81** — release-please 2.3.0 (auto-generated, will auto-merge on next version tag)
- **API key hash migration** — required before prod deploy
- **Forge's future note** — CODEOWNERS should migrate from `@volehuy15061998` (individual) to GitHub org team when Meridian grows
- **Pin TruffleHog action SHA** — `@main` is functional but `@v3.x.x` is more reproducible
- **Distributed system deployment** — 5-server plan (sub-ctrl, sub-api-1/2, sub-data, sub-worker-1) not yet started
- **process_video() refactoring** — 514 lines → step functions, deferred
- **SLOs** — not yet defined
- **mypy/pyright** — not yet in CI

## Security infrastructure now fully in place

- CODEOWNERS: 8 deploy-critical files require Meridian co-review (48h SLA)
- release-notify.yml: joint deployment checklist issue on every release
- ci.yml deploy-validate: compose config, bash syntax, PROD_IMAGE_TAG consistency
- secret-scan.yml: TruffleHog + public IP/credential scanner on every PR
- 30 CodeQL alerts resolved across: path-injection, stack-trace-exposure, weak-hashing, XSS, bad-tag-filter, insecure-protocol, missing-workflow-permissions, incomplete-url-sanitization
- 3 new labels: deployment, sentinel, meridian
