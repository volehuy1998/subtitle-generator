#!/usr/bin/env bash
# deploy-profile.sh — Branch-aware Docker deployment.
#
# Switches to the target branch, builds, and deploys.
# No argument = production. "newui" = subdomain staging.
#
# Usage:
#   ./scripts/deploy-profile.sh              # deploy prod from PROD_BRANCH
#   ./scripts/deploy-profile.sh --tag        # deploy prod + create git tag
#   ./scripts/deploy-profile.sh newui        # deploy newui from NEWUI_BRANCH
#   ./scripts/deploy-profile.sh newui feat/x # deploy newui from specific branch
#   ./scripts/deploy-profile.sh beta         # deploy beta from BETA_BRANCH
#   ./scripts/deploy-profile.sh beta feat/y  # deploy beta from specific branch
#
# Environment:
#   PROD_BRANCH   — branch for production (default: main)
#   NEWUI_BRANCH  — branch for newui (default: current branch)
#   BETA_BRANCH   — branch for beta (default: main)
#
# — Harbor (DevOps Engineer)

set -euo pipefail

REPO_ROOT="$(cd "$(dirname "$0")/.." && pwd)"
cd "$REPO_ROOT"

# Source .env if it exists (docker compose reads it, so should we)
if [ -f .env ]; then
  set -a
  # shellcheck disable=SC1091
  . ./.env
  set +a
fi

# ── Parse arguments ──────────────────────────────────────────────────────────

PROFILE="cpu"
TAG_FLAG=false
TARGET_BRANCH=""

case "${1:-}" in
  newui)
    PROFILE="newui"
    if [ -n "${2:-}" ]; then
      TARGET_BRANCH="$2"
    elif [ -n "${NEWUI_BRANCH:-}" ]; then
      TARGET_BRANCH="$NEWUI_BRANCH"
    fi
    ;;
  beta)
    PROFILE="beta"
    if [ -n "${2:-}" ]; then
      TARGET_BRANCH="$2"
    elif [ -n "${BETA_BRANCH:-}" ]; then
      TARGET_BRANCH="$BETA_BRANCH"
    fi
    ;;
  --tag)
    TAG_FLAG=true
    ;;
  "")
    # No args = production deploy
    ;;
  *)
    # First arg could be a branch name for prod, or unknown
    if git rev-parse --verify "$1" &>/dev/null; then
      TARGET_BRANCH="$1"
      if [ "${2:-}" = "--tag" ]; then
        TAG_FLAG=true
      fi
    else
      echo "✗ Unknown argument: $1" >&2
      echo "Usage: deploy-profile.sh [newui|beta [branch]] [--tag]" >&2
      exit 1
    fi
    ;;
esac

# Default target branch based on profile
if [ -z "$TARGET_BRANCH" ]; then
  case "$PROFILE" in
    cpu)   TARGET_BRANCH="${PROD_BRANCH:-main}" ;;
    newui) TARGET_BRANCH="$(git rev-parse --abbrev-ref HEAD)" ;;
    beta)  TARGET_BRANCH="${BETA_BRANCH:-main}" ;;
  esac
fi

# ── Helpers ──────────────────────────────────────────────────────────────────

log()  { echo "▸ $*"; }
err()  { echo "✗ $*" >&2; exit 1; }

current_branch() { git rev-parse --abbrev-ref HEAD; }

save_state() {
  ORIG_BRANCH="$(current_branch)"
  if ! git diff --quiet || ! git diff --cached --quiet; then
    STASHED=true
    git stash push -m "deploy: auto-stash before deploy"
    log "Stashed uncommitted changes"
  else
    STASHED=false
  fi
}

restore_state() {
  if [ "$(current_branch)" != "$ORIG_BRANCH" ]; then
    git checkout "$ORIG_BRANCH" --quiet
    log "Restored branch: $ORIG_BRANCH"
  fi
  if [ "$STASHED" = true ]; then
    git stash pop --quiet
    log "Restored stashed changes"
  fi
}

trap restore_state EXIT

# ── Validate ─────────────────────────────────────────────────────────────────

if ! git rev-parse --verify "$TARGET_BRANCH" &>/dev/null; then
  err "Branch '$TARGET_BRANCH' does not exist"
fi

log "Profile:  $PROFILE"
log "Branch:   $TARGET_BRANCH"
log "Commit:   $(git rev-parse --short "$TARGET_BRANCH")"

# ── Checkout target branch ───────────────────────────────────────────────────

save_state

if [ "$(current_branch)" != "$TARGET_BRANCH" ]; then
  git checkout "$TARGET_BRANCH" --quiet
  log "Checked out: $TARGET_BRANCH"
fi

# ── Pull latest from remote ─────────────────────────────────────────────────

if git rev-parse --verify "origin/$TARGET_BRANCH" &>/dev/null; then
  git pull --ff-only origin "$TARGET_BRANCH" --quiet 2>/dev/null && log "Pulled latest from origin/$TARGET_BRANCH" || log "No remote changes (or not fast-forwardable)"
fi

# ── Build and deploy ─────────────────────────────────────────────────────────

log "Building Docker profile: $PROFILE"
sudo docker compose --profile "$PROFILE" up -d --build --force-recreate

# ── Health check ─────────────────────────────────────────────────────────────

case "$PROFILE" in
  cpu)   PORT=8000 ;;
  newui) PORT=8001 ;;
  beta)  PORT=8002 ;;
esac

log "Waiting for health check on port $PORT..."
for i in $(seq 1 30); do
  if curl -sf "http://127.0.0.1:$PORT/health" >/dev/null 2>&1; then
    log "Health check passed ✓"
    break
  fi
  if [ "$i" -eq 30 ]; then
    err "Health check failed after 30 attempts"
  fi
  sleep 2
done

# ── Optional: create git tag ─────────────────────────────────────────────────

if [ "$TAG_FLAG" = true ]; then
  VERSION=$(python3 -c "
import re
with open('app/main.py') as f:
    m = re.search(r'version=\"([^\"]+)\"', f.read())
    print(m.group(1) if m else 'unknown')
  ")
  TAG_NAME="v${VERSION}-prod-$(date +%Y%m%d-%H%M%S)"
  git tag -a "$TAG_NAME" -m "Production deploy: $VERSION"
  log "Tagged: $TAG_NAME"
fi

# ── Summary ──────────────────────────────────────────────────────────────────

COMMIT=$(git rev-parse --short HEAD)
log ""
log "Deploy complete:"
log "  Profile: $PROFILE"
log "  Branch:  $TARGET_BRANCH"
log "  Commit:  $COMMIT"
log "  Health:  http://127.0.0.1:$PORT/health ✓"
if [ "$TAG_FLAG" = true ]; then
  log "  Tag:     $TAG_NAME"
fi
