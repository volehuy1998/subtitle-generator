---
name: meridian_issues_tracker
description: Team Meridian filed issues tracker — all deployment gaps reported to Sentinel team with status and assigned specialist
type: project
---

# Meridian Issues Tracker

## Filed Issues

| Issue | Title | Priority | Meridian Specialist | Status |
|-------|-------|----------|-------------------|--------|
| [#67](https://github.com/volehuy1998/subtitle-generator/issues/67) | deploy.sh Unicode crash (line 277) | P0-critical | Dockhand (container/deploy) | Open |
| [#68](https://github.com/volehuy1998/subtitle-generator/issues/68) | Missing newui Docker Compose profile | P1-high | Dockhand (container/deploy) | Open |
| [#69](https://github.com/volehuy1998/subtitle-generator/issues/69) | ENVIRONMENT=prod redirect loop behind proxy | P1-high | Crane (infra/nginx) | Open |
| [#70](https://github.com/volehuy1998/subtitle-generator/issues/70) | PROD_IMAGE_TAG not used in docker-compose | P0-critical | Dockhand (container/deploy) | Open |
| [#71](https://github.com/volehuy1998/subtitle-generator/issues/71) | CLAUDE.md wrong routes, missing WebSocket, cookie/CORS | P1-high | Signal (integration) + Vault (security) | Open |
| [#72](https://github.com/volehuy1998/subtitle-generator/issues/72) | Missing collaborator onboarding docs | P2-medium | Compass (lead) | Open |
| [#78](https://github.com/volehuy1998/subtitle-generator/issues/78) | deploy.sh lacks config file best-practice guidance | P2-medium | Compass (lead) | Open |

## Specialist Assignment Rationale

- **Dockhand** (Priya Kapoor): Container & orchestration issues (#67, #68, #70) — deploy.sh, docker-compose, image tagging
- **Crane** (Marcus Okonkwo): Infrastructure issues (#69) — nginx proxy, TLS termination, HSTS
- **Signal** (Fiona Chen): Integration issues (part of #71) — WebSocket /ws endpoint, SSE relay, CORS
- **Vault** (Anya Petrova): Security issues (part of #71) — session cookie Secure flag, HSTS, security headers
- **Compass** (Diana Reeves): Process/docs issues (#72, #78) — onboarding, best practices

## Pending Investigations

Team members not yet deployed but with known investigation areas:
- **Gauge** (Tomás Delgado): Prometheus metrics format, log aggregation, alerting integration
- **Rudder** (Kenji Matsuda): PostgreSQL fresh setup, Alembic bootstrap, backup procedures
- **Ballast** (Eliot Strand): Resource sizing guide, VRAM/RAM per model, concurrency tuning
