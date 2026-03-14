---
name: project_session_20260315
description: Session on 2026-03-15 — CI/CD fixes, ESLint mask removed, subdomain UI evaluation, PR attribute standards enforced
type: project
---

# Session Summary — 2026-03-15

## What Was Done

### CI/CD Fixes (PRs #63, #65)

**PR #63 — release-please fix (merged)**
- `release-please-action@v4` was failing: `package-name` input is v3 syntax, invalid in v4
- `default_workflow_permissions` was `read` — blocked PR creation by release-please
- Fix: removed `package-name` from `.github/workflows/release.yml`, set permissions to `write` via API
- First green Release workflow run achieved

**PR #65 — ESLint mask removed + 5 errors fixed (merged)**
- `|| true` in CI ESLint step was silently swallowing all linting failures
- 5 real ESLint errors uncovered and fixed:
  1. `react-refresh/only-export-components` → extracted `Router` into `src/Router.tsx`
  2. `react-hooks/static-components` → direct conditional returns in `Router.tsx`
  3. TDZ circular reference in `useSSE.ts` → added `connectRef` ref
  4. `@typescript-eslint/no-unused-expressions` in `StatusPage.tsx toggleCommit` → if/else
  5. `react-hooks/set-state-in-effect` in `StatusPage.tsx useEffect` → moved disable comment to correct line
- Issue #66 created to track the ESLint mask bug

### Subdomain UI Evaluation (Enterprise Slate)
- Playwright screenshots of all 5 pages at `newui.openlabs.club`
- Found and fixed: Google Fonts blocked (CSP `connect-src` → `font-src`), GPU badge on all pages, outdated About stack, wrong security commit SHA
- PRs #57–61 merged; Docker image rebuilt on port 8001; re-verified clean

### PR Attribute Standards Enforced
- All PRs must have 6 GitHub attributes: Reviewers, Assignees, Labels, Projects, Milestone, Development
- **Reviewer limitation**: GitHub prevents author from reviewing their own PR; `volehuy1998` is the only collaborator — this is a solo repo constraint
- Projects linked to "SubForge Roadmap" (PVT_kwHOAi6TKc4BRufS)
- Milestone: v2.2.0 — UI & Developer Experience (ID 1) or v3.0.0 — Distributed System & Scale (ID 2)

## Open Items (carried forward)
- Distributed system deployment (5-server Ansible)
- Team Meridian issue #37 (production deployment docs)
- process_video() refactor, SLOs, mypy/pyright
