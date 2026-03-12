# Multi-stage build for subtitle generator
# Stage 1: Base with system dependencies
FROM python:3.12-slim AS base

# Install ffmpeg and system deps
RUN apt-get update && apt-get install -y --no-install-recommends \
    ffmpeg \
    libsndfile1 \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Stage 2: Dependencies
FROM base AS deps

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Stage 3: Production image
FROM deps AS production

# Create non-root user for security
RUN groupadd -r appuser && useradd -r -g appuser -d /app -s /sbin/nologin appuser

# Copy application code
COPY . .

# Create required directories
RUN mkdir -p uploads outputs logs \
    && chown -R appuser:appuser /app

USER appuser

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=30s --retries=3 \
    CMD python -c "import urllib.request,ssl; urllib.request.urlopen('https://localhost:8000/health',context=ssl._create_unverified_context())" || python -c "import urllib.request; urllib.request.urlopen('http://localhost:8000/health')" || exit 1

EXPOSE 8000

# Entrypoint handles bind-mount permissions and starts uvicorn
ENTRYPOINT ["./entrypoint.sh"]
