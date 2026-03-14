---
name: feedback_vault_review_before_push
description: Mandatory rule — Vault must scan every .meridian/ sync for sensitive data (IP, ports, paths, creds) before pushing to GitHub
type: feedback
---

Every `.meridian/` backup sync must be reviewed by Vault (Anya Petrova) before pushing to GitHub.

**Why:** The public IP was leaked in MEMORY.md index THREE times despite being redacted in the content file. The local memory has unredacted details; syncing to the public backup re-introduces sensitive data if the index descriptions aren't also redacted. Compass missed this repeatedly because there was no dedicated security reviewer within Team Meridian.

**How to apply:**
1. Before any `git push` that includes `.meridian/` files, run a sensitive data scan:
   - `grep -rn "124\.197" .meridian/` (IP addresses)
   - `grep -rn "0\.0\.0\.0:" .meridian/` (port bindings)
   - `grep -rn "/opt/subtitle\|/etc/letsencrypt\|/etc/nginx" .meridian/` (absolute paths)
2. Vault signs off on the scan results
3. Only then push to GitHub
4. This is non-negotiable — no exceptions, even for "quick syncs"
