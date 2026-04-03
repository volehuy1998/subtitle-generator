#!/usr/bin/env bash
# Renew TLS certificates for all SubForge domains and reload nginx.
# Called by cron (see setup-cron.sh) or manually.
# Certbot handles all domains registered under /etc/letsencrypt/renewal/.
# -- Harbor (DevOps Engineer)
set -euo pipefail

LOGFILE="/var/log/subforge-cert-renewal.log"

log() { echo "[$(date '+%Y-%m-%d %H:%M:%S')] $*" | tee -a "$LOGFILE"; }

log "Starting certificate renewal..."

if certbot renew --quiet --deploy-hook "systemctl reload nginx" 2>&1 | tee -a "$LOGFILE"; then
    log "Certificate renewal completed successfully"
else
    log "ERROR: Certificate renewal failed (exit code: $?)"
    exit 1
fi
