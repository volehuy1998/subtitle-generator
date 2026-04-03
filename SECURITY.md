# Security Policy

## Supported Versions

| Version | Supported          |
|---------|--------------------|
| 2.5.x   | Yes                |
| 2.4.x   | Security fixes only|
| < 2.4   | No                 |

## Reporting a Vulnerability

**Do not open a public GitHub issue.** Use GitHub's private vulnerability reporting:

1. Go to the [Security tab](https://github.com/volehuy1998/subtitle-generator/security)
2. Click **Report a vulnerability**
3. Include: description, steps to reproduce, affected component, and potential impact

| Stage              | Timeframe           |
|--------------------|---------------------|
| Acknowledgment     | Within 48 hours     |
| Initial assessment | Within 5 business days |
| Fix development    | Based on severity   |
| Public disclosure  | After fix is released |

## Security Features

- **Authentication**: API key auth (`X-API-Key`), JWT tokens, brute-force protection
- **Input validation**: File type allowlist, magic bytes verification, size limits, ClamAV quarantine
- **Security headers**: CSP (nonce-based), HSTS, X-Frame-Options, X-Content-Type-Options
- **Audit logging**: HMAC-signed entries for all sensitive operations
- **Automated scanning**: CodeQL, GitHub Secret Protection, Semgrep SAST
- **Infrastructure**: TLS enforcement in production, fail2ban integration, rate limiting, CORS validation

## Live Status

Visit [`/security`](https://openlabs.club/security) to see real-time OWASP security assertion results.
