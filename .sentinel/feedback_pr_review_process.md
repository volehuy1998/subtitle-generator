---
name: feedback_pr_review_process
description: Every PR must have team engineer comments (approve/reject/feedback) visible on GitHub before merging. The investor wants transparency.
type: feedback
---

Before merging ANY PR, Team Sentinel must:

1. Deploy the relevant engineer(s) to comment on the PR with their review
2. Each comment must include: engineer nickname, APPROVE/REJECT, reasoning
3. At minimum: the code author + one reviewer from a different team must comment
4. Atlas (Tech Lead) comments last with the merge decision
5. ALL comments must be posted via `gh pr comment` so the investor can see them on GitHub

**Why:** The investor wants full transparency into the team's decision-making process. Every opinion — agreement, disagreement, concerns — should be visible in PR comments.

**How to apply:** Before calling `gh pr merge`, always launch agents for the relevant engineers to post their review comments on the PR first.
