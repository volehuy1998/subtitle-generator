# Memory Index

## Team Sentinel (Engineering)
- [team_structure.md](team_structure.md) — SubForge engineering team: 11 members (Atlas, Forge, Bolt, Pixel, Prism, Scout, Stress, Harbor, Anchor, Shield, Quill, Hawk) with Google SWE checklists and agent prompt templates
- [access_privileges.md](access_privileges.md) — Confirmed privileges: full GitHub access (all scopes), full server access, Docker, TLS, CI/CD — granted by investor on 2026-03-14

## Team Meridian (Deployment)
- [team_meridian.md](team_meridian.md) — Team Meridian: external deployment team (8 members — Compass, Crane, Vault, Gauge, Rudder, Signal, Ballast, Dockhand)
- [meridian_server.md](meridian_server.md) — Meridian server: hardware specs, domains, TLS, container layout (sensitive details redacted in public backup)
- [meridian_deployment_20260315.md](meridian_deployment_20260315.md) — First deployment session: two-domain setup, 7 workarounds, 7 issues filed
- [meridian_session_20260315.md](meridian_session_20260315.md) — Full session context: deployment, audit, investor feedback, memory system, next steps per specialist
- [meridian_issues_tracker.md](meridian_issues_tracker.md) — All filed issues (#67-#72, #78) with priority, specialist assignment, and status

## Feedback (Investor Preferences)
- [feedback_pr_review_process.md](feedback_pr_review_process.md) — Every PR must have engineer comments visible on GitHub before merging
- [feedback_detailed_logging.md](feedback_detailed_logging.md) — User values detailed logging for inventory, diagnostics, and planning
- [feedback_config_over_cli.md](feedback_config_over_cli.md) — Always use .env config files over CLI flags for deployment
- [feedback_delegate_no_bottleneck.md](feedback_delegate_no_bottleneck.md) — Compass must delegate to specialists, never bottleneck tasks at leader level
- [feedback_author_disclosure.md](feedback_author_disclosure.md) — Every team member must disclose their identity (name, role) when creating any content
- [feedback_vault_review_before_push.md](feedback_vault_review_before_push.md) — Vault must scan every .meridian/ sync for sensitive data before pushing to GitHub

## Cross-Team Agreements
- [project_cross_team_agreement.md](project_cross_team_agreement.md) — CODEOWNERS, 48h SLA, release notifications, CI validation — agreed 2026-03-15 via RFC #82

## Project State
- [project_session_20260314.md](project_session_20260314.md) — Major Sentinel session: UI overhaul, Google SWE standards, 17 issues resolved, 10 PRs merged
- [project_ci_failures.md](project_ci_failures.md) — CI fully green as of 2026-03-14
- [project_pending_work.md](project_pending_work.md) — Open: distributed deploy, process_video refactor, release-please, SLOs, mypy
- [project_distributed_system.md](project_distributed_system.md) — 5-server plan: sub-ctrl, sub-api-1/2, sub-data, sub-worker-1
- [project_tls.md](project_tls.md) — TLS certificates needed for globally accessible web service
- [project_tls_setup.md](project_tls_setup.md) — TLS cert obtained, main.py updated with HTTPS+HTTP redirect
- [project_status_page.md](project_status_page.md) — Public status page at /status with auto-incident detection

## References
- [reference_repo.md](reference_repo.md) — GitHub repo: volehuy1998/subtitle-generator
