---
name: access_privileges
description: Confirmed privileges granted by the investor (volehuy1998) to Team Sentinel — system access and GitHub full permissions
type: reference
---

# Team Sentinel — Granted Privileges

**Granted by:** volehuy1998 (investor/owner)
**Granted to:** Team Sentinel (Atlas + 10 engineers)
**Date confirmed:** 2026-03-14

## GitHub Access (github.com)

**Account:** volehuy1998
**Plan:** GitHub Free
**Token scopes (verified via `gh auth status`):**

| Scope | Access Level | What It Allows |
|-------|-------------|----------------|
| `repo` | Full | Code, PRs, issues, branches, releases, tags, settings |
| `workflow` | Full | GitHub Actions CI/CD creation and management |
| `admin:repo_hook` | Full | Webhooks, branch protection rules |
| `admin:org` | Full | Organization management |
| `admin:public_key` | Full | SSH key management |
| `admin:gpg_key` | Full | GPG signing key management |
| `admin:ssh_signing_key` | Full | SSH signing key management |
| `admin:org_hook` | Full | Organization webhook management |
| `admin:enterprise` | Full | Enterprise administration |
| `delete_repo` | Full | Repository deletion |
| `delete:packages` | Full | Package deletion |
| `write:packages` | Full | GitHub Packages / Container Registry |
| `write:discussion` | Full | Discussion management |
| `write:network_configurations` | Full | Network configuration |
| `project` | Full | GitHub Projects (boards) |
| `codespace` | Full | GitHub Codespaces |
| `copilot` | Full | GitHub Copilot |
| `gist` | Full | Gist creation/management |
| `notifications` | Full | Notification management |
| `audit_log` | Full | Audit log access |
| `user` | Full | User profile management |

## Repository Access

**Repository:** volehuy1998/subtitle-generator
**Branch protection:** Team Sentinel configured and manages branch protection on `main`
**CODEOWNERS:** Team Sentinel listed as code owner for all paths

## System Access (Server)

**Host:** Production server running subtitle-generator
**Access level:** Full sudo access via `claude-user` account
**Docker:** Full Docker and Docker Compose management
**Services:** Can start/stop/rebuild all containers (subtitle-generator, PostgreSQL, Redis)
**TLS:** Access to Let's Encrypt certificates at /etc/letsencrypt/
**Filesystem:** Full read/write to /home/claude-user/subtitle-generator/

## What Team Sentinel Is Authorized To Do

1. Create, merge, and close Pull Requests
2. Create and delete branches
3. Create tags and GitHub Releases
4. Configure branch protection rules
5. Manage GitHub Actions workflows
6. Configure Dependabot and CodeQL
7. Publish Docker images to ghcr.io
8. Create and manage GitHub Issues
9. Manage CODEOWNERS and repository settings
10. Deploy and manage Docker containers on the production server
11. Manage TLS certificates
12. Full CI/CD pipeline control

## Investor's Statement

> "You now know that I've given you maximum privileges, both on this system and on github.com."
> "You also have full access to all other features on github.com using my account because I have verified it for you."
> "Your team has full authority to propose and decide."
> "Please save all the confirmations of the privileges I've granted you, because if something goes wrong someday, I can use your confirmations to reinstate your privileges."

— volehuy1998, 2026-03-14
