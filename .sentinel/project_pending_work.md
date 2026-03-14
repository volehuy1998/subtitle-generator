---
name: project_pending_work
description: Open work items as of 2026-03-15
type: project
---

As of 2026-03-15, all open PRs resolved. CI fully green.

## Completed this session (2026-03-15)

- **PR #80 MERGED** — Quill's Configuration Best Practices in DEPLOY.md (resolves #78)
- **PR #83 MERGED** — Cross-team automation (CODEOWNERS + release-notify.yml + deploy-validate CI + CONTRIBUTING.md §10). Reviewed and approved by both Sentinel and Meridian teams.
- **PR #79 MERGED** — Team Meridian .meridian/ memory backup. Three rounds of security review; public IP redacted from MEMORY.md index before merge.
- **Issue #82 CLOSED** — RFC resolved by PR #83

## Open items

- **PR #81** — release-please 2.3.0 (auto-generated after PR #83 feat merged). Will auto-merge when enough features land. No action needed.
- **Forge's future note** — CODEOWNERS should migrate from `@volehuy15061998` (individual) to GitHub org team when Meridian grows
- **Distributed system deployment** — 5-server plan (sub-ctrl, sub-api-1/2, sub-data, sub-worker-1) not yet started
- **process_video() refactoring** — 514 lines → step functions, deferred
- **SLOs** — not yet defined
- **mypy/pyright** — not yet in CI

## Cross-team automation now in place

- CODEOWNERS: 8 deploy-critical files require Meridian co-review (48h SLA)
- release-notify.yml: joint deployment checklist issue on every release
- ci.yml deploy-validate: compose config, bash syntax, PROD_IMAGE_TAG consistency
- 3 new labels: deployment, sentinel, meridian
</content>
