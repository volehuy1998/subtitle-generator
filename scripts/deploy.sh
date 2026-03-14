#!/usr/bin/env bash
# =============================================================================
#  SubForge — automated deployment for Ubuntu Server 24.04
#  https://github.com/volehuy1998/subtitle-generator
#
#  Quick-start:
#    # Development (HTTP, no TLS):
#    sudo bash deploy.sh --mode dev
#
#    # Production (HTTPS via Let's Encrypt):
#    sudo bash deploy.sh --domain example.com --email admin@example.com
#
#    # Production via Docker:
#    sudo bash deploy.sh --domain example.com --email admin@example.com --docker
#
#    # Bring-your-own certificate (skip Let's Encrypt):
#    sudo bash deploy.sh --domain example.com \
#      --cert /path/to/fullchain.pem --key /path/to/privkey.pem
#
#  Re-running this script on an existing installation performs an in-place
#  update: pulls latest code, reinstalls pip packages, and restarts the service.
# =============================================================================
set -euo pipefail

# ── Colour helpers ────────────────────────────────────────────────────────────
if [[ -t 1 ]]; then
  R=$'\e[0;31m' G=$'\e[0;32m' Y=$'\e[1;33m' B=$'\e[0;34m' BOLD=$'\e[1m' RESET=$'\e[0m'
else
  R='' G='' Y='' B='' BOLD='' RESET=''
fi
info()    { printf '%b  info  %b %s\n'  "$B"    "$RESET" "$*"; }
ok()      { printf '%b  ok    %b %s\n'  "$G"    "$RESET" "$*"; }
warn()    { printf '%b  warn  %b %s\n'  "$Y"    "$RESET" "$*"; }
die()     { printf '%b  error %b %s\n'  "$R"    "$RESET" "$*" >&2; exit 1; }
section() { printf '\n%b━━  %s  ━━%b\n' "$BOLD" "$*"     "$RESET"; }
blank()   { echo; }

# ── Defaults ─────────────────────────────────────────────────────────────────
MODE="prod"                 # prod | dev
DOMAIN=""                   # required for prod
EMAIL=""                    # required for prod + Let's Encrypt
USE_DOCKER=0
USE_GPU=0
API_KEY=""
PRELOAD_MODEL=""
BYO_CERT=""                 # --cert: skip Let's Encrypt, use this file
BYO_KEY=""                  # --key:  skip Let's Encrypt, use this file
INSTALL_DIR="/opt/subtitle-generator"
REPO_URL="https://github.com/volehuy1998/subtitle-generator.git"
BRANCH="main"
SVC="subtitle-generator"    # systemd unit name

# ── Usage ─────────────────────────────────────────────────────────────────────
usage() {
cat <<EOF
${BOLD}SubForge deployment script for Ubuntu Server 24.04${RESET}

${BOLD}USAGE${RESET}
  sudo bash deploy.sh [OPTIONS]

${BOLD}MODE${RESET} (default: prod when --domain is given, dev otherwise)
  --mode dev          HTTP only on port 8000 — no TLS, no certificates needed
  --mode prod         HTTPS on :443 + HTTP→HTTPS redirect on :80

${BOLD}REQUIRED FOR PROD${RESET}
  --domain DOMAIN     Your public domain name (e.g. example.com)
  --email  EMAIL      Email for Let's Encrypt expiry notices

${BOLD}OPTIONAL${RESET}
  --docker            Deploy using Docker Compose (default: bare-metal systemd)
  --gpu               Install NVIDIA driver + CUDA / nvidia-container-toolkit
  --api-key KEY       Protect the API with this key (default: open access)
  --preload MODEL     Warm-start a Whisper model at startup:
                      tiny | base | small | medium | large
  --cert  FILE        Existing TLS certificate (fullchain.pem) — skips Let's Encrypt
  --key   FILE        Existing TLS private key  (privkey.pem)  — skips Let's Encrypt
  --install-dir DIR   Where to install (default: /opt/subtitle-generator)
  --branch BRANCH     Git branch to deploy (default: main)
  --repo URL          Override Git repository URL
  --help              Show this help

${BOLD}EXAMPLES${RESET}
  # Dev / localhost:
  sudo bash deploy.sh --mode dev

  # Prod, Let's Encrypt, bare-metal:
  sudo bash deploy.sh --domain example.com --email admin@example.com

  # Prod, Let's Encrypt, Docker, GPU:
  sudo bash deploy.sh --domain example.com --email admin@example.com --docker --gpu

  # Prod, bring-your-own certificate:
  sudo bash deploy.sh --domain example.com \\
    --cert /etc/ssl/certs/fullchain.pem --key /etc/ssl/private/privkey.pem

  # Update an existing installation (re-run with same arguments):
  sudo bash deploy.sh --domain example.com --email admin@example.com

EOF
exit 0
}

