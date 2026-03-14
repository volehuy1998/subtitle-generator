---
name: project_session_20260315
description: Session 2026-03-15 summary — cross-team automation, CodeQL security fixes, secret scanning
type: project
---

## Session summary — 2026-03-15

### Completed

1. **PR #65** — ESLint fix (eslint-disable-next-line on wrong line in StatusPage.tsx)
2. **Meridian Issues #67–#72** — all resolved: deploy.sh syntax, docker-compose newui profile, nginx proxy_pass docs, session cookie Secure flag, CORS explicit headers, CONTRIBUTING.md onboarding
3. **v2.2.0 release** — PR #64 merged (CHANGELOG + version bump), Docker image published, PR #76 merged (.env.example PROD_IMAGE_TAG)
4. **PR #80 merged** — Configuration Best Practices in DEPLOY.md (resolves Meridian issue #78)
5. **RFC #82** — Proposed automated cross-team collaboration; Team Meridian agreed on Option D
6. **PR #83 merged** — CODEOWNERS + release-notify.yml + deploy-validate CI job + CONTRIBUTING.md §10. Joint approval from Sentinel (Bolt, Forge, Scout, Atlas) and Meridian (Compass, Crane, Gauge, Signal).
7. **PR #79 merged** — Team Meridian .meridian/ memory backup. Three security review rounds; IP/port redaction required and completed.
8. **PR #85 merged** — Team Meridian .meridian/ sync update (project_cross_team_agreement, feedback_vault_review)
9. **PR #86 MERGED** — 30 CodeQL security alert fixes: path injection, stack trace exposure, weak password hashing, XSS, bad tag filter, insecure TLS, workflow permissions, URL sanitization
10. **PR #87 MERGED** — Automated sensitive data scanning: TruffleHog + custom IP/credential scanner

### Key agreements with Team Meridian

- 48h review SLA for CODEOWNERS-triggered reviews
- 8 deploy-critical files require Meridian co-review
- Joint deployment checklist issue auto-created on every release
- CI validates compose profiles, bash syntax, tag consistency on every PR

### Infrastructure added

- .github/workflows/release-notify.yml — release deployment notifications
- .github/CODEOWNERS — Meridian co-review for deploy-critical files
- .meridian/ — Team Meridian memory backup directory
- Labels: deployment, sentinel, meridian
- CONTRIBUTING.md §10 — cross-team review protocol
- .github/workflows/secret-scan.yml — TruffleHog + custom scanner (PR #87)
- scripts/scan_sensitive.py — public IP and credential detector
- .scanignore — allowlist for known-safe patterns

### Security fixes (PR #86)

- auth.py: SHA-256 → PBKDF2-HMAC-SHA256 (260k iterations) for passwords; HMAC-SHA256 for API keys
  - **IMPORTANT**: hash_api_key() change is breaking for existing API keys in DB — needs migration script before deploying to production
- Path injection: safe_path() + Path(filename).name throughout routes and services
- Stack trace exposure: all str(e) removed from HTTP responses
- XSS: innerHTML → createElement/textContent for GPU and device badges
- Bad tag filter, insecure TLS, missing CI permissions

### How to apply

When working on deploy-critical files, expect Meridian review to be required.
On every release, a joint checklist issue will be auto-created.
Before deploying PR #86 to production: handle hash_api_key() migration for existing API key records.
