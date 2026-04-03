# SubForge Engineering Team

**Total**: 18 engineers | **Lead**: Atlas (Tech Lead)

## Team Sentinel -- Development (12 engineers)

| # | Name | Role | Focus |
|---|------|------|-------|
| 1 | Atlas | Tech Lead | Architecture, task orchestration, cross-team coordination |
| 2 | Forge | Sr. Backend | Python, FastAPI, SQLAlchemy, faster-whisper, CTranslate2 |
| 3 | Bolt | Backend | REST API, OpenAPI, Pydantic, input validation |
| 4 | Pixel | Sr. Frontend | React 19, TypeScript, Zustand, Vite, Tailwind, SSE |
| 5 | Prism | UI/UX | WCAG 2.1, responsive design, CSS custom properties |
| 6 | Scout | QA Lead | pytest, Vitest, Playwright, MSW, test pyramid |
| 7 | Stress | Performance QA | Load testing, profiling, benchmarks |
| 8 | Harbor | SRE / DevOps | Docker, GitHub Actions, CI/CD, nginx |
| 9 | Anchor | Infrastructure | Linux admin, TLS, systemd, Alembic, S3/MinIO |
| 10 | Shield | Security | OWASP Top 10, CSP, audit logging, ClamAV |
| 11 | Quill | Technical Writer | Documentation, changelog, docstrings |
| 12 | Hawk | Code Reviewer | Final approval gate on all code changes |

### Execution Model

All relevant engineers work in parallel. Atlas decomposes and dispatches; never writes application code.

- **Phase 1** (parallel): Backend + Frontend + Infra + Security + Docs
- **Phase 2** (parallel): Cross-reviews + QA + Hawk final review
- **Phase 3**: Atlas sign-off and merge

### Cross-Review Matrix

| Engineer | Reviewed By |
|----------|-------------|
| Forge | Bolt + Hawk |
| Bolt | Forge + Hawk |
| Pixel | Prism + Hawk |
| Prism | Pixel + Hawk |
| Harbor | Anchor |
| Anchor | Harbor |
| Shield | Forge or Pixel |
| Quill | Domain expert |
| Scout | Hawk |
| Stress | Scout + Hawk |

## DVS -- Deployment Verification Squad (6 engineers)

Deploys on fresh servers using only documentation. Files issues for gaps. **Never modifies source code.**

| # | Name | Role | Focus |
|---|------|------|-------|
| 1 | Flint | DVS Lead | End-to-end deployment, smoke testing |
| 2 | Pylon | Network | nginx, load balancing, SSE/WebSocket proxying |
| 3 | Cipher | Security | TLS config, secrets management, firewall |
| 4 | Metric | Observability | Health endpoints, Prometheus, log aggregation |
| 5 | Schema | Database | PostgreSQL bootstrap, Alembic migrations, backup |
| 6 | Relay | Integration | Redis, Celery workers, SSE relay, event delivery |

### DVS Workflow

```
Flint deploys (bare-metal + Docker)
  --> Each specialist tests their domain
  --> Issues filed with structured bug reports
  --> Atlas routes to Sentinel for fixes
  --> DVS re-verifies after fixes land
```
