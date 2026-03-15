# Security Policy

## Supported Versions

| Version | Supported |
|---------|-----------|
| 2.3.x   | Yes       |
| 2.2.x   | Security fixes only |
| < 2.2   | No        |

## Reporting a Vulnerability

If you discover a security vulnerability in SubForge, please report it responsibly.

### How to Report

1. **Do NOT open a public GitHub issue** for security vulnerabilities.
2. **Email**: Send a detailed report to the repository maintainer via GitHub's private vulnerability reporting feature:
   - Go to the [Security tab](https://github.com/volehuy1998/subtitle-generator/security) of this repository
   - Click **"Report a vulnerability"**
   - Provide a detailed description including steps to reproduce

### What to Include

- Description of the vulnerability
- Steps to reproduce
- Affected component(s) (e.g., `app/middleware/auth.py`, `app/routes/upload.py`)
- Potential impact assessment
- Suggested fix (if you have one)

### Response Timeline

| Stage | Timeframe |
|-------|-----------|
| Acknowledgment | Within 48 hours |
| Initial assessment | Within 5 business days |
| Fix development | Depends on severity |
| Public disclosure | After fix is released |

### Severity Classification

| Level | Description | Example |
|-------|-------------|---------|
| **Critical** | Remote code execution, authentication bypass, data exfiltration | SQL injection in query params, API key leak |
| **High** | Privilege escalation, significant data exposure | Path traversal in file download, SSRF |
| **Medium** | Limited data exposure, denial of service | XSS in subtitle preview, file upload bypass |
| **Low** | Minor information disclosure, best practice violations | Missing security headers, verbose error messages |

## Security Measures in Place

SubForge implements the following security controls:

### Authentication & Authorization
- Optional API key authentication via `X-API-Key` header
- Brute-force protection middleware with automatic IP blocking
- Session management with secure cookie attributes

### Input Validation
- File upload validation: extension allowlist, magic bytes verification, size limits
- ClamAV quarantine integration for uploaded files (when available)
- Request body size limiting middleware

### Security Headers
- Content Security Policy (CSP)
- HTTP Strict Transport Security (HSTS) in production mode
- X-Frame-Options, X-Content-Type-Options, X-XSS-Protection
- Referrer-Policy

### Monitoring & Audit
- Audit logging for all sensitive operations (`app/services/audit.py`)
- Request logging middleware
- Security assertion tracking at `/security` with live OWASP results
- Automated secret scanning in CI (`.github/workflows/secret-scan.yml`)
- CodeQL static analysis (`.github/workflows/codeql.yml`)

### Infrastructure
- TLS/HTTPS enforcement in production mode
- Fail2ban integration for brute-force mitigation (`scripts/fail2ban/`)
- Rate limiting middleware
- CORS origin validation

## Live Security Status

Visit [`/security`](https://openlabs.club/security) on the live demo to see real-time OWASP security assertion results. Security commits automatically update `data/security_assertions.json` via a git post-commit hook.

## Automated Scanning

| Tool | Purpose | Config |
|------|---------|--------|
| CodeQL | Static analysis (Python + JavaScript) | `.github/workflows/codeql.yml` |
| Secret scanning | Detect leaked credentials | `.github/workflows/secret-scan.yml` |
| `scan_sensitive.py` | Custom sensitive data scanner | `scripts/scan_sensitive.py` |
| Ruff | Python linting (security rules) | `pyproject.toml` |
