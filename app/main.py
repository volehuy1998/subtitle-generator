"""FastAPI application factory."""

# NOTE: app.config must be imported before any other app or third-party imports.
# It sets OMP_NUM_THREADS and MKL_NUM_THREADS env vars (lines 6-8 of config.py)
# which must be in place before PyTorch/NumPy/CTranslate2 are loaded by transitive imports.
from app.config import UPLOAD_DIR, OUTPUT_DIR, LOG_DIR  # noqa: E402, I001

import asyncio
import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse

from app import state
from app.config import ENABLE_COMPRESSION, PRELOAD_MODEL, REDIS_URL, ROLE
from app.logging_setup import log_task_event, setup_logging
from app.middleware.auth import ApiKeyMiddleware
from app.middleware.request_log import RequestLogMiddleware
from app.middleware.security import SecurityHeadersMiddleware
from app.middleware.session import SessionMiddleware
from app.routes import router
from app.services.analytics import load_analytics_snapshot, save_analytics_snapshot
from app.services.cleanup import periodic_cleanup
from app.services.system_capability import detect_system_capabilities, log_capabilities

logger = logging.getLogger("subtitle-generator")


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Startup and shutdown lifecycle."""
    # Startup
    UPLOAD_DIR.mkdir(exist_ok=True)
    OUTPUT_DIR.mkdir(exist_ok=True)
    LOG_DIR.mkdir(exist_ok=True)

    # Initialize databases
    from app.db.engine import close_db, init_db

    await init_db()
    from app.db.status_engine import close_status_db, init_status_db

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
    from app.db.task_backend_db import DatabaseTaskBackend
    from app.services.task_backend import get_task_backend

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

    log_task_event(
        "system",
        "startup",
        **{
            "role": ROLE,
            "platform": caps["platform"]["os"],
            "cpu_cores": caps["cpu"]["logical_cores"],
            "ram_gb": caps["memory"]["total_gb"],
            "gpu": caps["gpu"]["devices"][0]["name"] if caps["gpu"]["devices"] else "none",
            "tuning": caps["tuning"],
            "redis": bool(REDIS_URL),
        },
    )

    # Register this worker for health monitoring
    from app.services.worker_health import register_worker

    worker_id = register_worker()
    app.state.worker_id = worker_id

    # Preload models in background (skip on web-only servers)
    # Models load AFTER server starts accepting connections, so users see the UI immediately.
    # Supports: "medium", "tiny,base,large", or "all"
    if ROLE != "web" and PRELOAD_MODEL:
        from app.config import VALID_MODELS

        if PRELOAD_MODEL.strip().lower() == "all":
            models_to_load = list(VALID_MODELS)
        else:
            models_to_load = [m.strip() for m in PRELOAD_MODEL.split(",") if m.strip() in VALID_MODELS]
        if models_to_load:
            asyncio.create_task(_preload_models_background(models_to_load))

    # Start idle model preloader (loads next model after 5 min idle) — Forge (Sr. Backend Engineer)
    idle_preload_task = None
    if ROLE != "web":
        idle_preload_task = asyncio.create_task(_idle_preload_loop())

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
    if ROLE != "web" and idle_preload_task is not None:
        idle_preload_task.cancel()
    try:
        await cleanup_task
    except asyncio.CancelledError:
        logger.debug("Cleanup task cancelled")
    try:
        await health_task
    except asyncio.CancelledError:
        logger.debug("Health task cancelled")
    if ROLE != "web" and idle_preload_task is not None:
        try:
            await idle_preload_task
        except asyncio.CancelledError:
            logger.debug("Idle preload task cancelled")

    # Drain in-flight tasks
    active = state.get_active_task_count()
    if active > 0:
        logger.info(f"SHUTDOWN Draining {active} in-flight task(s)...")
        await asyncio.to_thread(state.drain_tasks, 60.0)

    logger.info("SHUTDOWN Saving task history and analytics...")

    # Persist final task states to DB
    from app.db.task_backend_db import DatabaseTaskBackend
    from app.services.task_backend import get_task_backend

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
    except Exception as e:
        logger.warning("Failed to close analytics DB: %s", e)

    # Close Redis connections
    if REDIS_URL:
        try:
            from app.services.redis_client import close_async_redis, close_sync_redis

            await close_async_redis()
            close_sync_redis()
        except Exception as e:
            logger.warning("Failed to close Redis: %s", e)

    # Close status DB (local SQLite)
    await close_status_db()

    # Close main DB
    await close_db()

    logger.info(f"SHUTDOWN Complete (role={ROLE})")


async def _preload_models_background(models_to_load: list[str]):
    """Load models in background so the server accepts connections immediately."""
    import torch

    from app.services.model_manager import get_model

    device = "cuda" if torch.cuda.is_available() else "cpu"
    state.model_preload = {
        "status": "loading",
        "models": models_to_load,
        "current_model": None,
        "loaded": [],
        "total": len(models_to_load),
        "error": None,
    }
    logger.info(
        f"PRELOAD Loading {len(models_to_load)} model(s) on {device.upper()} in background: {', '.join(models_to_load)}"
    )

    for model_name in models_to_load:
        state.model_preload["current_model"] = model_name
        logger.info(f"PRELOAD Loading '{model_name}'...")
        try:
            await asyncio.to_thread(get_model, model_name, device)
            state.model_preload["loaded"].append(model_name)
            logger.info(
                f"PRELOAD Model '{model_name}' ready ({len(state.model_preload['loaded'])}/{len(models_to_load)})"
            )
        except Exception as e:
            logger.warning(f"PRELOAD Failed to load '{model_name}': {e}")
            state.model_preload["status"] = "error"
            state.model_preload["error"] = f"Failed to load '{model_name}': {e}"
            return

    state.model_preload["status"] = "ready"
    state.model_preload["current_model"] = None
    logger.info(f"PRELOAD All {len(models_to_load)} model(s) loaded successfully")


async def _idle_preload_loop():
    """After 5 min idle (no active tasks), preload the next most-used model.

    Sprint L10: Smart idle preloading — Forge (Sr. Backend Engineer)
    Checks every 60s. Skips if tasks are active or initial preload is running.
    Loads one model per idle cycle in priority order: base, small, medium, tiny, large.
    """
    MODEL_PRIORITY = ["base", "small", "medium", "tiny", "large"]
    IDLE_CHECK_INTERVAL = 60  # seconds between checks
    IDLE_THRESHOLD = 300  # 5 minutes of inactivity before preloading

    idle_seconds = 0

    while True:
        try:
            await asyncio.sleep(IDLE_CHECK_INTERVAL)
        except asyncio.CancelledError:
            return

        if state.shutting_down:
            return

        # Skip if initial preload still running
        if state.model_preload.get("status") == "loading":
            idle_seconds = 0
            continue

        # Skip if any tasks are active
        active = sum(1 for t in state.tasks.values() if t.get("status") not in ("done", "error", "cancelled", None))
        if active > 0:
            idle_seconds = 0
            continue

        idle_seconds += IDLE_CHECK_INTERVAL

        if idle_seconds < IDLE_THRESHOLD:
            continue

        # Find next unloaded model in priority order
        for model_name in MODEL_PRIORITY:
            key = (model_name, "cpu")
            if key not in state.loaded_models:
                try:
                    logger.info(f"IDLE_PRELOAD Starting idle preload of '{model_name}'")
                    from app.services.model_manager import get_model

                    await asyncio.to_thread(get_model, model_name, "cpu")
                    logger.info(f"IDLE_PRELOAD Loaded '{model_name}' successfully")
                except Exception as e:
                    logger.warning(f"IDLE_PRELOAD Failed to load '{model_name}': {e}")
                break  # Only load one model per idle cycle
        else:
            # All models already loaded — stop checking
            logger.info("IDLE_PRELOAD All priority models already loaded")
            return

        # Reset idle counter after a load attempt
        idle_seconds = 0


def _apply_tuning(tuning: dict):
    """Apply auto-tuned settings to runtime config."""
    import os

    from app import config

    # Update OMP threads if auto-tuned value differs
    omp = str(tuning["omp_threads"])
    os.environ["OMP_NUM_THREADS"] = omp
    os.environ["MKL_NUM_THREADS"] = omp

    # Update concurrent task limit (respect explicit env var override)
    if config.MAX_CONCURRENT_TASKS_EXPLICIT:
        max_tasks = config.MAX_CONCURRENT_TASKS
        logger.info(f"TUNING MAX_CONCURRENT_TASKS={max_tasks} (explicit override via env var)")
    else:
        max_tasks = tuning["max_concurrent_tasks"]
        config.MAX_CONCURRENT_TASKS = max_tasks
        logger.info(f"TUNING MAX_CONCURRENT_TASKS={max_tasks} (auto-tuned)")

    logger.info(f"TUNING Applied: OMP_THREADS={omp}, MAX_TASKS={max_tasks}")


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
            "AI-powered subtitle generation service.\n\n"
            "## Stack\n"
            "**Backend:** Python 3.12 · FastAPI · Uvicorn · SQLAlchemy (async) · Alembic · SQLite · Redis (optional)\n\n"
            "**AI / Media:** faster-whisper (CTranslate2) · pyannote.audio · PyTorch · FFmpeg\n\n"
            "**Frontend:** React 19 · TypeScript · Vite 6 · Tailwind CSS v4 · Zustand · Radix UI\n\n"
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
        version="2.3.0",
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

    from app.middleware.cors import CORS_ALLOW_HEADERS, CORS_ALLOW_METHODS, get_cors_origins

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
        log_task_event(
            "system",
            "unhandled_exception",
            path=str(request.url.path),
            method=request.method,
            error_type=type(exc).__name__,
            error=str(exc),
        )
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