# ── Argument parsing ──────────────────────────────────────────────────────────
while [[ $# -gt 0 ]]; do
  case "$1" in
    --mode)        MODE="$2";          shift 2 ;;
    --domain)      DOMAIN="$2";        shift 2 ;;
    --email)       EMAIL="$2";         shift 2 ;;
    --docker)      USE_DOCKER=1;       shift   ;;
    --gpu)         USE_GPU=1;          shift   ;;
    --api-key)     API_KEY="$2";       shift 2 ;;
    --preload)     PRELOAD_MODEL="$2"; shift 2 ;;
    --cert)        BYO_CERT="$2";      shift 2 ;;
    --key)         BYO_KEY="$2";       shift 2 ;;
    --install-dir) INSTALL_DIR="$2";   shift 2 ;;
    --branch)      BRANCH="$2";        shift 2 ;;
    --repo)        REPO_URL="$2";      shift 2 ;;
    --help|-h)     usage ;;
    *) die "Unknown option: $1  (run with --help for usage)" ;;
  esac
done

# ── Validation ────────────────────────────────────────────────────────────────
[[ "$(id -u)" -eq 0 ]] || die "Run as root:  sudo bash deploy.sh ..."

# Auto-select dev mode when no domain is provided
if [[ -z "$DOMAIN" && "$MODE" == "prod" ]]; then
  warn "No --domain given — switching to --mode dev (HTTP on :8000)"
  MODE="dev"
fi

if [[ "$MODE" == "prod" ]]; then
  [[ -n "$DOMAIN" ]] || die "--domain is required for prod mode"

  if [[ -n "$BYO_CERT" || -n "$BYO_KEY" ]]; then
    # Validate bring-your-own cert
    [[ -n "$BYO_CERT" && -n "$BYO_KEY" ]] \
      || die "Provide both --cert and --key together"
    [[ -f "$BYO_CERT" ]] || die "Certificate file not found: $BYO_CERT"
    [[ -f "$BYO_KEY"  ]] || die "Key file not found: $BYO_KEY"
  else
    [[ -n "$EMAIL" ]] \
      || die "--email is required when using Let's Encrypt (or pass --cert + --key)"
  fi
fi

if [[ -n "$PRELOAD_MODEL" ]]; then
  case "$PRELOAD_MODEL" in tiny|base|small|medium|large) ;;
    *) die "--preload must be: tiny | base | small | medium | large" ;;
  esac
fi

# ── Derived paths ─────────────────────────────────────────────────────────────
CERT_DIR="/etc/letsencrypt/live/${DOMAIN}"
CERT_FILE="${CERT_DIR}/fullchain.pem"
KEY_FILE="${CERT_DIR}/privkey.pem"
if [[ -n "$BYO_CERT" ]]; then
  CERT_FILE="$BYO_CERT"
  KEY_FILE="$BYO_KEY"
fi

