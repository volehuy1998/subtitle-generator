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

# Fall back to stdout logging if logs dir is not writable
if [ -d "logs" ] && [ ! -w "logs" ]; then
    echo "WARN: Falling back to stdout-only logging (logs/ not writable)"
    export LOG_OUTPUT=stdout
fi

# Run database migrations (ignore errors if alembic not configured)
python -m alembic upgrade head 2>/dev/null

# Start uvicorn
exec python -m uvicorn app.main:app \
    --host 0.0.0.0 \
    --port 8000 \
    --workers 1 \
    --timeout-keep-alive 75 \
    --access-log \
    --log-level info
