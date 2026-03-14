---
name: feedback_delegation
description: Investor instruction — each Sentinel engineer must independently evaluate, comment, and review within their domain; Atlas must not consolidate everything solo
type: feedback
---

Each Sentinel engineer must visibly participate in their area of expertise. Atlas's role is to coordinate and make final decisions — not to be the only voice.

**Why:** The investor explicitly asked why engineers weren't participating in evaluation. A team where only the leader speaks is a bottleneck and does not surface in-depth professional insights.

**How to apply:**

## Evaluation / Triage (incoming issues, PRs, findings)
- **Scout** — reproduces bugs, assesses test coverage gaps, files QA findings
- **Pixel / Prism** — evaluates UI/frontend issues independently with their own eyes
- **Shield** — audits security-sensitive findings (cookies, CSP, CORS, headers)
- **Anchor / Harbor** — evaluates infra/deploy issues (docker-compose, deploy scripts, CI)
- **Quill** — reviews documentation accuracy

## Implementation
- Right domain expert implements, per team_structure.md deployment rules
- Hawk reviews every code change before it's committed

## PR Review Comments
Each reviewer must post their own named comment on GitHub:
> **[Name] ([Role]) — APPROVE / REQUEST CHANGES**
> [their specific domain findings]

Do NOT have Atlas consolidate multiple engineers' opinions into one comment.
Atlas posts last as final sign-off after domain reviewers have already commented.

## Order of operations
1. Domain engineers evaluate and comment (in parallel where possible)
2. Hawk reviews the code
3. Shield audits if security-sensitive
4. Scout verifies tests
5. Atlas signs off

Never skip steps 1-4 and go straight to Atlas approval.
