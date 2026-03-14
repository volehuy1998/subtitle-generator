---
name: project_cross_team_agreement
description: Sentinel-Meridian cross-team collaboration agreement — CODEOWNERS, 48h review SLA, release notifications, CI validation (RFC #82, agreed 2026-03-15)
type: project
---

# Cross-Team Collaboration Agreement

**Agreed:** 2026-03-15 via RFC [#82](https://github.com/volehuy1998/subtitle-generator/issues/82)
**Parties:** Team Sentinel (Atlas) + Team Meridian (Compass)

## 1. CODEOWNERS — Meridian as required reviewer

Files requiring Meridian review before merge:
- docker-compose.yml, scripts/deploy.sh, docs/DEPLOY.md, .env.example
- Dockerfile, Dockerfile.gpu, nginx.conf, entrypoint.sh

## 2. Response SLA

- Meridian responds within **48 hours** on CODEOWNERS-triggered reviews
- If no response in 48h, Sentinel may merge with a note
- Documented in CONTRIBUTING.md

## 3. Release Deployment Notification

- GitHub Actions workflow fires on `release: [published]`
- Creates a joint deployment checklist issue tagging both teams
- Includes changelog summary

## 4. CI Validation of Deploy Files

- `docker compose --profile cpu config` + `--profile newui config`
- `bash -n scripts/deploy.sh`
- `PROD_IMAGE_TAG` consistency check

## Implementation Assignments

| Task | Sentinel Engineer | Meridian Reviewer |
|------|-------------------|-------------------|
| CODEOWNERS + SLA docs | Forge | Crane |
| Release notify workflow | Bolt | Gauge |
| CI validation job | Scout | Signal |

**Why:** Investor requested continuous automatic collaboration without manual reminders. This agreement ensures both directions: Sentinel changes trigger Meridian review, releases trigger joint deployment checklists.
