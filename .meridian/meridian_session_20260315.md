---
name: meridian_session_20260315
description: Full session context — deployment, 7 issues, audit, cross-team RFC, security PRs reviewed, sensitive data RFC, deployment updated, all resolved
type: project
---

# Meridian Session — 2026-03-15

## Final State

All issues closed. All PRs merged. Deployment updated. Cross-team automation live. Sensitive data scanning in CI.

### Deployment

| Domain | Status | Image | Includes |
|--------|--------|-------|----------|
| meridian-openlabs.shop | Healthy | v2.1.0 pinned | Stable purple UI (Inter font) |
| newui.meridian-openlabs.shop | Healthy | Latest main | Enterprise Slate theme + all security fixes |

Infrastructure: PostgreSQL 16, Redis 7, host nginx (TLS + HSTS), Let's Encrypt (expires 2026-06-12)
Config: `docker-compose.override.yml` (ports, no certs, ENVIRONMENT=dev) + `.env` (DOMAIN, PROD_IMAGE_TAG)

### Issues Filed & Resolved (all 7 closed)

| Issue | Priority | Specialist | Resolution |
|-------|----------|-----------|------------|
| #67 | P0 | Dockhand | deploy.sh Unicode fix (PR #73) |
| #68 | P1 | Dockhand | newui Docker profile (PR #73) |
| #69 | P1 | Crane | Reverse proxy docs (PR #73) |
| #70 | P0 | Dockhand | PROD_IMAGE_TAG (PR #73) |
| #71 | P1 | Signal+Vault | Cookie/CORS/WebSocket (PR #73+#74) |
| #72 | P2 | Compass | Collaborator onboarding (PR #73) |
| #78 | P2 | Compass | Config best practices (PR #80) |

### PRs — Meridian Authored

| PR | Status | Review Rounds |
|----|--------|---------------|
| #79 | Merged | 3 rounds (redacted IP per Hawk) |
| #85 | Merged | 1 round |
| #91 | Open | Final session sync |

### PRs — Meridian Reviewed & Approved

| PR | Description |
|----|-------------|
| #83 | Cross-team automation (CODEOWNERS, release-notify, CI validation) |
| #86 | 30 CodeQL security fixes (path injection, stack trace, PBKDF2, XSS) |
| #87 | Automated sensitive data scanning (16 rules, TruffleHog + custom) |

### RFCs Resolved

| RFC | Topic | Outcome |
|-----|-------|---------|
| #82 | Cross-team automation | CODEOWNERS + release-notify + CI validation + 48h SLA |
| #89 | Sensitive data classification | 16 rules, no file-path exceptions, Category 4 = warning |

### Investor Rules (all saved to feedback memory files)

1. `feedback_config_over_cli.md` — use .env files, not CLI flags
2. `feedback_delegate_no_bottleneck.md` — delegate to specialists
3. `feedback_author_disclosure.md` — identify yourself on all content
4. `feedback_pr_review_process.md` — PR comments visible on GitHub
5. `feedback_detailed_logging.md` — thorough logging
6. `feedback_vault_review_before_push.md` — Vault scans before every GitHub push

### Key Learnings

- Local MEMORY.md must also use redacted descriptions (root cause of repeated IP leak)
- `docker-compose.override.yml` is the correct way to customize without editing upstream compose file
- `!override` directive replaces merged sequences (ports, volumes) in Compose v5+
- Cross-team CODEOWNERS with SLA prevents bottleneck while ensuring review
- Automated CI scanning catches what manual review misses