# ── Banner ────────────────────────────────────────────────────────────────────
blank
printf '%b' "$BOLD"
echo "  ╔══════════════════════════════════════════╗"
echo "  ║        SubForge — deployment script      ║"
echo "  ╚══════════════════════════════════════════╝"
printf '%b\n' "$RESET"
info "Mode:         $MODE"
info "Install dir:  $INSTALL_DIR"
[[ -n "$DOMAIN" ]]        && info "Domain:       $DOMAIN"
[[ "$USE_DOCKER" -eq 1 ]] && info "Engine:       Docker Compose"
[[ "$USE_DOCKER" -eq 0 ]] && info "Engine:       bare-metal systemd"
[[ "$USE_GPU" -eq 1 ]]    && info "GPU:          enabled"
[[ -n "$PRELOAD_MODEL" ]] && info "Preload:      $PRELOAD_MODEL"
[[ -n "$API_KEY" ]]       && info "API auth:     enabled"
blank

# =============================================================================
section "1 / Platform check"
# =============================================================================

if ! grep -qi 'ubuntu' /etc/os-release 2>/dev/null; then
  warn "This script targets Ubuntu 24.04. Continuing anyway…"
fi

ok "Ubuntu detected: $(. /etc/os-release && echo "$PRETTY_NAME")"

# =============================================================================
section "2 / System packages"
# =============================================================================

export DEBIAN_FRONTEND=noninteractive

info "Updating package index…"
apt-get update -qq

info "Installing core dependencies…"
apt-get install -y -qq \
  python3 python3-pip python3-venv \
  ffmpeg libsndfile1 \
  git curl ca-certificates \
  ufw

ok "Core packages installed"

# =============================================================================
section "3 / GPU packages"
# =============================================================================

if [[ "$USE_GPU" -eq 1 ]]; then
  if [[ "$USE_DOCKER" -eq 0 ]]; then
    info "Installing NVIDIA driver and CUDA toolkit (bare-metal)…"
    apt-get install -y -qq nvidia-driver-550 nvidia-cuda-toolkit || \
      warn "Could not install NVIDIA packages — driver may already be installed"
    ok "NVIDIA driver/CUDA installed (reboot may be required)"
  else
    info "Installing NVIDIA Container Toolkit for Docker GPU passthrough…"
    # Add NVIDIA Container Toolkit repo
    curl -fsSL https://nvidia.github.io/libnvidia-container/gpgkey \
      | gpg --dearmor -o /usr/share/keyrings/nvidia-container-toolkit-keyring.gpg 2>/dev/null
    curl -sL https://nvidia.github.io/libnvidia-container/stable/deb/nvidia-container-toolkit.list \
      | sed 's#deb https://#deb [signed-by=/usr/share/keyrings/nvidia-container-toolkit-keyring.gpg] https://#g' \
      | tee /etc/apt/sources.list.d/nvidia-container-toolkit.list > /dev/null
    apt-get update -qq
    apt-get install -y -qq nvidia-container-toolkit
    nvidia-ctk runtime configure --runtime=docker 2>/dev/null || true
    ok "NVIDIA Container Toolkit installed"
  fi
else
  info "Skipping GPU packages (pass --gpu to install)"
fi

# =============================================================================
section "4 / Docker"
# =============================================================================

if [[ "$USE_DOCKER" -eq 1 ]]; then
  if command -v docker &>/dev/null; then
    ok "Docker already installed: $(docker --version)"
  else
    info "Installing Docker Engine…"
    install -m 0755 -d /etc/apt/keyrings
    curl -fsSL https://download.docker.com/linux/ubuntu/gpg \
      | gpg --dearmor -o /etc/apt/keyrings/docker.gpg
    chmod a+r /etc/apt/keyrings/docker.gpg
    echo \
      "deb [arch=$(dpkg --print-architecture) signed-by=/etc/apt/keyrings/docker.gpg] \
https://download.docker.com/linux/ubuntu \
$(. /etc/os-release && echo "$VERSION_CODENAME") stable" \
      | tee /etc/apt/sources.list.d/docker.list > /dev/null
    apt-get update -qq
    apt-get install -y -qq docker-ce docker-ce-cli containerd.io docker-compose-plugin
    systemctl enable --now docker
    ok "Docker installed: $(docker --version)"
  fi

  if [[ "$USE_GPU" -eq 1 ]]; then
    systemctl restart docker
    ok "Docker restarted with NVIDIA runtime"
  fi
