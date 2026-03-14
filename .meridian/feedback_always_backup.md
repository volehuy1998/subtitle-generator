---
name: feedback_always_backup
description: CRITICAL investor rule — every memory change MUST be immediately backed up to GitHub via scripts/meridian-backup.sh. No exceptions.
type: feedback
---

Every memory change MUST be immediately backed up to GitHub. This is non-negotiable.

**Why:** The investor has repeated this instruction multiple times because Compass kept updating local memory without syncing to `.meridian/` on GitHub. This is the single most frequently violated rule. The investor should never have to remind us of this again.

**How to apply:**
1. After ANY write to `~/.claude/projects/-root-subtitle-generator/memory/`, immediately run:
   ```bash
   bash scripts/meridian-backup.sh
   ```
2. The script handles: file sync, Vault security scan, branch creation, commit, and push
3. After the script runs, create a PR for the branch
4. This applies to ALL memory updates — session logs, feedback rules, issue trackers, agreements, everything
5. NEVER say "context saved" or "memory updated" without also having pushed to GitHub
6. If in doubt, run the backup script — it's idempotent and will exit cleanly if nothing changed
