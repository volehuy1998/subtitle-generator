---
name: TLS and deployment setup for openlabs.club
description: TLS cert obtained, main.py updated with HTTPS+HTTP redirect, DEPLOY.md created for fresh Ubuntu 24.04 hosts
type: project
---

TLS certificate obtained via Certbot for the production domain:
- Cert and key paths configured via `SSL_CERTFILE` and `SSL_KEYFILE` env vars
- Auto-renewal configured via Certbot systemd timer

main.py updated to run HTTPS on port 443 + HTTP→HTTPS redirect on port 80 (dual uvicorn servers via asyncio.gather).

DEPLOY.md created with full deployment instructions for fresh Ubuntu Server 24.04 hosts, including a quick deploy script.

**Why:** Service will be publicly accessible globally, user plans to deploy on many fresh Ubuntu 24.04 hosts.
**How to apply:** Refer to DEPLOY.md for deployment steps. Requires sudo for privileged ports. System deps: python3, python3-venv, ffmpeg, libsndfile1, certbot.