else
  info "Skipping Docker install (pass --docker to use Docker Compose)"
fi

# =============================================================================
section "5 / Repository"
# =============================================================================

if [[ -d "$INSTALL_DIR/.git" ]]; then
  info "Repository already exists — pulling latest changes…"
  git -C "$INSTALL_DIR" fetch --quiet origin
  git -C "$INSTALL_DIR" checkout --quiet "$BRANCH"
  git -C "$INSTALL_DIR" reset --hard "origin/$BRANCH"
  ok "Repository updated to $(git -C "$INSTALL_DIR" log -1 --format='%h %s')"
else
  info "Cloning repository to ${INSTALL_DIR}…"
  git clone --quiet --branch "$BRANCH" "$REPO_URL" "$INSTALL_DIR"
  ok "Repository cloned"
fi

cd "$INSTALL_DIR"

# =============================================================================
section "6 / Firewall"
# =============================================================================

if ufw status | grep -q "Status: active"; then
  if [[ "$MODE" == "prod" ]]; then
    ufw allow 80/tcp  comment 'SubForge HTTP redirect' &>/dev/null
    ufw allow 443/tcp comment 'SubForge HTTPS'         &>/dev/null
    ok "Firewall: opened ports 80 and 443"
  else
    ufw allow 8000/tcp comment 'SubForge dev HTTP' &>/dev/null
    ok "Firewall: opened port 8000"
  fi
else
  warn "ufw not active — skipping firewall configuration"
fi

# =============================================================================
section "7 / TLS certificate"
# =============================================================================

if [[ "$MODE" == "prod" ]]; then
  if [[ -n "$BYO_CERT" ]]; then
    ok "Using provided certificate: $BYO_CERT"
  elif [[ -f "$CERT_FILE" ]]; then
    EXPIRY=$(openssl x509 -enddate -noout -in "$CERT_FILE" 2>/dev/null \
      | sed 's/notAfter=//' || echo "unknown")
    ok "Existing certificate found for $DOMAIN (expires: $EXPIRY)"
  else
    info "Obtaining Let's Encrypt certificate for ${DOMAIN}…"
    info "Port 80 must be free for the ACME challenge"

    # Temporarily stop any service using port 80
    STOPPED_SVC=""
    if systemctl is-active --quiet "$SVC" 2>/dev/null; then
      systemctl stop "$SVC"
      STOPPED_SVC="$SVC"
    fi
    if [[ "$USE_DOCKER" -eq 1 ]]; then
      docker compose -f "$INSTALL_DIR/docker-compose.yml" down 2>/dev/null || true
    fi

    apt-get install -y -qq certbot

    certbot certonly \
      --standalone \
      --non-interactive \
      --agree-tos \
      --email "$EMAIL" \
      -d "$DOMAIN"

    ok "Certificate issued and stored at $CERT_DIR"

    # Restart service if we stopped it
    [[ -n "$STOPPED_SVC" ]] && systemctl start "$STOPPED_SVC" || true

    # Install automated renewal hook
    HOOK_DIR="/etc/letsencrypt/renewal-hooks/deploy"
    mkdir -p "$HOOK_DIR"
    HOOK="$HOOK_DIR/subforge-reload.sh"
    cat > "$HOOK" <<HOOKEOF
#!/bin/bash
# Auto-generated by SubForge deploy.sh
# Called by certbot after each successful renewal
set -e
DOMAIN="$DOMAIN"
INSTALL_DIR="$INSTALL_DIR"
USE_DOCKER="$USE_DOCKER"

