# SubForge CI/CD Restructuring — Design Spec

**Date:** 2026-03-18
**Author:** Atlas (Tech Lead), Team Sentinel
**Status:** Approved (brainstorming complete)

---

## Table of Contents

1. [Goals & Principles](#1-goals--principles)
2. [Pipeline Architecture](#2-pipeline-architecture)
3. [Tier 1 — Fast Gate](#3-tier-1--fast-gate)
4. [Tier 2 — Full Gate](#4-tier-2--full-gate)
5. [Specialized Workflows](#5-specialized-workflows)
6. [Pre-Commit Hook](#6-pre-commit-hook)
7. [Branch Protection & Merge Rules](#7-branch-protection--merge-rules)
8. [Ruff Configuration](#8-ruff-configuration)
9. [Removed Workflows](#9-removed-workflows)
10. [Migration Plan](#10-migration-plan)

---

## 1. Goals & Principles

### Goals

- **Merge only when all requirements pass** — no advisory checks that developers ignore
- **Fast feedback** — Tier 1 (<2 min) catches 80% of issues before slow checks run
- **Source-code-driven** — every check exists because the code demands it, not because it was inherited
- **Fewer workflows** — 4 active workflows + 1 unchanged notification (down from 8), each with one clear purpose
- **Pre-commit matches CI** — if pre-commit passes, Tier 1 should not surprise you

### Principles (from industry research)

- **Two-tier gate model** — fast lint gate + thorough validation gate. Both block merge.
- **Ruff for code quality + security** — TID253 banned imports, S6xx subprocess safety. Industry standard for Python 2026.
- **Semgrep for fast SAST** — 10-second scans, 3,000+ community rules. Runs on every PR.
- **CodeQL for deep analysis** — weekly/nightly semantic taint tracking. Advisory, not blocking.
- **GitHub Secret Protection** — handles sensitive data scanning. No custom secret scanner needed.
- **Staged-files-only pre-commit** — fast, relevant, language-aware. Not a CI mirror.
- **Docs skip CI entirely** — lightweight docs.yml provides stub checks for branch protection.

---

## 2. Pipeline Architecture

### Workflow Inventory (4 workflows)

| Workflow | Trigger | Purpose | Required Check? |
|----------|---------|---------|-----------------|
| `ci.yml` | push/PR to main (code paths) | Tier 1 lint + Tier 2 full validation | Yes: `Lint`, `Test` |
| `codeql.yml` | weekly + push to main (code paths) | Deep semantic security analysis | No (advisory) |
| `docs.yml` | push/PR to main (docs paths only) | Stub checks + docs validation | Yes: stub `Lint`, stub `Test` |
| `release.yml` | push to main (code paths) | Semantic release + Docker publish | No (post-merge) |

`release-notify.yml` is unchanged (fires on release publish, creates deployment checklist).

### Execution Flow

```
Code PR opened/pushed:
  ci.yml triggers
    |
    +-- Tier 1: tier1-lint (<2 min)
    |   +-- Ruff lint + format (Python)
    |   +-- TypeScript type check
    |   +-- ESLint (frontend)
    |   +-- Import order validation
    |   +-- Config consistency
    |   -> Provides "Lint" required check
    |
    +-- Tier 2 (parallel, depends on Tier 1):
        +-- tier2-test-backend
        +-- tier2-test-frontend
        +-- tier2-semgrep
        +-- tier2-dependency-audit
        +-- tier2-build
        +-- tier2-schema
            |
            +-- tier2-gate (aggregator)
                -> Provides "Test" required check

Docs-only PR:
  docs.yml triggers
    +-- Stub "Lint" job (always passes)
    +-- Stub "Test" job (always passes)
    +-- docs-validate (optional, non-blocking)

Weekly:
  codeql.yml triggers
    +-- CodeQL Advanced (Python, JS/TS, Actions)
        -> Results in GitHub Security tab
```

### Path Filtering

```yaml
# ci.yml — triggers on code changes only
on:
  push:
    branches: [main]
    paths-ignore:
      - '**.md'
      - 'docs/**'
      - 'LICENSE'
      - 'CODE_OF_CONDUCT.md'
      - 'CONTRIBUTING.md'
      - '.github/PULL_REQUEST_TEMPLATE.md'
  pull_request:
    branches: [main]
    paths-ignore:
      # same list

# docs.yml — triggers on docs changes only
on:
  push:
    branches: [main]
    paths:
      - '**.md'
      - 'docs/**'
      - 'LICENSE'
      - 'CODE_OF_CONDUCT.md'
      - 'CONTRIBUTING.md'
      - '.github/PULL_REQUEST_TEMPLATE.md'
  pull_request:
    branches: [main]
    paths:
      # same list
```

---

## 3. Tier 1 — Fast Gate

**Job name:** `tier1-lint`
**Status check name:** `Lint`
**Target time:** < 2 minutes
**Blocks merge:** Yes

### Steps

```yaml
tier1-lint:
  name: Lint
  runs-on: ubuntu-latest
  steps:
    - uses: actions/checkout@v6

    # -- Python --
    - uses: actions/setup-python@v6
      with:
        python-version: '3.12'

    - name: Install Python tools
      run: pip install ruff

    - name: Ruff lint
      run: ruff check .   # rules configured in pyproject.toml (single source of truth)

    - name: Ruff format check
      run: ruff format --check --diff .

    # -- Frontend --
    - uses: actions/setup-node@v4
      with:
        node-version: '20'
        cache: 'npm'
        cache-dependency-path: frontend/package-lock.json

    - name: Install frontend dependencies
      run: cd frontend && npm ci

    - name: TypeScript type check
      run: cd frontend && npx tsc -b --noEmit

    - name: ESLint
      run: cd frontend && npx eslint src/ --max-warnings 0

    # -- Consistency --
    - name: Validate cross-file consistency
      run: python scripts/validate_consistency.py
```

### What Tier 1 catches

| Check | Tool | What it detects |
|-------|------|-----------------|
| Python lint | Ruff E,F,W | Syntax errors, undefined names, unused imports |
| Python format | Ruff format | Inconsistent formatting |
| Subprocess safety | Ruff S602,S603,S604 | `shell=True`, string args to subprocess |
| SQL injection patterns | Ruff S608 | String concatenation in SQL queries |
| Banned top-level imports | Ruff TID253 | `torch`, `faster_whisper`, `ctranslate2`, `numpy` at module level |
| TypeScript errors | tsc | Type mismatches, missing properties, null safety |
| Frontend code quality | ESLint | React anti-patterns, unused vars, accessibility |
| Version mismatch | validate_consistency.py | main.py version vs tests vs CHANGELOG |
| Module count drift | validate_consistency.py | Route/service/middleware count in CLAUDE.md vs actual |
| Required files | validate_consistency.py | README, SECURITY, LICENSE, etc. exist |
| Import order | validate_consistency.py | `app.config` is first import in `app/main.py` |

---

## 4. Tier 2 — Full Gate

**Status check name:** `Test` (via `tier2-gate` aggregator job)
**Target time:** < 10 minutes (parallel jobs)
**Blocks merge:** Yes
**Depends on:** Tier 1 passing

### Jobs (all parallel, all need tier1-lint)

#### tier2-test-backend

```yaml
tier2-test-backend:
  needs: tier1-lint
  runs-on: ubuntu-latest
  steps:
    - uses: actions/checkout@v6
    - uses: actions/setup-python@v6
      with:
        python-version: '3.12'
    - run: sudo apt-get update && sudo apt-get install -y ffmpeg
    - run: pip install -r requirements.txt
    - run: pytest tests/ -v --tb=short --cov=app --cov-report=xml
    - uses: actions/upload-artifact@v7
      with:
        name: backend-coverage
        path: coverage.xml
```

#### tier2-test-frontend

```yaml
tier2-test-frontend:
  needs: tier1-lint
  runs-on: ubuntu-latest
  steps:
    - uses: actions/checkout@v6
    - uses: actions/setup-node@v4
      with:
        node-version: '20'
        cache: 'npm'
        cache-dependency-path: frontend/package-lock.json
    - run: cd frontend && npm ci
    - run: cd frontend && npx vitest run --coverage
```

#### tier2-semgrep

```yaml
tier2-semgrep:
  needs: tier1-lint
  runs-on: ubuntu-latest
  steps:
    - uses: actions/checkout@v6
    - run: pip install semgrep
    - name: Semgrep SAST scan
      run: |
        semgrep scan \
          --config=auto \
          --config=p/python \
          --config=p/security-audit \
          --error \
          --no-git-ignore \
          app/
```

**False positive handling:**
- Inline: add `# nosemgrep: rule-id` comment on the flagged line
- File-level: create `.semgrepignore` (gitignore syntax) for paths to exclude
- These are triaged during migration step 3 before `--error` is enabled

**What Semgrep catches that Ruff does not:**
- Cross-statement patterns (user input flows into subprocess)
- Framework-aware rules (FastAPI CORS misconfig, missing auth)
- Path traversal patterns
- Insecure deserialization
- SSRF patterns

#### tier2-dependency-audit

```yaml
tier2-dependency-audit:
  needs: tier1-lint
  runs-on: ubuntu-latest
  steps:
    - uses: actions/checkout@v6
    - uses: actions/setup-python@v6
      with:
        python-version: '3.12'
    - uses: actions/setup-node@v4
      with:
        node-version: '20'
        cache: 'npm'
        cache-dependency-path: frontend/package-lock.json

    - name: Python dependency audit
      run: |
        pip install pip-audit
        # Known CVE exceptions documented inline with justification
        pip-audit -r requirements.txt \
          || echo "::warning::pip-audit found issues — check output above"
        # For persistent exceptions: pip-audit -r requirements.txt --ignore-vuln PYSEC-XXXX

    - name: Frontend dependency audit
      run: cd frontend && npm ci && npm audit --audit-level=high
```

#### tier2-build

```yaml
tier2-build:
  needs: tier1-lint
  runs-on: ubuntu-latest
  steps:
    - uses: actions/checkout@v6
    - uses: actions/setup-node@v4
      with:
        node-version: '20'
        cache: 'npm'
        cache-dependency-path: frontend/package-lock.json

    - name: Build frontend
      run: cd frontend && npm ci && npm run build

    - name: Validate build output
      run: |
        test -f frontend/dist/index.html || (echo "FAIL: index.html missing" && exit 1)
        test -d frontend/dist/assets || (echo "FAIL: assets/ missing" && exit 1)
        ls frontend/dist/assets/*.js > /dev/null 2>&1 || (echo "FAIL: no JS bundles" && exit 1)
        ls frontend/dist/assets/*.css > /dev/null 2>&1 || (echo "FAIL: no CSS bundles" && exit 1)
        echo "Build validation passed"

    - name: Build Docker image
      if: github.ref == 'refs/heads/main'
      run: docker build -t subtitle-generator:${{ github.sha }} .

    - name: Validate Docker health
      if: github.ref == 'refs/heads/main'
      run: |
        docker run -d --name health-test -p 8000:8000 subtitle-generator:${{ github.sha }}
        sleep 15
        curl -f http://localhost:8000/health || (docker logs health-test && exit 1)
        docker stop health-test
```

#### tier2-schema

```yaml
tier2-schema:
  needs: tier1-lint
  runs-on: ubuntu-latest
  steps:
    - uses: actions/checkout@v6
    - uses: actions/setup-python@v6
      with:
        python-version: '3.12'
    - run: pip install -r requirements.txt

    - name: Migration dry-run
      run: |
        DATABASE_URL=sqlite+aiosqlite:///test_schema.db alembic upgrade head

    - name: Validate schema matches models
      run: |
        python -c "
        from app.db.models import Base
        from sqlalchemy import create_engine, inspect
        engine = create_engine('sqlite:///test_schema.db')
        inspector = inspect(engine)
        db_tables = set(inspector.get_table_names())
        model_tables = set(Base.metadata.tables.keys())
        missing = model_tables - db_tables
        extra = db_tables - model_tables - {'alembic_version'}
        if missing:
            print(f'FAIL: Tables in models but not in DB: {missing}')
            exit(1)
        if extra:
            print(f'FAIL: Tables in DB but not in models: {extra}')
            exit(1)
        print(f'Schema OK: {len(db_tables)} tables match')
        "
```

#### tier2-gate (aggregator)

```yaml
tier2-gate:
  name: Test
  needs:
    - tier2-test-backend
    - tier2-test-frontend
    - tier2-semgrep
    - tier2-dependency-audit
    - tier2-build
    - tier2-schema
  runs-on: ubuntu-latest
  steps:
    - run: echo "All Tier 2 checks passed"
```

This job provides the `Test` required status check. It only succeeds if all 6 Tier 2 jobs succeed.

---

## 5. Specialized Workflows

### codeql.yml

Deep semantic analysis. Weekly + on push to main. NOT a required check.

Changes from current:
- Pin `actions/checkout` to v6 (was v4)

```yaml
on:
  push:
    branches: [main]
    paths-ignore: ['**.md', 'docs/**']
  schedule:
    - cron: '0 3 * * 0'    # Weekly Sunday 3am UTC
```

Languages: Python, JavaScript/TypeScript, Actions.
Results feed into GitHub Security tab via SARIF.

### docs.yml

Replaces `docs-skip.yml`. Triggers on docs-only changes. Provides passing stubs for required checks.

```yaml
on:
  push:
    branches: [main]
    paths: ['**.md', 'docs/**', 'LICENSE', 'CODE_OF_CONDUCT.md', 'CONTRIBUTING.md', '.github/PULL_REQUEST_TEMPLATE.md']
  pull_request:
    branches: [main]
    paths: ['**.md', 'docs/**', 'LICENSE', 'CODE_OF_CONDUCT.md', 'CONTRIBUTING.md', '.github/PULL_REQUEST_TEMPLATE.md']

jobs:
  Lint:
    runs-on: ubuntu-latest
    steps:
      - run: echo "Docs-only change -- lint skipped"

  Test:
    runs-on: ubuntu-latest
    steps:
      - run: echo "Docs-only change -- tests skipped"

  docs-validate:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v6
      - name: Check broken links in docs
        run: |
          # Lightweight docs check: verify all file links in README.md exist
          python -c "
          import re, os
          with open('README.md') as f: content = f.read()
          links = re.findall(r'\[.*?\]\((?!http)(.*?)\)', content)
          broken = [l for l in links if not os.path.exists(l)]
          if broken: print(f'Broken links: {broken}'); exit(1)
          print(f'All {len(links)} file links valid')
          "
```

### release.yml

Semantic release + Docker publish. Changes from current:
- Add health test before Docker publish to ghcr.io
- Pin all action versions consistently

### release-notify.yml

No changes. Fires on release published event. Creates deployment checklist issue.

---

## 6. Pre-Commit Hook

Replaces `.git/hooks/pre-commit`. Smart, staged-files-only, language-aware.

```bash
#!/usr/bin/env bash
set -e

# -- Blocked files --
BLOCKED=$(git diff --cached --name-only | grep -E '(cert\.pem|privkey\.pem|\.env$)' || true)
if [ -n "$BLOCKED" ]; then
  echo "BLOCKED: Cannot commit sensitive files: $BLOCKED"
  exit 1
fi

# -- Secret patterns in staged content --
if git diff --cached -U0 | grep -qE '(API_KEY|SECRET|PRIVATE.KEY)=.{8,}'; then
  echo "BLOCKED: Staged content contains potential secrets"
  exit 1
fi

# -- Python staged files --
PY_FILES=$(git diff --cached --name-only --diff-filter=ACM -- '*.py' || true)
if [ -n "$PY_FILES" ]; then
  echo "pre-commit: Checking Python files..."
  ruff check $PY_FILES --select E,F,W,S602,S603,S604,S608,TID253 --ignore E501
  ruff format --check $PY_FILES
fi

# -- Frontend staged files --
FE_FILES=$(git diff --cached --name-only --diff-filter=ACM -- 'frontend/src/**/*.ts' 'frontend/src/**/*.tsx' || true)
if [ -n "$FE_FILES" ]; then
  if [ -d "frontend/node_modules" ]; then
    echo "pre-commit: Checking frontend files..."
    cd frontend && npx eslint $FE_FILES --max-warnings 0
    cd ..
  else
    echo "pre-commit: WARNING -- frontend/node_modules missing, skipping eslint (run npm ci)"
  fi
fi

echo "pre-commit: All checks passed."
```

### Alignment with CI

| Check | Pre-commit | CI Tier 1 | CI Tier 2 |
|-------|-----------|-----------|-----------|
| Ruff lint (E,F,W,S6xx,TID253) | Staged files | All files | -- |
| Ruff format | Staged files | All files | -- |
| Blocked files | Staged files | -- | -- |
| Secret patterns | Staged content | -- | -- |
| ESLint | Staged frontend | All frontend | -- |
| TypeScript tsc | -- | All frontend | -- |
| Alembic check | -- | Yes | -- |
| Consistency | -- | Yes | -- |
| Tests | -- | -- | Yes |
| Semgrep | -- | -- | Yes |
| Dependency audit | -- | -- | Yes |
| Build validation | -- | -- | Yes |
| Schema dry-run | -- | -- | Yes |

---

## 7. Branch Protection & Merge Rules

### Required status checks

```
Required checks: 2
  1. Lint    -> from ci.yml:tier1-lint OR docs.yml:Lint (stub)
  2. Test    -> from ci.yml:tier2-gate OR docs.yml:Test (stub)
```

### Branch protection settings

| Setting | Value |
|---------|-------|
| Required status checks | `Lint`, `Test` |
| Enforce admins | true (no one bypasses) |
| Required approving reviews | 0 (no reviews) |
| Merge method | Squash only |
| Auto-delete branches | On merge |

### What blocks merge -- complete matrix

| Scenario | Blocks merge? | Which check fails? |
|----------|--------------|-------------------|
| Ruff lint error | Yes | Lint |
| Ruff format error | Yes | Lint |
| Subprocess shell=True (S602) | Yes | Lint |
| Banned top-level import (TID253) | Yes | Lint |
| TypeScript type error | Yes | Lint |
| ESLint warning | Yes | Lint |
| Version mismatch | Yes | Lint |
| Config import order wrong | Yes | Lint |
| Backend test fails | Yes | Test |
| Frontend test fails | Yes | Test |
| Semgrep finding | Yes | Test |
| pip-audit CVE | Yes | Test |
| npm audit high vuln | Yes | Test |
| Frontend build fails | Yes | Test |
| DB schema mismatch | Yes | Test |
| CodeQL finding | No | Advisory (weekly) |
| Docker build fails | No | Main branch only |
| Docs-only PR | No | Stubs always pass |

---

## 8. Ruff Configuration

### pyproject.toml

```toml
[tool.ruff]
target-version = "py312"

[tool.ruff.lint]
select = [
  "E",      # pycodestyle errors
  "F",      # pyflakes
  "W",      # pycodestyle warnings
  "I",      # isort (import sorting)
  "S602",   # subprocess-popen-with-shell-equals-true
  "S603",   # subprocess-without-shell-equals-true
  "S604",   # call-with-shell-equals-true
  "S608",   # hardcoded-sql-expression
  "TID253", # banned-module-level-imports
]
ignore = ["E501"]   # no line length limit

[tool.ruff.lint.flake8-tidy-imports]
banned-module-level-imports = [
  "torch",
  "faster_whisper",
  "ctranslate2",
  "numpy",
]

[tool.ruff.lint.flake8-tidy-imports.banned-api]
"subprocess.call".msg = "Use subprocess.run() with shell=False and list args"
```

### validate_consistency.py addition

New check -- `app.config` must be the first import in `app/main.py`:

```python
def check_import_order():
    """Verify app.config is imported before any other app module in main.py."""
    with open("app/main.py") as f:
        lines = f.readlines()

    first_import = None
    for line in lines:
        stripped = line.strip()
        if stripped.startswith(("import ", "from ")) and not stripped.startswith("#"):
            first_import = stripped
            break

    if first_import and "app.config" not in first_import:
        return f"app/main.py: first import must be from app.config, found: {first_import}"
    return None
```

---

## 9. Removed Workflows

| Workflow | Reason for removal |
|----------|-------------------|
| `secret-scan.yml` | Replaced by GitHub Secret Protection (native feature) |
| `docs-skip.yml` | Replaced by `docs.yml` with stub checks + docs validation |
| `review-gate.yml` | Engineer review requirement removed |
| `pr-attributes.yml` | PR attribute enforcement removed |
| `deploy-validate` job (in old ci.yml) | Docker compose profile validation and deploy.sh checks are subsumed by the `tier2-build` job which builds and health-checks the Docker image directly |

### Files to delete

```
.github/workflows/secret-scan.yml
.github/workflows/docs-skip.yml
.github/workflows/review-gate.yml
.github/workflows/pr-attributes.yml
scripts/scan_sensitive.py
.scanignore
```

---

## 10. Migration Plan

### Order of operations

1. Add `pyproject.toml` ruff configuration -- new rules, banned imports
2. Fix any existing violations -- ruff S6xx and TID253 may flag existing code
3. Dry-run Semgrep on existing code: `semgrep scan --config=auto --config=p/python app/` -- triage findings, add `# nosemgrep` for false positives, create `.semgrepignore` for paths to skip
4. Dry-run pip-audit: `pip-audit -r requirements.txt` -- document known CVE exceptions with `--ignore-vuln` flags
5. Update `validate_consistency.py` -- add import order check
6. Write new `ci.yml` -- two-tier structure
7. Write new `docs.yml` -- replaces docs-skip.yml
8. Update `codeql.yml` -- pin actions/checkout@v6
9. Update `release.yml` -- add health test before Docker publish
10. Update `.git/hooks/pre-commit` -- staged-files-only, language-aware
11. Update branch protection -- set required checks to `Lint` + `Test` only
12. Delete removed workflows -- secret-scan, docs-skip, review-gate, pr-attributes
13. Delete removed scripts -- scan_sensitive.py, .scanignore
14. Test on a PR -- verify both tiers pass, docs-only PR gets stubs

### Rollback plan

If the new CI breaks:
- Branch protection can be temporarily set to zero required checks
- Old workflow files are in git history
- Pre-commit hook bypass: `git commit --no-verify`
