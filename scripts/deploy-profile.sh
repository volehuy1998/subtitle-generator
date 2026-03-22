#!/usr/bin/env bash
# deploy-profile.sh — Branch-aware Docker profile deployment.
#
# Ensures each Docker profile builds from its designated branch:
#   - cpu (production): always builds from 'main'
#   - newui (staging):  builds from NEWUI_BRANCH (default: current branch)
#
# Usage:
#   ./scripts/deploy-profile.sh cpu              # build prod from main
#   ./scripts/deploy-profile.sh cpu --tag        # build prod + create git tag
#   ./scripts/deploy-profile.sh newui            # build newui from NEWUI_BRANCH
#   ./scripts/deploy-profile.sh newui feat/foo   # build newui from feat/foo
#
# Environment:
#   NEWUI_BRANCH  — branch for newui profile (overridden by CLI arg)
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

PROFILE="${1:?Usage: deploy-profile.sh <cpu|newui> [branch|--tag]}"
SECOND_ARG="${2:-}"

# ── Helpers ──────────────────────────────────────────────────────────────────

log()  { echo "▸ $*"; }
err()  { echo "✗ $*" >&2; exit 1; }

current_branch() { git rev-parse --abbrev-ref HEAD; }

# Save and restore working state safely
save_state() {
  ORIG_BRANCH="$(current_branch)"
  if ! git diff --quiet || ! git diff --cached --quiet; then
    STASHED=true
    git stash push -m "deploy-profile: auto-stash before $PROFILE deploy"
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

# Ensure restore happens on exit (success or failure)
trap restore_state EXIT

# ── Determine target branch ─────────────────────────────────────────────────

case "$PROFILE" in
  cpu)
    TAG_FLAG=false
    if [ "$SECOND_ARG" = "--tag" ]; then
      TAG_FLAG=true
    elif [ -n "$SECOND_ARG" ]; then
      # Allow explicit branch override: deploy-profile.sh cpu <branch>
      PROD_BRANCH_OVERRIDE="$SECOND_ARG"
    fi
    TARGET_BRANCH="${PROD_BRANCH_OVERRIDE:-${PROD_BRANCH:-main}}"
    ;;
  newui)
    if [ -n "$SECOND_ARG" ] && [ "$SECOND_ARG" != "--tag" ]; then
      TARGET_BRANCH="$SECOND_ARG"
    elif [ -n "${NEWUI_BRANCH:-}" ]; then
      TARGET_BRANCH="$NEWUI_BRANCH"
    else
      TARGET_BRANCH="$(current_branch)"
    fi
    TAG_FLAG=false
    ;;
  *)
    err "Unknown profile: $PROFILE (expected 'cpu' or 'newui')"
    ;;
esac

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

# ── Pull latest from remote (if tracking branch exists) ─────────────────────

if git rev-parse --verify "origin/$TARGET_BRANCH" &>/dev/null; then
  git pull --ff-only origin "$TARGET_BRANCH" --quiet 2>/dev/null && log "Pulled latest from origin/$TARGET_BRANCH" || log "No remote changes (or not fast-forwardable)"
fi

# ── Build and deploy ─────────────────────────────────────────────────────────

log "Building Docker profile: $PROFILE"
sudo docker compose --profile "$PROFILE" up -d --build --force-recreate

# ── Health check ─────────────────────────────────────────────────────────────

case "$PROFILE" in
  cpu)  PORT=8000 ;;
  newui) PORT=8001 ;;
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
