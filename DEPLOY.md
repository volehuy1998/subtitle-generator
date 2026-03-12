# Deployment Guide — Ubuntu Server 24.04 (Fresh Install)

Deploy the subtitle generator with HTTPS (Let's Encrypt) on a fresh Ubuntu 24.04 host.

## Prerequisites

- Ubuntu Server 24.04 LTS (freshly installed)
- Root or sudo access
- Domain pointed to the server's IP (A record)
- Ports 80 and 443 open in firewall/security group

## Step 1: System Update & Dependencies

```bash
sudo apt-get update && sudo apt-get upgrade -y
sudo apt-get install -y python3 python3-pip python3-venv ffmpeg libsndfile1 git certbot
```

## Step 2: Clone the Repository

```bash
cd /opt
sudo git clone https://github.com/volehuy1998/subtitle-generator.git subtitle-generator
sudo chown -R $USER:$USER /opt/subtitle-generator
cd /opt/subtitle-generator
```

## Step 3: Python Virtual Environment

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install --upgrade pip
pip install -r requirements.txt
```

## Step 4: Obtain TLS Certificate

Stop any service on port 80 first, then run:

```bash
sudo certbot certonly --standalone --non-interactive --agree-tos \
  --email admin@openlabs.club -d openlabs.club
```

Certificates will be saved to:
- `/etc/letsencrypt/live/openlabs.club/fullchain.pem`
- `/etc/letsencrypt/live/openlabs.club/privkey.pem`

> **Note:** Replace `openlabs.club` with your domain if different. Certbot auto-renewal is configured via systemd timer.

## Step 5: Create Required Directories

```bash
mkdir -p uploads outputs logs
```

## Step 6: Open Firewall Ports (if ufw is enabled)

```bash
sudo ufw allow 80/tcp
sudo ufw allow 443/tcp
```

## Step 7: Create systemd Service

```bash
sudo tee /etc/systemd/system/subtitle-generator.service > /dev/null <<'EOF'
[Unit]
Description=Subtitle Generator Web Service
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

> **Note:** Runs as root because ports 80 and 443 are privileged. For production hardening, consider using `CAP_NET_BIND_SERVICE` or a reverse proxy instead.

## Step 8: Start the Service

```bash
sudo systemctl daemon-reload
sudo systemctl enable subtitle-generator
sudo systemctl start subtitle-generator
```

## Step 9: Verify

```bash
# Check service status
sudo systemctl status subtitle-generator

# Test HTTPS
curl -s https://openlabs.club/health

# Test HTTP -> HTTPS redirect
curl -s -o /dev/null -w "%{http_code}" http://openlabs.club/
# Should return 301
```

## Environment Variables (Optional)

Set these in the `[Service]` section of the systemd unit file:

```ini
Environment=API_KEYS=key1,key2
Environment=HF_TOKEN=hf_xxxxx
Environment=PRELOAD_MODEL=base
Environment=FILE_RETENTION_HOURS=24
Environment=ENABLE_COMPRESSION=true
```

## Useful Commands

```bash
# View logs
sudo journalctl -u subtitle-generator -f

# Restart service
sudo systemctl restart subtitle-generator

# Stop service
sudo systemctl stop subtitle-generator

# Check certificate expiry
sudo certbot certificates

# Manually renew certificate
sudo certbot renew
```

## Quick Deploy Script

For convenience, run all steps in one go on a fresh Ubuntu 24.04 host:

```bash
#!/bin/bash
set -e

DOMAIN="openlabs.club"
EMAIL="admin@openlabs.club"
REPO_URL="https://github.com/volehuy1998/subtitle-generator.git"

# System deps
sudo apt-get update && sudo apt-get upgrade -y
sudo apt-get install -y python3 python3-pip python3-venv ffmpeg libsndfile1 git certbot

# Clone
cd /opt
sudo git clone "$REPO_URL" subtitle-generator
sudo chown -R $USER:$USER /opt/subtitle-generator
cd /opt/subtitle-generator

# Python setup
python3 -m venv .venv
source .venv/bin/activate
pip install --upgrade pip
pip install -r requirements.txt

# Directories
mkdir -p uploads outputs logs

# TLS certificate
sudo certbot certonly --standalone --non-interactive --agree-tos \
  --email "$EMAIL" -d "$DOMAIN"

# systemd service
sudo tee /etc/systemd/system/subtitle-generator.service > /dev/null <<UNIT
[Unit]
Description=Subtitle Generator Web Service
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
