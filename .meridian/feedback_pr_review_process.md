---
name: feedback_pr_review_process
description: Every PR must have team engineer comments (approve/reject/feedback) visible on GitHub before merging. The investor wants transparency.
type: feedback
---

Before merging ANY PR, the authoring team must ensure transparent review:

**Upstream rule (from Sentinel/investor):**
1. Each reviewer must comment with: engineer nickname, APPROVE/REJECT, reasoning
2. At minimum: the code author + one reviewer must comment
3. Team lead comments last with the merge decision
4. ALL comments must be posted via `gh pr comment` so the investor can see them on GitHub

**How Team Meridian applies this:**
- For Meridian PRs (e.g., `.meridian/` backups, deployment configs): Compass reviews + one specialist signs off
- For PRs to Sentinel code: follow Sentinel's process — Hawk (Code Reviewer) must approve
- When reviewing Sentinel PRs that affect deployment: Meridian specialists post domain-specific feedback

**Why:** The investor wants full transparency into every team's decision-making process. Every opinion — agreement, disagreement, concerns — should be visible in PR comments.

**How to apply:** Before calling `gh pr merge`, always ensure review comments from the relevant engineers are posted on the PR first.
