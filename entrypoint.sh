#!/bin/sh
# Entrypoint script for subtitle-generator container.
# When Docker creates host directories for bind mounts, they default to root:root 0755,
# which prevents the non-root appuser from writing to them.
# This script detects unwritable directories and falls back to stdout-only logging.

for dir in uploads outputs logs; do
    if [ -d "$dir" ] && [ ! -w "$dir" ]; then
        echo "WARN: /app/$dir is not writable — check host directory permissions (chmod 777 or chown to match container UID)"
    fi
done

# Ensure status.db is writable if it exists (may have been created by a different UID on the host)
if [ -f "logs/status.db" ] && [ ! -w "logs/status.db" ]; then
    chmod 664 logs/status.db 2>/dev/null || true
fi

# Fall back to stdout logging if logs dir is not writable
if [ -d "logs" ] && [ ! -w "logs" ]; then
    echo "WARN: Falling back to stdout-only logging (logs/ not writable)"
    export LOG_OUTPUT=stdout
fi

# Run database migrations (ignore errors if alembic not configured)
python -m alembic upgrade head 2>/dev/null

# Start uvicorn — with TLS if certs are mounted
SSL_CERT="/certs/fullchain.pem"
SSL_KEY="/certs/privkey.pem"

if [ -f "$SSL_CERT" ] && [ -f "$SSL_KEY" ]; then
    echo "INFO: TLS certificates found — starting HTTPS on port 8000"
    # Start HTTP-to-HTTPS redirect server on port 8080 in the background
    python -c "
from starlette.applications import Starlette
from starlette.responses import RedirectResponse
from starlette.routing import Route
import uvicorn

async def redirect(request):
    url = request.url.replace(scheme='https', port=443)
    return RedirectResponse(url=str(url), status_code=301)

app = Starlette(routes=[Route('/{path:path}', redirect)])
uvicorn.run(app, host='0.0.0.0', port=8080, log_level='warning')
" &
    exec python -m uvicorn app.main:app \
        --host 0.0.0.0 \
        --port 8000 \
        --workers 1 \
        --timeout-keep-alive 75 \
        --access-log \
        --log-level info \
        --ssl-certfile "$SSL_CERT" \
        --ssl-keyfile "$SSL_KEY"
else
    echo "INFO: No TLS certificates — starting HTTP on port 8000"
    exec python -m uvicorn app.main:app \
        --host 0.0.0.0 \
        --port 8000 \
        --workers 1 \
        --timeout-keep-alive 75 \
        --access-log \
        --log-level info
fi
