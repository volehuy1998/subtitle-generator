---
name: feedback_author_disclosure
description: Every engineer must disclose their name and role in all artifacts they create — PRs, issues, comments, commits, docs
type: feedback
---

Every Sentinel engineer must identify themselves by name and role in everything they create or contribute to.

**Why:** The investor requires full transparency on who is responsible for what. Anonymous contributions make accountability impossible and obscure the team's expertise.

**How to apply:**

## Commits
Every commit message should be attributable to the engineer who authored the work. Use the commit body or Co-Authored-By when multiple engineers contributed.

## PR descriptions
The PR description must include an **Author** line:
> **Author:** Forge (Senior Backend Engineer), Anchor (Infrastructure Engineer)

## GitHub issue comments / review comments
Every comment must begin with the author header:
> **[Name] ([Role]) — [APPROVE / REQUEST CHANGES / COMMENT]**

Examples:
- `**Forge (Senior Backend Engineer) — APPROVE**`
- `**Shield (Security Engineer) — REQUEST CHANGES**`
- `**Quill (Technical Writer) — COMMENT**`

## Issue creation
Issues filed by a Sentinel engineer must include in the body:
> **Filed by:** Scout (QA Lead)

## Documentation
Any doc section added or significantly modified by an engineer should note authorship in the PR that introduced it, not inline in the doc itself.

## No exceptions
Atlas, Forge, Bolt, Pixel, Prism, Scout, Stress, Harbor, Anchor, Shield, Quill, Hawk — all 11 engineers follow this rule without exception.
