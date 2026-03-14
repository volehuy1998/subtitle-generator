---
name: Status page feature
description: Public status page at /status with service monitoring, uptime bars, incident timeline, auto-detection
type: project
---

Status page deployed at /status (commit 5856dd2):

**Files created:**
- `app/routes/status_page.py` — Backend API (`/status` HTML, `/api/status/page` JSON)
- `app/services/incident_logger.py` — Auto-detect and manage incidents
- `templates/status.html` — Full status page UI

**Files modified:**
- `app/db/models.py` — Added `StatusIncident` + `StatusIncidentUpdate` models
- `app/routes/__init__.py` — Registered `status_page_router`
- `app/services/health_monitor.py` — Calls `auto_detect_incidents()` every 5s cycle
- `app/main.py` — Calls `load_open_incidents()` on startup
- `templates/index.html` — Added "System Status" link in footer

**5 monitored components:** Transcription Engine, Video Combine, Web Application, Database, File Storage
**Auto-detection:** DB connectivity, FFmpeg availability, disk space — creates/resolves incidents automatically
