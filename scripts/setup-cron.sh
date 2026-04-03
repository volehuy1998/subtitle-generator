#!/usr/bin/env bash
# Install cron jobs for SubForge server maintenance.
# Run once after deployment (idempotent -- safe to re-run).
# -- Harbor (DevOps Engineer)
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"

log() { echo "[setup-cron] $*"; }

CRON_MARKER="# subforge-managed"
CRON_JOBS=$(cat <<EOF
# -- SubForge scheduled tasks ${CRON_MARKER}
# Cert renewal: twice daily (certbot skips if not due)
15 2,14 * * * ${SCRIPT_DIR}/renew-certs.sh >> /var/log/subforge-cert-renewal.log 2>&1 ${CRON_MARKER}
# Log rotation: daily at 3am
0 3 * * * /usr/sbin/logrotate /etc/logrotate.conf --state /var/lib/logrotate/status >> /dev/null 2>&1 ${CRON_MARKER}
# Temp file cleanup: daily at 4am (uploads/outputs older than FILE_RETENTION_HOURS)
0 4 * * * find ${REPO_ROOT}/uploads ${REPO_ROOT}/outputs -type f -mtime +1 -delete >> /var/log/subforge-cleanup.log 2>&1 ${CRON_MARKER}
EOF
)

# Remove any existing subforge cron entries, then append fresh ones
EXISTING_CRON=$(crontab -l 2>/dev/null || true)
FILTERED_CRON=$(echo "$EXISTING_CRON" | grep -v "$CRON_MARKER" || true)
echo "${FILTERED_CRON}
${CRON_JOBS}" | crontab -

log "Cron jobs installed:"
crontab -l | grep "$CRON_MARKER"
log "Done"
