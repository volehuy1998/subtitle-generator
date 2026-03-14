---
name: project_pending_work
description: Open work items as of 2026-03-15
type: project
---

As of 2026-03-15, CI is fully green. All known ESLint errors resolved.

## Recently completed (2026-03-15)

- **release-please automation** — PR #63 merged
- **ESLint mask removed** — PR #65 merged: removed `|| true` from CI, fixed all 5 hidden ESLint errors
- **Team Meridian issues #67–#72** — all resolved and merged (PRs #68–#74)
- **release-please / v2.2.0** — PR #64 merged; Docker image published; PR #76 merged (.env.example PROD_IMAGE_TAG bump)
- **PR #80 merged** — Quill's Configuration Best Practices section in DEPLOY.md (resolves Issue #78)
- **RFC #82 + PR #83** — Cross-team automation (CODEOWNERS + release-notify.yml + deploy-validate CI job + CONTRIBUTING.md §10). PR #83 open, awaiting Meridian review (48h SLA).

## Open items

- **PR #83** — Cross-team automation (CODEOWNERS, release-notify.yml, deploy-validate); awaiting Meridian review (due ~2026-03-16T20:40)
- **PR #79** — Team Meridian .meridian/ memory backup; blocked on Meridian redacting public IP + open DB ports from meridian_server.md
- **PR #81** — release-please 2.2.1 PR (auto-generated); will auto-merge when next feature lands
- **Distributed system deployment** — 5-server plan (sub-ctrl, sub-api-1/2, sub-data, sub-worker-1) not yet started
- **process_video() refactoring** — 514 lines → step functions, deferred
- **SLOs** — not yet defined
- **mypy/pyright** — not yet in CI
</content>
</invoke>