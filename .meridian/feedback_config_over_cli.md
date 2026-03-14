---
name: feedback_config_over_cli
description: Investor preference — always use .env config files over CLI flags for deployment, document best practices clearly
type: feedback
---

Always prefer `.env` configuration files over inline CLI flags when deploying.

**Why:** The investor raised this as a known concern with the Sentinel team. CLI flags are ephemeral, hard to reproduce, and don't self-document. Configuration files provide reproducibility, version control, and clarity about what's deployed.

**How to apply:** When deploying or configuring SubForge (or any service), always:
1. Copy `.env.example` to `.env` first
2. Fill in deployment-specific values in `.env`
3. Let Docker Compose / deploy script read from `.env`
4. Never edit `docker-compose.yml` directly for environment-specific overrides
5. If a deploy script lacks config file support, file an issue requesting it
