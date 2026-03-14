---
name: project_distributed_system
description: Distributed deployment plan — 5 CPU servers, agreed architecture, model preloading
type: project
---

## Infrastructure
- 5 servers, all 8C/24G/300GB, CPU-only (GPUs coming later), LAN network

## Agreed server allocation
| Hostname | Role | Services |
|---|---|---|
| **sub-ctrl** | LB + deploy controller | Nginx, Ansible, Certbot, Flower |
| **sub-api-1** | API node 1 | FastAPI (ROLE=web) |
| **sub-api-2** | API node 2 | FastAPI (ROLE=web) |
| **sub-data** | Data tier | PostgreSQL 16, Redis 7, MinIO |
| **sub-worker-1** | Transcription worker | Celery (ROLE=worker), all Whisper models preloaded |

## Key decisions
- All Whisper models (tiny→large) preloaded on workers at startup (PRELOAD_MODEL=all)
- CPU int8 compute type (~5.2GB total for all 5 models, fits in 24GB)
- User will notify when GPUs become available — plan will expand with GPU workers

**Why:** User has multiple servers, needs to scale the service.

**How to apply:** Reference this plan when discussing deployment, scaling, or infrastructure changes. Workers are the scaling bottleneck — add more worker servers for throughput.
