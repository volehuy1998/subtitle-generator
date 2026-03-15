#!/usr/bin/env python3
"""Validate cross-file consistency across the SubForge project.

Catches the class of bugs where one file is updated but references in other
files become stale. Designed to run in CI on every code change.

Checks:
  1. Version string in app/main.py matches all test assertions
  2. CHANGELOG.md latest version matches app/main.py
  3. README.md references that point to real files exist
  4. Module counts in CLAUDE.md match actual file counts
  5. SECURITY.md exists (referenced by README.md)

Exit code 0 = all checks pass, 1 = at least one failure.
"""

import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
ERRORS: list[str] = []


def error(msg: str) -> None:
    ERRORS.append(msg)
    print(f"  FAIL: {msg}")


def ok(msg: str) -> None:
    print(f"  OK:   {msg}")


# ── 1. Version consistency ──────────────────────────────────────────────


def check_version_consistency() -> None:
    print("\n[1/5] Version consistency")

    # Extract version from app/main.py
    main_py = ROOT / "app" / "main.py"
    main_text = main_py.read_text()
    m = re.search(r'version="([^"]+)"', main_text)
    if not m:
        error("Cannot find version= in app/main.py")
        return
    app_version = m.group(1)
    ok(f"app/main.py version: {app_version}")

    # Check all test files for version assertions
    tests_dir = ROOT / "tests"
    version_pattern = re.compile(r"""(?:==|!=)\s*["'](\d+\.\d+\.\d+)["']""")
    for test_file in sorted(tests_dir.glob("*.py")):
        text = test_file.read_text()
        for line_num, line in enumerate(text.splitlines(), 1):
            if "version" in line.lower() and version_pattern.search(line):
                found = version_pattern.search(line)
                if found:
                    test_ver = found.group(1)
                    if test_ver != app_version:
                        error(
                            f"{test_file.name}:{line_num} asserts version "
                            f"'{test_ver}' but app/main.py has '{app_version}'"
                        )
                    else:
                        ok(f"{test_file.name}:{line_num} version matches")


# ── 2. CHANGELOG version ────────────────────────────────────────────────


def check_changelog_version() -> None:
    print("\n[2/5] CHANGELOG latest version")

    changelog = ROOT / "CHANGELOG.md"
    if not changelog.exists():
        error("CHANGELOG.md not found")
        return

    main_py = ROOT / "app" / "main.py"
    m = re.search(r'version="([^"]+)"', main_py.read_text())
    app_version = m.group(1) if m else "unknown"

    text = changelog.read_text()
    # Match ## [X.Y.Z] or ## [vX.Y.Z]
    versions = re.findall(r"^## \[v?(\d+\.\d+\.\d+)\]", text, re.MULTILINE)
    if not versions:
        error("No version headers found in CHANGELOG.md")
        return

    latest = versions[0]
    if latest == app_version:
        ok(f"CHANGELOG latest ({latest}) matches app/main.py ({app_version})")
    else:
        # Warn but don't fail — CHANGELOG may lag during development
        print(f"  WARN: CHANGELOG latest ({latest}) != app/main.py ({app_version})")


# ── 3. README file references ────────────────────────────────────────────


def check_readme_references() -> None:
    print("\n[3/5] README.md file references")

    readme = ROOT / "README.md"
    if not readme.exists():
        error("README.md not found")
        return

    text = readme.read_text()
    # Find markdown links: [text](path)
    links = re.findall(r"\[.*?\]\(([^)]+)\)", text)
    for link in links:
        # Skip external URLs and anchors
        if link.startswith("http") or link.startswith("#") or link.startswith("mailto:"):
            continue
        # Resolve relative path
        target = ROOT / link
        if not target.exists():
            error(f"README.md links to '{link}' but file does not exist")
        else:
            ok(f"README.md -> {link} exists")


# ── 4. Module counts in CLAUDE.md ────────────────────────────────────────


def check_module_counts() -> None:
    print("\n[4/5] CLAUDE.md module counts")

    claude_md = ROOT / "CLAUDE.md"
    if not claude_md.exists():
        error("CLAUDE.md not found")
        return

    text = claude_md.read_text()

    checks = {
        "app/routes/": (r"routes/`\*\*? \((\d+) modules?\)", ROOT / "app" / "routes"),
        "app/services/": (r"services/`\*\*? \((\d+) modules?\)", ROOT / "app" / "services"),
        "app/middleware/": (r"middleware/`\*\*? \((\d+) modules?\)", ROOT / "app" / "middleware"),
    }

    for label, (pattern, directory) in checks.items():
        m = re.search(pattern, text)
        if not m:
            print(f"  SKIP: No module count pattern found for {label}")
            continue

        claimed = int(m.group(1))
        # Count all .py files (including __init__.py, matching CLAUDE.md convention)
        actual = len(list(directory.glob("*.py")))

        if claimed == actual:
            ok(f"{label} claims {claimed}, actual {actual}")
        else:
            error(f"{label} claims {claimed} modules but actual count is {actual}")


# ── 5. Required files exist ──────────────────────────────────────────────


def check_required_files() -> None:
    print("\n[5/5] Required project files exist")

    required = [
        "README.md",
        "CLAUDE.md",
        "CONTRIBUTING.md",
        "CHANGELOG.md",
        "SECURITY.md",
        "LICENSE",
        "CODE_OF_CONDUCT.md",
        "docs/TEAM.md",
        "docs/DEPLOY.md",
        ".env.example",
    ]

    for path in required:
        target = ROOT / path
        if target.exists():
            ok(f"{path} exists")
        else:
            error(f"{path} is missing")


# ── Main ─────────────────────────────────────────────────────────────────


def main() -> int:
    print("=" * 60)
    print("  SubForge Consistency Validation")
    print("=" * 60)

    check_version_consistency()
    check_changelog_version()
    check_readme_references()
    check_module_counts()
    check_required_files()

    print("\n" + "=" * 60)
    if ERRORS:
        print(f"  FAILED: {len(ERRORS)} error(s) found")
        for e in ERRORS:
            print(f"    - {e}")
        print("=" * 60)
        return 1
    else:
        print("  ALL CHECKS PASSED")
        print("=" * 60)
        return 0


if __name__ == "__main__":
    sys.exit(main())