if [[ "\$USE_DOCKER" -eq 1 ]]; then
  docker compose -f "\$INSTALL_DIR/docker-compose.yml" restart 2>/dev/null || true
else
  systemctl restart subforge.service 2>/dev/null || \\
    systemctl restart subtitle-generator.service 2>/dev/null || true
fi
echo "[\$(date)] SubForge cert renewal hook — service reloaded"
HOOKEOF
    chmod +x "$HOOK"
    ok "Renewal hook installed at $HOOK"
  fi
else
  info "Dev mode — skipping TLS certificate"
fi

# =============================================================================
section "8 / Deployment"
# =============================================================================

if [[ "$USE_DOCKER" -eq 1 ]]; then
  # ── Docker deployment ───────────────────────────────────────────────────────

  info "Configuring .env for Docker Compose…"

  # Build the .env file Docker Compose will read
  cat > "$INSTALL_DIR/.env" <<ENVEOF
# Generated by deploy.sh — $(date -u '+%Y-%m-%d %H:%M UTC')
DOMAIN=${DOMAIN:-localhost}
ENVIRONMENT=${MODE}
CORS_ORIGINS=${DOMAIN:+https://}${DOMAIN:-*}
API_KEYS=${API_KEY}
PRELOAD_MODEL=${PRELOAD_MODEL}
FILE_RETENTION_HOURS=24
ENABLE_COMPRESSION=true
GITHUB_TOKEN=
HF_TOKEN=
WEBHOOK_ALERT_URL=
ENVEOF
  ok ".env written"

  PROFILE="cpu"
  [[ "$USE_GPU" -eq 1 ]] && PROFILE="gpu"

  info "Building and starting Docker containers (profile: $PROFILE)…"
  info "This may take 5-15 minutes on first run (Python packages + model cache)"

  docker compose --profile "$PROFILE" pull   --quiet 2>/dev/null || true
  docker compose --profile "$PROFILE" up     --build --detach --remove-orphans

  ok "Docker containers started"

else
  # ── Bare-metal / systemd deployment ────────────────────────────────────────

  info "Setting up Python virtual environment…"
  if [[ ! -d "$INSTALL_DIR/.venv" ]]; then
    python3 -m venv "$INSTALL_DIR/.venv"
  fi

  "$INSTALL_DIR/.venv/bin/pip" install --quiet --upgrade pip
  info "Installing Python packages (may take a few minutes)…"
  "$INSTALL_DIR/.venv/bin/pip" install --quiet -r "$INSTALL_DIR/requirements.txt"
  ok "Python environment ready"

  info "Creating required directories…"
  mkdir -p "$INSTALL_DIR"/{uploads,outputs,logs}
  ok "Directories created"

  # ── Build systemd unit ──────────────────────────────────────────────────────
  info "Writing systemd service unit…"

  EXEC_ENV="Environment=ENVIRONMENT=${MODE}"
  EXEC_ENV+=$'\n'"Environment=PYTHONUNBUFFERED=1"

  if [[ "$MODE" == "prod" ]]; then
    EXEC_ENV+=$'\n'"Environment=SSL_CERTFILE=${CERT_FILE}"
    EXEC_ENV+=$'\n'"Environment=SSL_KEYFILE=${KEY_FILE}"
  fi
  [[ -n "$API_KEY" ]]       && EXEC_ENV+=$'\n'"Environment=API_KEYS=${API_KEY}"
  [[ -n "$PRELOAD_MODEL" ]] && EXEC_ENV+=$'\n'"Environment=PRELOAD_MODEL=${PRELOAD_MODEL}"

  cat > /etc/systemd/system/subforge.service <<UNIT
[Unit]
Description=SubForge — AI subtitle generator
Documentation=https://github.com/volehuy1998/subtitle-generator
After=network.target

[Service]
Type=simple
User=root
WorkingDirectory=${INSTALL_DIR}
ExecStart=${INSTALL_DIR}/.venv/bin/python main.py
Restart=on-failure
RestartSec=5
${EXEC_ENV}

[Install]
WantedBy=multi-user.target
UNIT

  systemctl daemon-reload
  systemctl enable subforge.service
  systemctl restart subforge.service
  ok "systemd service started: subforge.service"

fi

# =============================================================================
section "9 / Verification"
# =============================================================================

info "Waiting for service to become ready…"
MAX_WAIT=45
WAITED=0
HEALTH_URL="http://localhost:8000/health"
if [[ "$MODE" == "prod" ]]; then
  # Docker exposes TLS on host port 443; bare-metal binds directly to :443
  HEALTH_URL="https://localhost/health"
fi

until curl -sk --max-time 5 "$HEALTH_URL" | grep -q '"status"' 2>/dev/null; do
  sleep 2
  WAITED=$((WAITED + 2))
  if [[ $WAITED -ge $MAX_WAIT ]]; then
    warn "Service did not respond within ${MAX_WAIT}s — check logs:"
    if [[ "$USE_DOCKER" -eq 1 ]]; then
      warn "  docker compose -f ${INSTALL_DIR}/docker-compose.yml logs --tail=30"
    else
      warn "  sudo journalctl -u subforge -n 30"
    fi
    break
  fi
  printf '.'
done
echo

HEALTH=$(curl -sk --max-time 5 "$HEALTH_URL" 2>/dev/null || echo '{}')
if echo "$HEALTH" | grep -q '"status"'; then
  ok "Health check passed: $(echo "$HEALTH" | python3 -c 'import sys,json; d=json.load(sys.stdin); print(d.get("status","?"))' 2>/dev/null)"
else
  warn "Health check did not return a status — service may still be initialising"
fi

# =============================================================================
section "Deployment complete"
# =============================================================================

blank
printf '%b' "$BOLD"
echo "  ┌─────────────────────────────────────────────────────────┐"
if [[ "$MODE" == "prod" && -n "$DOMAIN" ]]; then
  printf "  │  %-55s│\n" "App:     https://$DOMAIN"
  printf "  │  %-55s│\n" "Status:  https://$DOMAIN/status"
  printf "  │  %-55s│\n" "API docs:https://$DOMAIN/docs"
else
  printf "  │  %-55s│\n" "App:     http://localhost:8000"
  printf "  │  %-55s│\n" "Status:  http://localhost:8000/status"
  printf "  │  %-55s│\n" "API docs:http://localhost:8000/docs"
fi
echo "  └─────────────────────────────────────────────────────────┘"
printf '%b\n' "$RESET"

if [[ "$USE_DOCKER" -eq 1 ]]; then
  echo "  Useful commands:"
  echo "    View logs:    docker compose -f $INSTALL_DIR/docker-compose.yml logs -f"
  echo "    Restart:      docker compose -f $INSTALL_DIR/docker-compose.yml restart"
  echo "    Update:       sudo bash $INSTALL_DIR/scripts/deploy.sh <same-args>"
else
  echo "  Useful commands:"
  echo "    View logs:    sudo journalctl -u subforge -f"
  echo "    Restart:      sudo systemctl restart subforge"
  echo "    Update:       sudo bash $INSTALL_DIR/scripts/deploy.sh <same-args>"
fi

if [[ "$MODE" == "prod" && -z "$BYO_CERT" ]]; then
  blank
  info "Let's Encrypt renews automatically via certbot.timer."
  info "To test renewal: sudo certbot renew --dry-run"
fi

if [[ "$USE_GPU" -eq 1 && "$USE_DOCKER" -eq 0 ]]; then
  blank
  warn "GPU: if this was a fresh NVIDIA driver install, reboot to load the kernel module:"
  warn "     sudo reboot"
fi

blank
ok "Done.  Deployment finished at $(date '+%Y-%m-%d %H:%M:%S %Z')"
blank
