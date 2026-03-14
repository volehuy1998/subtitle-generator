# Team Meridian — Deployment Memory Backup

This directory is a backup of Team Meridian's persistent memory, originally stored in `.claude/projects/` which is local to the deployment machine and not version-controlled.

## Why This Exists

Following Team Sentinel's `.sentinel/` pattern. If the deployment system is wiped, the `.claude/` directory deleted, or Claude Code reinstalled, all team memory is lost. This backup in the repo ensures Team Meridian can be fully restored from GitHub.

## How To Restore

If starting fresh on a new system:

```bash
# After installing Claude Code and cloning the repo:
# The memory path is derived from your working directory.
# For /root/subtitle-generator:
mkdir -p ~/.claude/projects/-root-subtitle-generator/memory/
cp .meridian/*.md ~/.claude/projects/-root-subtitle-generator/memory/
```

## Contents

| File | Purpose |
|------|---------|
| `MEMORY.md` | Index of all memory files (shared with Sentinel) |
| `meridian_server.md` | Server details: IP, OS, domains, TLS, container layout, paths |
| `meridian_deployment_20260315.md` | First deployment session: workarounds, issues filed |
| `meridian_issues_tracker.md` | All filed issues with priority, specialist assignments |
| `feedback_config_over_cli.md` | Investor preference: .env files over CLI flags |
| `feedback_delegate_no_bottleneck.md` | Investor instruction: delegate, don't bottleneck |
| `feedback_pr_review_process.md` | PR review transparency rule |
| `feedback_detailed_logging.md` | Detailed logging preference |

## Keep In Sync

When memory files are updated in `.claude/`, copy them here and commit:

```bash
cp ~/.claude/projects/-root-subtitle-generator/memory/meridian_*.md .meridian/
cp ~/.claude/projects/-root-subtitle-generator/memory/feedback_*.md .meridian/
git add .meridian/ && git commit -m "chore: sync .meridian/ backup with latest memory"
```

---

*Team Meridian — "We deploy what Sentinel builds."*
