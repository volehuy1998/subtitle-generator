"""FastAPI application factory."""

from app.config import UPLOAD_DIR, OUTPUT_DIR, LOG_DIR  # noqa: F401 - must import first for env vars

import asyncio
from contextlib import asynccontextmanager

from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse

from app import state
from app.logging_setup import setup_logging, log_task_event
from app.middleware.request_log import RequestLogMiddleware
from app.middleware.security import SecurityHeadersMiddleware
from app.middleware.auth import ApiKeyMiddleware
from app.middleware.session import SessionMiddleware
from app.routes import router
from app.services.system_capability import detect_system_capabilities, log_capabilities
from app.services.cleanup import periodic_cleanup
from app.services.analytics import load_analytics_snapshot, save_analytics_snapshot
from app.config import PRELOAD_MODEL, ENABLE_COMPRESSION, ROLE, REDIS_URL

import logging

logger = logging.getLogger("subtitle-generator")


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Startup and shutdown lifecycle."""
    # Startup
    UPLOAD_DIR.mkdir(exist_ok=True)
    OUTPUT_DIR.mkdir(exist_ok=True)
    LOG_DIR.mkdir(exist_ok=True)

    # Initialize databases
    from app.db.engine import init_db, close_db
    await init_db()
    from app.db.status_engine import init_status_db, close_status_db
    await init_status_db()

    # Capture main event loop for thread-safe async scheduling
    state.main_event_loop = asyncio.get_running_loop()

    # Detect system capabilities and apply auto-tuning
    caps = detect_system_capabilities()
    log_capabilities(caps)
    app.state.system_caps = caps

    # Apply tuning to config
    _apply_tuning(caps["tuning"])

    # Load task history from DB (with JSON file fallback)
    from app.services.task_backend import get_task_backend
    from app.db.task_backend_db import DatabaseTaskBackend
    backend = get_task_backend()
    if isinstance(backend, DatabaseTaskBackend):
        loaded = await backend.load_from_db()
        if loaded == 0:
            # First run: migrate from task_history.json if it exists
            state.load_task_history()
            for tid, tdata in state.tasks.items():
                backend.set(tid, tdata)
                await backend.persist_task(tid, tdata)
            if state.tasks:
                logger.info(f"Migrated {len(state.tasks)} tasks from JSON to DB")
        else:
            # Populate state.tasks from DB cache for backward compat
            for tid, tdata in backend.items():
                state.tasks[tid] = tdata
            logger.info(f"Loaded {loaded} tasks from database")
    else:
        state.load_task_history()

    # Load analytics: try DB first, fallback to JSON snapshot
    from app.services.analytics import load_analytics_from_db
    db_loaded = await load_analytics_from_db()
    if not db_loaded:
        load_analytics_snapshot()

    log_task_event("system", "startup", **{
        "role": ROLE,
        "platform": caps["platform"]["os"],
        "cpu_cores": caps["cpu"]["logical_cores"],
        "ram_gb": caps["memory"]["total_gb"],
        "gpu": caps["gpu"]["devices"][0]["name"] if caps["gpu"]["devices"] else "none",
        "tuning": caps["tuning"],
        "redis": bool(REDIS_URL),
    })

    # Register this worker for health monitoring
    from app.services.worker_health import register_worker
    worker_id = register_worker()
    app.state.worker_id = worker_id

    # Preload model if configured (skip on web-only servers)
    if ROLE != "web" and PRELOAD_MODEL and PRELOAD_MODEL in ("tiny", "base", "small", "medium", "large"):
        try:
            from app.services.model_manager import get_model
            import torch
            device = "cuda" if torch.cuda.is_available() else "cpu"
            logger.info(f"PRELOAD Loading model '{PRELOAD_MODEL}' on {device.upper()}...")
            await asyncio.to_thread(get_model, PRELOAD_MODEL, device)
            logger.info(f"PRELOAD Model '{PRELOAD_MODEL}' ready")
        except Exception as e:
            logger.warning(f"PRELOAD Failed: {e}")

    # Start background cleanup task
    cleanup_task = asyncio.create_task(periodic_cleanup())

    # Load open incidents for status page
    from app.services.incident_logger import load_open_incidents
    await load_open_incidents()

    # Start background health monitor (sets/clears state.system_critical)
    from app.services.health_monitor import health_check_loop
    health_task = asyncio.create_task(health_check_loop())

    yield

    # Shutdown
    state.shutting_down = True
    cleanup_task.cancel()
    health_task.cancel()
    try:
        await cleanup_task
    except asyncio.CancelledError:
        pass
    try:
        await health_task
    except asyncio.CancelledError:
        pass

    # Drain in-flight tasks
    active = state.get_active_task_count()
    if active > 0:
        logger.info(f"SHUTDOWN Draining {active} in-flight task(s)...")
        await asyncio.to_thread(state.drain_tasks, 60.0)

    logger.info("SHUTDOWN Saving task history and analytics...")

    # Persist final task states to DB
    from app.services.task_backend import get_task_backend
    from app.db.task_backend_db import DatabaseTaskBackend
    backend = get_task_backend()
    if isinstance(backend, DatabaseTaskBackend):
        for tid, tdata in state.tasks.items():
            if tdata.get("status") in ("done", "error", "cancelled"):
                await backend.persist_task(tid, tdata)
    else:
        state.save_task_history()

    save_analytics_snapshot()  # Keep JSON snapshot as backup

    # Close legacy analytics SQLite (if still open)
    try:
        from app.services.analytics_db import close as close_analytics_db
        close_analytics_db()
    except Exception:
        pass

    # Close Redis connections
    if REDIS_URL:
        try:
            from app.services.redis_client import close_async_redis, close_sync_redis
            await close_async_redis()
            close_sync_redis()
        except Exception:
            pass

    # Close status DB (local SQLite)
    await close_status_db()

    # Close main DB
    await close_db()

    logger.info(f"SHUTDOWN Complete (role={ROLE})")


def _apply_tuning(tuning: dict):
    """Apply auto-tuned settings to runtime config."""
    import os
    from app import config

    # Update OMP threads if auto-tuned value differs
    omp = str(tuning["omp_threads"])
    os.environ["OMP_NUM_THREADS"] = omp
    os.environ["MKL_NUM_THREADS"] = omp

    # Update concurrent task limit
    config.MAX_CONCURRENT_TASKS = tuning["max_concurrent_tasks"]

    logger.info(f"TUNING Applied: OMP_THREADS={omp}, MAX_TASKS={tuning['max_concurrent_tasks']}")


def create_app() -> FastAPI:
    # Setup logging before anything else
    LOG_DIR.mkdir(exist_ok=True)
    setup_logging()

    openapi_tags = [
        {"name": "Upload", "description": "File upload and transcription initiation"},
        {"name": "Progress", "description": "Real-time task progress (SSE, WebSocket, polling)"},
        {"name": "Download", "description": "Download generated subtitles (SRT, VTT, JSON)"},
        {"name": "Tasks", "description": "Task queue management, retry, deduplication"},
        {"name": "Subtitles", "description": "Subtitle viewing and editing"},
        {"name": "Embedding", "description": "Embed subtitles into video files"},
        {"name": "Analytics", "description": "Usage analytics, charts, and data export"},
        {"name": "System", "description": "Health checks, system info, metrics"},
        {"name": "User", "description": "Feedback, sessions, webhooks"},
    ]

    app = FastAPI(
        title="Subtitle Generator",
        description=(
            "AI-powered subtitle generation service using faster-whisper (CTranslate2).\n\n"
            "## Features\n"
            "- **99 languages** with auto-detection\n"
            "- **Word-level timestamps** for karaoke-style subtitles\n"
            "- **Speaker diarization** (who is speaking)\n"
            "- **Subtitle embedding** (soft mux + hard burn with ASS styling)\n"
            "- **Real-time progress** via SSE and WebSocket\n"
            "- **Analytics dashboard** with charts and data export\n\n"
            "## Output Formats\n"
            "- SRT (SubRip), VTT (WebVTT), JSON (with word-level data)\n\n"
            "## Authentication\n"
            "Optional API key via `X-API-Key` header or `api_key` query parameter.\n"
            "Set `API_KEYS` environment variable (comma-separated) to enable."
        ),
        version="2.0.0",
        lifespan=lifespan,
        docs_url="/docs",
        redoc_url="/redoc",
        openapi_tags=openapi_tags,
        swagger_ui_parameters={
            "defaultModelsExpandDepth": -1,
            "docExpansion": "list",
            "filter": True,
            "tryItOutEnabled": True,
        },
    )

    # Middleware (order matters: last added = first executed)
    app.add_middleware(RequestLogMiddleware)

    # Critical state gate — blocks all user operations when system is unhealthy.
    # Placed early (runs before auth/session) so blocked requests skip all processing.
    from app.middleware.critical_state import CriticalStateMiddleware
    app.add_middleware(CriticalStateMiddleware)

    app.add_middleware(ApiKeyMiddleware)

    # Brute force protection (before auth, blocks repeat offenders)
    from app.middleware.brute_force import BruteForceMiddleware
    app.add_middleware(BruteForceMiddleware)

    app.add_middleware(SessionMiddleware)

    # Request body size limiting
    from app.middleware.body_limit import BodyLimitMiddleware
    app.add_middleware(BodyLimitMiddleware)

    app.add_middleware(SecurityHeadersMiddleware)

    # CORS
    from starlette.middleware.cors import CORSMiddleware
    from app.middleware.cors import get_cors_origins, CORS_ALLOW_METHODS, CORS_ALLOW_HEADERS
    app.add_middleware(
        CORSMiddleware,
        allow_origins=get_cors_origins(),
        allow_credentials=True,
        allow_methods=CORS_ALLOW_METHODS,
        allow_headers=CORS_ALLOW_HEADERS,
    )

    # GZip compression (outermost, compresses all responses)
    if ENABLE_COMPRESSION:
        from app.middleware.compression import GZipMiddleware
        app.add_middleware(GZipMiddleware, minimum_size=500)

    # Global exception handler - prevents unhandled exceptions from crashing the service
    @app.exception_handler(Exception)
    async def global_exception_handler(request: Request, exc: Exception):
        logger.error(f"UNHANDLED {request.method} {request.url.path}: {type(exc).__name__}: {exc}", exc_info=True)
        log_task_event("system", "unhandled_exception",
                       path=str(request.url.path),
                       method=request.method,
                       error_type=type(exc).__name__,
                       error=str(exc))
        return JSONResponse(
            status_code=500,
            content={"detail": "Internal server error. Please try again."},
        )

    # Routes
    app.include_router(router)

    # Serve React build assets (JS/CSS bundles)
    from pathlib import Path
    from fastapi.staticfiles import StaticFiles
    _react_assets = Path(__file__).parent.parent / "frontend" / "dist" / "assets"
    if _react_assets.exists():
        app.mount("/assets", StaticFiles(directory=str(_react_assets)), name="react-assets")

    return app


app = create_app()
