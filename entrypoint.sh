#!/usr/bin/env bash
# Docker entrypoint for SubForge.
# Handles env validation, migrations, model preload, and server start.
# -- Harbor (DevOps Engineer)
set -euo pipefail

log() { echo "[entrypoint] $*"; }

# -- Writable directory checks ------------------------------------------------
for dir in uploads outputs logs; do
    if [ -d "$dir" ] && [ ! -w "$dir" ]; then
        log "WARN: /app/$dir is not writable -- check host permissions"
    fi
done

if [ -d "logs" ] && [ ! -w "logs" ]; then
    log "WARN: logs/ not writable -- falling back to stdout-only logging"
    export LOG_OUTPUT=stdout
fi

# -- Database migrations ------------------------------------------------------
if [ -n "${DATABASE_URL:-}" ]; then
    log "Running Alembic migrations..."
    python -m alembic upgrade head 2>&1 || log "WARN: Alembic migration failed (may not be configured)"
fi

# -- Model preload ------------------------------------------------------------
if [ -n "${PRELOAD_MODEL:-}" ]; then
    log "Preloading model(s): $PRELOAD_MODEL"
    python -c "
from app.services.model_manager import preload_models
preload_models('${PRELOAD_MODEL}')
" 2>&1 || log "WARN: Model preload failed -- models will load on first request"
fi

# -- Start server based on ROLE -----------------------------------------------
ROLE="${ROLE:-standalone}"
ENVIRONMENT="${ENVIRONMENT:-dev}"

case "$ROLE" in
    worker)
        log "Starting Celery worker..."
        exec celery -A app.celery_app worker \
            --loglevel=info \
            --concurrency="${MAX_CONCURRENT_TASKS:-2}"
        ;;
    web|standalone)
        UVICORN_ARGS=(
            --host 0.0.0.0
            --port "${PORT:-8000}"
            --workers 1
            --timeout-keep-alive 75
            --access-log
        )

        if [ "$ENVIRONMENT" = "prod" ]; then
            UVICORN_ARGS+=(--log-level warning)
            SSL_CERT="${SSL_CERTFILE:-/certs/fullchain.pem}"
            SSL_KEY="${SSL_KEYFILE:-/certs/privkey.pem}"
            if [ -f "$SSL_CERT" ] && [ -f "$SSL_KEY" ]; then
                log "TLS certs found -- starting HTTPS"
                UVICORN_ARGS+=(--ssl-certfile "$SSL_CERT" --ssl-keyfile "$SSL_KEY")
            fi
        else
            UVICORN_ARGS+=(--log-level info)
        fi

        log "Starting uvicorn (role=$ROLE, env=$ENVIRONMENT)..."
        exec python -m uvicorn app.main:app "${UVICORN_ARGS[@]}"
        ;;
    *)
        log "ERROR: Unknown ROLE=$ROLE (expected: standalone, web, worker)"
        exit 1
        ;;
esac
