---
name: project_pending_work
description: Current project status — uncommitted multi-model preload changes, distributed deployment in progress
type: project
---

As of 2026-03-14, CI is fully green. Translation feature committed and pushed.

## Uncommitted changes (in progress)
- **PRELOAD_MODEL enhancement**: Now supports `"all"`, comma-separated lists (e.g. `"tiny,base,large"`), in addition to single model. Changed in `app/config.py` and `app/main.py`.
- Next step: user wants Ansible playbooks for deploying to 5 servers (see project_distributed_system.md)

## Recently committed (2026-03-14)
- Translation support: Argos Translate (any-to-any) + Whisper translate (any->English)
- Translation route, service, frontend UI, pipeline integration with progress events
- Enhanced embed panel with style options
- Translation and control test suites, e2e tests
- Updated CLAUDE.md with full current architecture (29 routes, 32 services, 12 middleware, 1326 tests)
- cert.pem and privkey.pem excluded from git (should be in .gitignore)

## No known outstanding issues
