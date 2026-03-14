---
name: feedback_pr_attributes_mandatory
description: All 6 GitHub PR attributes are mandatory before requesting review. Tagging was missing on PRs #86-90 and investor caught it.
type: feedback
---

Before opening ANY pull request, ALL 6 GitHub attributes must be set (CONTRIBUTING.md §8):

1. **Reviewers** — at least one Sentinel engineer (`--reviewer volehuy1998` or equivalent)
2. **Assignees** — PR author (`--assignee volehuy1998`)
3. **Labels** — type label + priority label (+ team label if applicable):
   - Type: `bug`, `enhancement`, `documentation`, `deployment`
   - Priority: `P0-critical`, `P1-high`, `P2-medium`, `P3-low`
   - Team: `sentinel`
4. **Projects** — linked to SubForge Roadmap (node `PVT_kwHOAi6TKc4BRufS`)
5. **Milestone** — appropriate release milestone (currently `1` = v2.2.0)
6. **Development** — at least one issue linked via `Closes #N` in PR body

**Why:** PRs #86, #87, #88, #90 were merged without labels, assignees, milestones, or project links. Investor caught the pattern from the PR list and called it out. This was a policy breach. `gh pr edit` fails due to Projects classic API deprecation — use REST API (`gh api`) instead.

**How to apply:**
Use this template when creating any PR with `gh pr create`:
```bash
gh pr create \
  --title "..." \
  --body "..." \
  --assignee "volehuy1998" \
  --label "bug,P0-critical,sentinel"

# Then immediately after creation:
PR_NUM=$(gh pr view --json number --jq '.number')
PR_NODE=$(gh pr view --json id --jq '.id')

gh api repos/volehuy1998/subtitle-generator/issues/${PR_NUM}/assignees --method POST --field "assignees[]=volehuy1998"
gh api repos/volehuy1998/subtitle-generator/issues/${PR_NUM} --method PATCH --field "milestone=1"
gh api graphql -f query='mutation { addProjectV2ItemById(input: {projectId: "PVT_kwHOAi6TKc4BRufS", contentId: "'${PR_NODE}'"}) { item { id } } }'
```

Labels to apply per PR type:
- Security fix → `bug` + `P0-critical` + `sentinel`
- New CI feature → `enhancement` + `P1-high` + `sentinel`
- Deployment change → `enhancement` + `deployment` + `P1-high` + `sentinel`
- Docs/memory sync → `documentation` + `P3-low` + `sentinel`
- Bug fix → `bug` + priority + `sentinel`
