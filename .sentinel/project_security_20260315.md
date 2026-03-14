---
name: project_security_20260315
description: Security work completed 2026-03-15 — CodeQL fixes and automated secret scanning
type: project
---

**Why:** The codebase had 30 open CodeQL alerts. PR #85 (Meridian memory sync) leaked a public IP. Both needed to be addressed.

**How to apply:** When touching auth/API key code, be aware of the PBKDF2 migration and the API key hash migration blocker.

## PR #86 — 30 CodeQL fixes (security/codeql-fixes branch)

| Category | Fix |
|---|---|
| `py/path-injection` | safe_path() + Path(filename).name in storage, routes |
| `py/stack-trace-exposure` | str(e) removed from all HTTP responses; logged server-side |
| `py/weak-sensitive-data-hashing` | PBKDF2-HMAC-SHA256 for passwords, HMAC-SHA256 for API keys |
| `js/xss-through-dom` | createElement+textContent instead of innerHTML for GPU/device badges |
| `py/bad-tag-filter` | </\s*script\s*> to match trailing whitespace |
| `py/insecure-protocol` | ctx.minimum_version = TLSv1_2 on all SSL contexts |
| `actions/missing-workflow-permissions` | permissions: contents: read in ci.yml |
| `py/incomplete-url-substring-sanitization` | token-based CSP assertions in tests |

### PBKDF2 migration (backward compat)
- New hashes: `pbkdf2:salt:hex` (260k iterations)
- Legacy hashes: `salt:hex` (SHA-256) — verified via legacy path until user re-authenticates
- No forced migration, no lockouts

### API key hash migration BLOCKER
- `hash_api_key()` changed from `sha256(key)` to `hmac(JWT_SECRET, key, sha256)`
- Existing `api_keys` DB rows will fail validation after deploy
- Must run migration script or force-revoke all keys before production deploy

## PR #87 — Automated sensitive data scanning (feat/secret-scanning branch)

Added two-layer CI gate on every PR:

1. **TruffleHog** (`trufflesecurity/trufflehog@main --only-verified`): tokens, API keys, PEM certs, 700+ detectors
2. **scripts/scan_sensitive.py**: public IPv4 (RFC 1918 excluded), PEM keys, DB URLs with credentials, hardcoded passwords
3. **.scanignore**: allowlist for RFC 5737 test IPs, localhost, test fixtures

**Proof:** scanner catches `124.197.31.140` (exit 1), passes `10.0.1.5` / `192.168.1.100` (exit 0).
