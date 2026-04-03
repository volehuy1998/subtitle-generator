# Scripts

| Script | Purpose |
|--------|---------|
| `deploy-profile.sh` | Branch-per-environment Docker deployment |
| `renew-certs.sh` | Renew TLS certificates via certbot |
| `setup-cron.sh` | Install cron job for automatic cert renewal |
| `validate_consistency.py` | CI consistency checks (version, links, module counts) |
| `update_security_assertions.py` | Update security tracking data (called by post-commit hook) |
| `analyze.py` | Log analysis and diagnostics |
| `benchmark.py` | Performance benchmarking |
| `loadtest.py` | Concurrent load testing |
| `check_interface.py` | Playwright UI verification |
| `cleanup_test_incidents.py` | Remove test incident data |

## deploy-profile.sh

Handles branch checkout, Docker build, health verification, and rollback tagging.

```bash
# Production (builds from PROD_BRANCH, currently prod-editorial-nav)
./scripts/deploy-profile.sh cpu

# Production with git tag for rollback
./scripts/deploy-profile.sh cpu --tag

# Staging (builds from NEWUI_BRANCH in .env)
./scripts/deploy-profile.sh newui

# Staging from a specific branch
./scripts/deploy-profile.sh newui feat/my-feature
```

## fail2ban/

Filter and jail configs for brute-force protection. See inline comments for installation steps.
