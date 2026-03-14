# Team Sentinel — Backup Memory

This directory is a backup of Team Sentinel's persistent memory, originally stored in `.claude/projects/` which is local to the development machine and not version-controlled.

## Why This Exists

If the development system is wiped, the `.claude/` directory deleted, or Claude Code reinstalled, all team memory is lost — team structure, granted privileges, review processes, session history. This backup in the repo ensures the team can be fully restored from GitHub.

## How To Restore

If starting fresh on a new system:

```bash
# After installing Claude Code and cloning the repo:
# The memory path is derived from your working directory, with slashes replaced by dashes.
# For /root/subtitle-generator the path is:
mkdir -p ~/.claude/projects/-root-subtitle-generator/memory/
cp .sentinel/*.md ~/.claude/projects/-root-subtitle-generator/memory/
```

The memory path pattern is `~/.claude/projects/<working-dir-with-dashes>/memory/`, where the working directory's `/` separators are replaced with `-`. For example:
- `/root/subtitle-generator` → `-root-subtitle-generator`
- `/home/claude-user/subtitle-generator` → `-home-claude-user-subtitle-generator`

## Contents

| File | Purpose |
|------|---------|
| `MEMORY.md` | Index of all memory files |
| `access_privileges.md` | Investor-granted permissions (GitHub + server) |
| `team_structure.md` | 11 engineers, roles, Google SWE checklists, agent prompts |
| `feedback_pr_review_process.md` | PR review transparency rule |
| `feedback_detailed_logging.md` | Logging preferences |
| `reference_repo.md` | GitHub repo reference |
| `project_distributed_system.md` | 5-server deployment plan |
| `project_tls.md` | TLS certificate requirements |
| `project_tls_setup.md` | TLS setup completed |
| `project_status_page.md` | Public status page details |
| `project_session_20260314.md` | Major session summary (2026-03-14) |
| `project_ci_failures.md` | CI status tracking |
| `project_pending_work.md` | Open work items |

## Keep In Sync

When memory files are updated in `.claude/`, copy them here and commit:

```bash
cp ~/.claude/projects/-root-subtitle-generator/memory/*.md .sentinel/
git add .sentinel/ && git commit -m "chore: sync .sentinel/ backup with latest memory"
```

---

*Team Sentinel — "We guard quality, security, and standards."*
