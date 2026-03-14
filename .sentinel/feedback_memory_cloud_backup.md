---
name: feedback_memory_cloud_backup
description: Every memory update must be backed up to the cloud (.sentinel/ directory committed and pushed to GitHub)
type: feedback
---

Every time memory files are created or updated, they must be synced to `.sentinel/` in the GitHub repository and pushed.

**Why:** Local memory (in `~/.claude/projects/`) is not visible to the investor or team. The `.sentinel/` directory in the repo is the authoritative cloud backup — it persists across sessions and is auditable.

**How to apply:**

After any memory write (new file or update to existing file):
1. Copy all updated memory files to `.sentinel/`:
   ```bash
   cp ~/.claude/projects/-home-claude-user-subtitle-generator/memory/*.md \
      /home/claude-user/subtitle-generator/.sentinel/
   ```
2. Commit with message: `chore(memory): sync Sentinel memory backup`
3. Push to origin main (or current branch if mid-PR)

This applies to ALL memory types: user, feedback, project, reference.

Do not batch memory updates and forget to push — sync immediately after each update.
