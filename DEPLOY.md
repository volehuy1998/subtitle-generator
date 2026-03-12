# Deployment Guide — Ubuntu Server 24.04

Deploy the subtitle generator in single-node or multi-node mode on fresh Ubuntu 24.04 hosts.

## Table of Contents

- [System Requirements](#system-requirements)
- [Common Setup (All Nodes)](#common-setup-all-nodes)
- [Mode A: Single-Node Deployment](#mode-a-single-node-deployment)
- [Mode B: Multi-Node Deployment](#mode-b-multi-node-deployment)
- [Mode C: Docker Deployment](#mode-c-docker-deployment)
- [GPU Deployment](#gpu-deployment)
- [Environment Variables Reference](#environment-variables-reference)
- [Useful Commands](#useful-commands)
- [Troubleshooting](#troubleshooting)

---

## System Requirements

### Required System Packages

| Package | Role | What breaks without it |
|---------|------|------------------------|
| **ffmpeg** | Audio extraction (video to WAV), media probing (duration/codec detection), subtitle embedding (soft mux and hard burn), video+subtitle combining | Transcription pipeline fails at audio extraction. Embed/combine features fail. Health indicator shows **yellow warning**. |
| **libsndfile1** | Audio I/O library used by faster-whisper for reading WAV/FLAC audio data | Whisper model loading or audio decoding fails with missing shared library errors |
| **python3**, **python3-pip**, **python3-venv** | Python runtime, package manager, virtual environment support | Application cannot start |
| **git** | Clone the repository, manage updates | Cannot fetch or update the codebase |
| **curl** | Health check verification, TLS debugging, Docker healthchecks | Cannot verify deployment or run Docker health probes |
| **certbot** | Obtain and renew Let's Encrypt TLS certificates | HTTPS will not work (single-node mode) |

### Optional (GPU Acceleration)

| Package | Role |
|---------|------|
| **nvidia-driver-550+** | NVIDIA GPU kernel driver |
| **cuda-toolkit-12.x** | CUDA runtime for GPU-accelerated transcription |
| **nvidia-container-toolkit** | Required for GPU passthrough in Docker |

### Minimum Hardware

| Resource | Minimum | Recommended |
|----------|---------|-------------|
| RAM | 4 GB (tiny model, CPU) | 16+ GB (medium model) |
| CPU | 2 cores | 8+ cores |
| Disk | 10 GB free | 50+ GB (for uploads/outputs) |
| GPU (optional) | NVIDIA with 2+ GB VRAM | NVIDIA with 6+ GB VRAM (large model) |

---

## Common Setup (All Nodes)

These steps apply to every server, regardless of deployment mode.

### Step 1: System Update & Dependencies

```bash
sudo apt-get update && sudo apt-get upgrade -y
sudo apt-get install -y python3 python3-pip python3-venv ffmpeg libsndfile1 git curl curl
```

### Step 2: Clone the Repository

```bash
cd /opt
sudo git clone https://github.com/volehuy1998/subtitle-generator.git subtitle-generator
sudo chown -R $USER:$USER /opt/subtitle-generator
cd /opt/subtitle-generator
```

### Step 3: Python Virtual Environment

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install --upgrade pip
pip install -r requirements.txt
```

### Step 4: Create Required Directories

```bash
mkdir -p uploads outputs logs
```

### Step 5: Open Firewall Ports (if ufw is enabled)

```bash
sudo ufw allow 80/tcp
sudo ufw allow 443/tcp
```

---

## Mode A: Single-Node Deployment

Everything runs on one server: web app, transcription, and storage. This is the default mode — no Redis, S3, or Celery needed.

### A1. Obtain TLS Certificate

```bash
sudo apt-get install -y certbot
sudo certbot certonly --standalone --non-interactive --agree-tos \
  --email admin@openlabs.club -d openlabs.club
```

### A2. Create systemd Service

```bash
sudo tee /etc/systemd/system/subtitle-generator.service > /dev/null <<'EOF'
[Unit]
Description=Subtitle Generator (Standalone)
After=network.target

[Service]
Type=simple
User=root
WorkingDirectory=/opt/subtitle-generator
ExecStart=/opt/subtitle-generator/.venv/bin/python main.py
Restart=on-failure
RestartSec=5
Environment=PYTHONUNBUFFERED=1

[Install]
WantedBy=multi-user.target
EOF
```

### A3. Start & Verify

```bash
sudo systemctl daemon-reload
sudo systemctl enable --now subtitle-generator

# Verify
curl -s https://openlabs.club/health
curl -s -o /dev/null -w "%{http_code}" http://openlabs.club/  # Should return 301
```

### Quick Deploy Script (Single-Node)

```bash
#!/bin/bash
set -e

DOMAIN="openlabs.club"
EMAIL="admin@openlabs.club"
REPO_URL="https://github.com/volehuy1998/subtitle-generator.git"

sudo apt-get update && sudo apt-get upgrade -y
sudo apt-get install -y python3 python3-pip python3-venv ffmpeg libsndfile1 git curl curl certbot

cd /opt
sudo git clone "$REPO_URL" subtitle-generator
sudo chown -R $USER:$USER /opt/subtitle-generator
cd /opt/subtitle-generator

python3 -m venv .venv
source .venv/bin/activate
pip install --upgrade pip
pip install -r requirements.txt

mkdir -p uploads outputs logs

sudo certbot certonly --standalone --non-interactive --agree-tos \
  --email "$EMAIL" -d "$DOMAIN"

sudo tee /etc/systemd/system/subtitle-generator.service > /dev/null <<UNIT
[Unit]
Description=Subtitle Generator (Standalone)
After=network.target

[Service]
Type=simple
User=root
WorkingDirectory=/opt/subtitle-generator
ExecStart=/opt/subtitle-generator/.venv/bin/python main.py
Restart=on-failure
RestartSec=5
Environment=PYTHONUNBUFFERED=1

[Install]
WantedBy=multi-user.target
UNIT

sudo systemctl daemon-reload
sudo systemctl enable --now subtitle-generator
echo "Deployed! Verify: curl -s https://$DOMAIN/health"
```

---

## Mode B: Multi-Node Deployment

Split the service across multiple servers for horizontal scaling:

```
                 ┌───────────┐
                 │   NGINX   │  ← TLS termination + load balancing
                 │ (1 server)│
                 └─────┬─────┘
                       │
          ┌────────────┼────────────┐
          │                         │
   ┌──────▼──────┐          ┌──────▼──────┐
   │ Web Server 1│   ...    │ Web Server N│  ← FastAPI (ROLE=web)
   └──────┬──────┘          └──────┬──────┘
          │                         │
   ┌──────▼─────────────────────────▼──────┐
   │           Redis + PostgreSQL           │  ← Shared state
   │           MinIO / S3                   │  ← Shared storage
   └──────┬─────────────────────────┬──────┘
          │                         │
   ┌──────▼──────┐          ┌──────▼──────┐
   │  Worker 1   │   ...    │  Worker N   │  ← Celery (ROLE=worker)
   └─────────────┘          └─────────────┘
```

**Server roles:**

| Role | What it does | Env var |
|------|-------------|---------|
| **Infrastructure** | Redis, PostgreSQL, MinIO | N/A (services) |
| **Web server** | Accepts uploads, serves UI, SSE/WebSocket | `ROLE=web` |
| **Worker** | Runs Celery, loads Whisper models, transcribes | `ROLE=worker` |
| **Load balancer** | NGINX with TLS termination | N/A (NGINX config) |

### B1. Infrastructure Server

Install Redis, PostgreSQL, and MinIO on one dedicated server (or use managed services).

```bash
# Redis
sudo apt-get install -y redis-server
sudo systemctl enable --now redis-server

# PostgreSQL
sudo apt-get install -y postgresql postgresql-contrib
sudo -u postgres createuser --superuser subtitle_user
sudo -u postgres createdb subtitle_generator -O subtitle_user
sudo -u postgres psql -c "ALTER USER subtitle_user PASSWORD 'your_secure_password';"

# MinIO (S3-compatible storage)
wget https://dl.min.io/server/minio/release/linux-amd64/minio
chmod +x minio
sudo mv minio /usr/local/bin/

sudo mkdir -p /data/minio
sudo tee /etc/systemd/system/minio.service > /dev/null <<'EOF'
[Unit]
Description=MinIO Object Storage
After=network.target

[Service]
Type=simple
User=root
Environment=MINIO_ROOT_USER=minioadmin
Environment=MINIO_ROOT_PASSWORD=minioadmin123
ExecStart=/usr/local/bin/minio server /data/minio --console-address ":9001"
Restart=on-failure

[Install]
WantedBy=multi-user.target
EOF

sudo systemctl daemon-reload
sudo systemctl enable --now minio
```

> **Note:** Replace passwords with secure values. For production, use managed services (AWS RDS, ElastiCache, S3).

Make note of your infrastructure server's IP (e.g., `10.0.1.10`). All other servers connect to it.

### B2. Web Server(s)

Run [Common Setup](#common-setup-all-nodes) first, then:

```bash
sudo tee /etc/systemd/system/subtitle-generator.service > /dev/null <<'EOF'
[Unit]
Description=Subtitle Generator (Web)
After=network.target

[Service]
Type=simple
User=root
WorkingDirectory=/opt/subtitle-generator
ExecStart=/opt/subtitle-generator/.venv/bin/uvicorn app.main:app --host 0.0.0.0 --port 8000
Restart=on-failure
RestartSec=5
Environment=PYTHONUNBUFFERED=1
Environment=ROLE=web
Environment=REDIS_URL=redis://10.0.1.10:6379/0
Environment=CELERY_BROKER_URL=redis://10.0.1.10:6379/0
Environment=DATABASE_URL=postgresql+asyncpg://subtitle_user:your_secure_password@10.0.1.10:5432/subtitle_generator
Environment=STORAGE_BACKEND=s3
Environment=S3_ENDPOINT_URL=http://10.0.1.10:9000
Environment=S3_BUCKET_NAME=subtitle-generator
Environment=S3_ACCESS_KEY=minioadmin
Environment=S3_SECRET_KEY=minioadmin123

[Install]
WantedBy=multi-user.target
EOF

sudo systemctl daemon-reload
sudo systemctl enable --now subtitle-generator
```

> Web servers listen on port 8000 (plain HTTP). TLS is handled by the NGINX load balancer.

### B3. Worker Server(s)

Run [Common Setup](#common-setup-all-nodes) first, then:

```bash
sudo tee /etc/systemd/system/subtitle-worker.service > /dev/null <<'EOF'
[Unit]
Description=Subtitle Generator (Celery Worker)
After=network.target

[Service]
Type=simple
User=root
WorkingDirectory=/opt/subtitle-generator
ExecStart=/opt/subtitle-generator/.venv/bin/celery -A app.celery_app worker --concurrency=1 --loglevel=info
Restart=on-failure
RestartSec=5
Environment=PYTHONUNBUFFERED=1
Environment=ROLE=worker
Environment=REDIS_URL=redis://10.0.1.10:6379/0
Environment=CELERY_BROKER_URL=redis://10.0.1.10:6379/0
Environment=DATABASE_URL=postgresql+asyncpg://subtitle_user:your_secure_password@10.0.1.10:5432/subtitle_generator
Environment=STORAGE_BACKEND=s3
Environment=S3_ENDPOINT_URL=http://10.0.1.10:9000
Environment=S3_BUCKET_NAME=subtitle-generator
Environment=S3_ACCESS_KEY=minioadmin
Environment=S3_SECRET_KEY=minioadmin123
Environment=PRELOAD_MODEL=medium

[Install]
WantedBy=multi-user.target
EOF

sudo systemctl daemon-reload
sudo systemctl enable --now subtitle-worker
```

> **Concurrency=1** because faster-whisper is not multi-worker safe. For GPU workers, deploy one worker per GPU. For CPU workers, you can increase `--concurrency` to match `MAX_CONCURRENT_TASKS`.

### B4. NGINX Load Balancer

Install on a dedicated server (or the infrastructure server):

```bash
sudo apt-get install -y nginx certbot python3-certbot-nginx

# Obtain TLS certificate
sudo certbot certonly --standalone --non-interactive --agree-tos \
  --email admin@openlabs.club -d openlabs.club
```

Create the NGINX config:

```bash
sudo tee /etc/nginx/sites-available/subtitle-generator > /dev/null <<'EOF'
upstream web_servers {
    # Add all web server IPs here
    server 10.0.1.20:8000;
    server 10.0.1.21:8000;
    # server 10.0.1.22:8000;  # add more as needed
}

server {
    listen 80;
    server_name openlabs.club;
    return 301 https://$host$request_uri;
}

server {
    listen 443 ssl http2;
    server_name openlabs.club;

    ssl_certificate /etc/letsencrypt/live/openlabs.club/fullchain.pem;
    ssl_certificate_key /etc/letsencrypt/live/openlabs.club/privkey.pem;

    # SSL settings
    ssl_protocols TLSv1.2 TLSv1.3;
    ssl_ciphers HIGH:!aNULL:!MD5;
    ssl_prefer_server_ciphers on;
    ssl_session_cache shared:SSL:10m;

    # Upload size limit (match MAX_FILE_SIZE = 2GB)
    client_max_body_size 2g;

    # Proxy timeouts (transcription can take a long time)
    proxy_read_timeout 3600s;
    proxy_send_timeout 3600s;
    proxy_connect_timeout 30s;

    location / {
        proxy_pass http://web_servers;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }

    # SSE — disable buffering
    location /events/ {
        proxy_pass http://web_servers;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        proxy_buffering off;
        proxy_cache off;
        proxy_read_timeout 3600s;
    }

    # WebSocket
    location /ws/ {
        proxy_pass http://web_servers;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection "upgrade";
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        proxy_read_timeout 3600s;
    }
}
EOF

sudo ln -sf /etc/nginx/sites-available/subtitle-generator /etc/nginx/sites-enabled/
sudo rm -f /etc/nginx/sites-enabled/default
sudo nginx -t && sudo systemctl reload nginx
```

### B5. Verify Multi-Node Deployment

```bash
# From any machine:
curl -s https://openlabs.club/health

# Check worker status:
curl -s https://openlabs.club/api/system/info | python3 -m json.tool

# Monitor Celery workers (from any worker node):
cd /opt/subtitle-generator && source .venv/bin/activate
celery -A app.celery_app inspect active
celery -A app.celery_app inspect stats
```

### Quick Deploy Scripts (Multi-Node)

#### Infrastructure Node

```bash
#!/bin/bash
set -e
sudo apt-get update && sudo apt-get upgrade -y
sudo apt-get install -y redis-server postgresql postgresql-contrib wget

# Redis
sudo systemctl enable --now redis-server
# Allow remote connections
sudo sed -i 's/^bind 127.0.0.1/bind 0.0.0.0/' /etc/redis/redis.conf
sudo systemctl restart redis-server

# PostgreSQL
sudo -u postgres createuser --superuser subtitle_user 2>/dev/null || true
sudo -u postgres createdb subtitle_generator -O subtitle_user 2>/dev/null || true
sudo -u postgres psql -c "ALTER USER subtitle_user PASSWORD 'your_secure_password';"
# Allow remote connections
echo "host all all 0.0.0.0/0 md5" | sudo tee -a /etc/postgresql/*/main/pg_hba.conf
sudo sed -i "s/#listen_addresses = 'localhost'/listen_addresses = '*'/" /etc/postgresql/*/main/postgresql.conf
sudo systemctl restart postgresql

# MinIO
wget -q https://dl.min.io/server/minio/release/linux-amd64/minio
chmod +x minio && sudo mv minio /usr/local/bin/
sudo mkdir -p /data/minio
sudo MINIO_ROOT_USER=minioadmin MINIO_ROOT_PASSWORD=minioadmin123 \
  /usr/local/bin/minio server /data/minio --console-address ":9001" &

echo "Infrastructure ready! Redis=6379, PostgreSQL=5432, MinIO=9000"
```

#### Web Node

```bash
#!/bin/bash
set -e
INFRA_IP="${1:?Usage: $0 <infrastructure-ip>}"
REPO_URL="https://github.com/volehuy1998/subtitle-generator.git"

sudo apt-get update && sudo apt-get upgrade -y
sudo apt-get install -y python3 python3-pip python3-venv ffmpeg libsndfile1 git curl

cd /opt
sudo git clone "$REPO_URL" subtitle-generator 2>/dev/null || true
sudo chown -R $USER:$USER /opt/subtitle-generator
cd /opt/subtitle-generator

python3 -m venv .venv
source .venv/bin/activate
pip install --upgrade pip && pip install -r requirements.txt
mkdir -p uploads outputs logs

sudo tee /etc/systemd/system/subtitle-generator.service > /dev/null <<UNIT
[Unit]
Description=Subtitle Generator (Web)
After=network.target
[Service]
Type=simple
User=root
WorkingDirectory=/opt/subtitle-generator
ExecStart=/opt/subtitle-generator/.venv/bin/uvicorn app.main:app --host 0.0.0.0 --port 8000
Restart=on-failure
RestartSec=5
Environment=PYTHONUNBUFFERED=1
Environment=ROLE=web
Environment=REDIS_URL=redis://${INFRA_IP}:6379/0
Environment=CELERY_BROKER_URL=redis://${INFRA_IP}:6379/0
Environment=DATABASE_URL=postgresql+asyncpg://subtitle_user:your_secure_password@${INFRA_IP}:5432/subtitle_generator
Environment=STORAGE_BACKEND=s3
Environment=S3_ENDPOINT_URL=http://${INFRA_IP}:9000
Environment=S3_BUCKET_NAME=subtitle-generator
Environment=S3_ACCESS_KEY=minioadmin
Environment=S3_SECRET_KEY=minioadmin123
[Install]
WantedBy=multi-user.target
UNIT

sudo systemctl daemon-reload
sudo systemctl enable --now subtitle-generator
echo "Web server ready on port 8000"
```

#### Worker Node

```bash
#!/bin/bash
set -e
INFRA_IP="${1:?Usage: $0 <infrastructure-ip>}"
REPO_URL="https://github.com/volehuy1998/subtitle-generator.git"

sudo apt-get update && sudo apt-get upgrade -y
sudo apt-get install -y python3 python3-pip python3-venv ffmpeg libsndfile1 git curl

cd /opt
sudo git clone "$REPO_URL" subtitle-generator 2>/dev/null || true
sudo chown -R $USER:$USER /opt/subtitle-generator
cd /opt/subtitle-generator

python3 -m venv .venv
source .venv/bin/activate
pip install --upgrade pip && pip install -r requirements.txt
mkdir -p uploads outputs logs

sudo tee /etc/systemd/system/subtitle-worker.service > /dev/null <<UNIT
[Unit]
Description=Subtitle Generator (Celery Worker)
After=network.target
[Service]
Type=simple
User=root
WorkingDirectory=/opt/subtitle-generator
ExecStart=/opt/subtitle-generator/.venv/bin/celery -A app.celery_app worker --concurrency=1 --loglevel=info
Restart=on-failure
RestartSec=5
Environment=PYTHONUNBUFFERED=1
Environment=ROLE=worker
Environment=REDIS_URL=redis://${INFRA_IP}:6379/0
Environment=CELERY_BROKER_URL=redis://${INFRA_IP}:6379/0
Environment=DATABASE_URL=postgresql+asyncpg://subtitle_user:your_secure_password@${INFRA_IP}:5432/subtitle_generator
Environment=STORAGE_BACKEND=s3
Environment=S3_ENDPOINT_URL=http://${INFRA_IP}:9000
Environment=S3_BUCKET_NAME=subtitle-generator
Environment=S3_ACCESS_KEY=minioadmin
Environment=S3_SECRET_KEY=minioadmin123
Environment=PRELOAD_MODEL=medium
[Install]
WantedBy=multi-user.target
UNIT

sudo systemctl daemon-reload
sudo systemctl enable --now subtitle-worker
echo "Worker ready! Celery consuming from redis://${INFRA_IP}:6379/0"
```

---

## Mode C: Docker Deployment

The simplest deployment option. Both CPU and GPU Dockerfiles are included.

### CPU Mode

```bash
docker compose --profile cpu up --build -d
```

This starts the app on port 8000 with a PostgreSQL database. The Dockerfile installs ffmpeg and libsndfile1 automatically.

### GPU Mode

Requires the [NVIDIA Container Toolkit](https://docs.nvidia.com/datacenter/cloud-native/container-toolkit/latest/install-guide.html):

```bash
# Install NVIDIA Container Toolkit (Ubuntu)
curl -fsSL https://nvidia.github.io/libnvidia-container/gpgkey | sudo gpg --dearmor -o /usr/share/keyrings/nvidia-container-toolkit-keyring.gpg
curl -s -L https://nvidia.github.io/libnvidia-container/stable/deb/nvidia-container-toolkit.list | \
  sed 's#deb https://#deb [signed-by=/usr/share/keyrings/nvidia-container-toolkit-keyring.gpg] https://#g' | \
  sudo tee /etc/apt/sources.list.d/nvidia-container-toolkit.list
sudo apt-get update && sudo apt-get install -y nvidia-container-toolkit
sudo nvidia-ctk runtime configure --runtime=docker
sudo systemctl restart docker

# Start with GPU
docker compose --profile gpu up --build -d
```

### Verify Docker Deployment

```bash
curl -s http://localhost:8000/health | python3 -m json.tool
```

The health response should show `"status": "healthy"` with `"ffmpeg_ok": true`.

---

## GPU Deployment

For bare-metal GPU deployments (non-Docker), install NVIDIA drivers and CUDA before the common setup:

```bash
# Install NVIDIA driver (Ubuntu 24.04)
sudo apt-get install -y nvidia-driver-550

# Reboot to load the driver
sudo reboot

# Verify GPU is detected
nvidia-smi

# Install CUDA toolkit (needed by PyTorch)
sudo apt-get install -y nvidia-cuda-toolkit
```

Then proceed with the [Common Setup](#common-setup-all-nodes). The application auto-detects CUDA at startup and selects GPU mode. The startup log will show:

```
GPU:             NVIDIA GeForce RTX 4090 | 24.0GB total, 23.5GB free
TUNING:
  Device:        cuda
```

If GPU is not detected, the application falls back to CPU mode automatically.

---

## Environment Variables Reference

### Application

| Variable | Purpose | Default |
|----------|---------|---------|
| `ROLE` | Server role: `standalone`, `web`, or `worker` | `standalone` |
| `API_KEYS` | Comma-separated API keys (auth disabled if empty) | empty |
| `HF_TOKEN` | Hugging Face token for model downloads | empty |
| `PRELOAD_MODEL` | Preload whisper model at startup (tiny/base/small/medium/large) | empty |
| `FILE_RETENTION_HOURS` | Auto-cleanup retention period | `24` |
| `ENABLE_COMPRESSION` | GZip response compression | `true` |

### Infrastructure (Multi-Node Only)

| Variable | Purpose | Default |
|----------|---------|---------|
| `REDIS_URL` | Redis connection URL | empty (disabled) |
| `CELERY_BROKER_URL` | Celery broker URL (defaults to REDIS_URL) | empty |
| `DATABASE_URL` | PostgreSQL connection URL | SQLite (local) |
| `STORAGE_BACKEND` | `local` or `s3` | `local` |
| `S3_ENDPOINT_URL` | S3/MinIO endpoint | empty (AWS S3) |
| `S3_BUCKET_NAME` | S3 bucket name | `subtitle-generator` |
| `S3_ACCESS_KEY` | S3 access key | empty |
| `S3_SECRET_KEY` | S3 secret key | empty |
| `S3_REGION` | S3 region | `us-east-1` |

---

## Useful Commands

```bash
# View logs (systemd)
sudo journalctl -u subtitle-generator -f
sudo journalctl -u subtitle-worker -f

# Restart services
sudo systemctl restart subtitle-generator
sudo systemctl restart subtitle-worker

# Check certificate expiry
sudo certbot certificates

# Manually renew certificate
sudo certbot renew

# Celery worker inspection (from worker node)
cd /opt/subtitle-generator && source .venv/bin/activate
celery -A app.celery_app inspect active     # active tasks
celery -A app.celery_app inspect stats      # worker stats
celery -A app.celery_app inspect reserved   # queued tasks

# Redis monitoring
redis-cli -h 10.0.1.10 monitor   # live command stream
redis-cli -h 10.0.1.10 info      # server stats
```

## Scaling Guide

| To handle more... | Do this |
|-------------------|---------|
| Concurrent users | Add more **web servers** behind NGINX |
| Transcription throughput | Add more **worker servers** |
| Storage capacity | Use AWS S3 or add MinIO nodes |
| Database load | Use managed PostgreSQL (RDS) with read replicas |
| Redis reliability | Deploy Redis Sentinel or Redis Cluster |

## Troubleshooting

### Yellow Warning Indicator in Dashboard

**Symptom**: The health status shows a yellow warning light instead of green "Healthy".

**Cause**: The health endpoint checks for ffmpeg availability using `shutil.which("ffmpeg")`. If ffmpeg is not installed or not on the system PATH, it returns `"status": "warning"` with `"ffmpeg_ok": false`.

**Fix**:
```bash
# Install ffmpeg
sudo apt-get update && sudo apt-get install -y ffmpeg

# Verify
ffmpeg -version
```

No restart is needed — the next health check will detect ffmpeg automatically.

### Transcription Fails at Audio Extraction

**Symptom**: Upload completes but task fails with an error about audio extraction or ffmpeg.

**Cause**: ffmpeg is not installed. The pipeline uses ffmpeg to convert uploaded video/audio to WAV format before passing to Whisper.

**Fix**: Install ffmpeg as shown above.

### Model Loading Fails with Shared Library Error

**Symptom**: Error mentioning `libsndfile.so` or similar shared library not found.

**Fix**:
```bash
sudo apt-get install -y libsndfile1
```

### TLS Certificate Issues

**Symptom**: HTTPS not working, browser shows certificate warnings, or server won't start with TLS enabled.

**Checks**:
```bash
# Check if certificates exist
sudo ls -la /etc/letsencrypt/live/YOUR_DOMAIN/

# Check certificate expiry
sudo certbot certificates

# Renew if expired
sudo certbot renew

# Test without TLS (for debugging)
HTTPS_REDIRECT=false python3 -m uvicorn app.main:app --host 0.0.0.0 --port 8000
```

If certificates don't exist yet, obtain them:
```bash
sudo certbot certonly --standalone -d YOUR_DOMAIN --non-interactive --agree-tos -m your@email.com
```

### GPU Not Detected

**Symptom**: App starts but uses CPU even though a GPU is installed.

**Checks**:
```bash
# Verify NVIDIA driver
nvidia-smi

# Check CUDA availability in Python
source /opt/subtitle-generator/.venv/bin/activate
python3 -c "import torch; print(torch.cuda.is_available())"
```

If `nvidia-smi` fails, install the driver:
```bash
sudo apt-get install -y nvidia-driver-550
sudo reboot
```

If `torch.cuda.is_available()` returns False, reinstall PyTorch with CUDA:
```bash
pip install torch --index-url https://download.pytorch.org/whl/cu121
```

### Docker Container Crashes on Startup

**Symptom**: Container exits immediately or restarts in a loop.

**Checks**:
```bash
# View logs
docker compose logs subtitle-generator

# Common causes:
# 1. uploads/ or outputs/ directories not writable
mkdir -p uploads outputs logs
chmod 777 uploads outputs logs

# 2. Port already in use
sudo lsof -i :8000
```

### Verifying a Healthy Deployment

Run these checks after deployment to confirm everything is working:

```bash
# 1. Health endpoint (should return "status": "healthy")
curl -s http://localhost:8000/health | python3 -m json.tool

# 2. FFmpeg available
ffmpeg -version | head -1

# 3. Uploads directory writable
ls -la uploads/

# 4. No warning indicators
curl -s http://localhost:8000/health | grep -o '"status":"[^"]*"'
```
