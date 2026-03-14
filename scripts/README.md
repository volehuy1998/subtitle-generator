# Utility Scripts

| Script | Purpose | Usage |
|--------|---------|-------|
| deploy.sh | Production deployment automation | `bash scripts/deploy.sh` |
| analyze.py | Log analysis and diagnostics | `python scripts/analyze.py` |
| benchmark.py | Performance benchmarking | `python scripts/benchmark.py` |
| loadtest.py | Concurrent load testing | `python scripts/loadtest.py` |
| check_interface.py | Playwright UI verification | `python scripts/check_interface.py` |
| renew-certs.sh | TLS certificate renewal | `bash scripts/renew-certs.sh` |
| setup-cron.sh | Cron job setup for cert renewal | `bash scripts/setup-cron.sh` |
| update_security_assertions.py | Update security tracking data | Called by post-commit hook |

## Fail2ban Configuration

The `fail2ban/` subdirectory contains filter and jail configs for protecting the service
against brute-force and abuse. See inline comments in those files for installation steps.
