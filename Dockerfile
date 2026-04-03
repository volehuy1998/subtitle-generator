# SubForge — multi-stage Docker build
# Stage 1: Build frontend + install Python deps
FROM python:3.12-slim AS builder

RUN apt-get update && apt-get install -y --no-install-recommends \
    curl && rm -rf /var/lib/apt/lists/*
RUN curl -fsSL https://deb.nodesource.com/setup_20.x | bash - \
    && apt-get install -y --no-install-recommends nodejs \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /build

COPY requirements.txt .
RUN pip install --no-cache-dir --prefix=/install -r requirements.txt

COPY frontend/package*.json frontend/
RUN cd frontend && npm ci --ignore-scripts
COPY frontend/ frontend/
RUN cd frontend && npm run build

# Stage 2: Minimal runtime image
FROM python:3.12-slim AS runtime

ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1

RUN apt-get update && apt-get install -y --no-install-recommends \
    ffmpeg libsndfile1 curl \
    && rm -rf /var/lib/apt/lists/*

RUN groupadd -r appuser && useradd -r -g appuser -d /app -s /sbin/nologin appuser
WORKDIR /app

COPY --from=builder /install /usr/local
COPY app/ app/
COPY main.py entrypoint.sh alembic.ini ./
COPY alembic/ alembic/
COPY templates/ templates/
COPY --from=builder /build/frontend/dist frontend/dist/

RUN mkdir -p uploads outputs logs \
    && chmod +x entrypoint.sh \
    && chown -R appuser:appuser /app

USER appuser
EXPOSE 8000

HEALTHCHECK --interval=30s --timeout=5s --start-period=30s --retries=3 \
    CMD curl -f http://localhost:8000/health/live || exit 1

ENTRYPOINT ["./entrypoint.sh"]
