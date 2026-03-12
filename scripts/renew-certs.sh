#!/bin/bash
# Called by certbot after successful renewal.
# Copies new certs to the project directory and restarts the service.
set -e

DEST=/home/claude-user/subtitle-generator

# Read DOMAIN from the project .env file if present; fall back to env var.
if [[ -f "$DEST/.env" ]]; then
  DOMAIN="${DOMAIN:-$(grep -E '^DOMAIN=' "$DEST/.env" | cut -d= -f2- | tr -d '[:space:]"'"'"')}"
fi

if [[ -z "$DOMAIN" ]]; then
  echo "[$(date)] ERROR: DOMAIN not set — cannot locate certbot cert directory" >&2
  exit 1
fi

CERT_DIR="/etc/letsencrypt/live/$DOMAIN"

cp "$CERT_DIR/fullchain.pem" "$DEST/cert.pem"
cp "$CERT_DIR/privkey.pem"   "$DEST/privkey.pem"

# Fix ownership so the app user can read the certs.
APP_USER=$(stat -c '%U' "$DEST")
chown "$APP_USER:$APP_USER" "$DEST/cert.pem" "$DEST/privkey.pem"

# Restart whichever runtime is active (systemd takes priority over Docker).
if systemctl is-active --quiet subforge 2>/dev/null; then
  systemctl reload-or-restart subforge
elif [[ -f "$DEST/docker-compose.yml" ]]; then
  DOMAIN="$DOMAIN" docker compose -f "$DEST/docker-compose.yml" \
    --profile cpu --profile gpu restart 2>/dev/null || true
fi

echo "[$(date)] Cert renewal hook completed for $DOMAIN"
