---
name: project_pending_work
description: Open work items as of 2026-03-15
type: project
---

As of 2026-03-15, CI is fully green. All known ESLint errors resolved.

## Recently completed (2026-03-15)

- **release-please automation** — PR #63 merged: removed invalid `package-name` input (v4 syntax), fixed repo `default_workflow_permissions` to `write`
- **ESLint mask removed** — PR #65 merged: removed `|| true` from CI ESLint step; fixed all 5 hidden ESLint errors; extracted `Router.tsx` from `main.tsx`; added `connectRef` in `useSSE.ts` for TDZ-safe recursive reconnect
- **Issue #66 created and closed** — tracking issue for the ESLint mask bug

## Open items

- **Distributed system deployment** — 5-server plan (sub-ctrl, sub-api-1/2, sub-data, sub-worker-1) not yet started; Ansible playbooks not yet written
- **process_video() refactoring** — 514 lines → step functions, deferred
- **StatusPage / TranscribeForm component splitting** — deferred
- **SLOs** — not yet defined
- **mypy/pyright** — not yet in CI
- **Team Meridian (#37)** — external deployment team waiting for response on production deployment docs
