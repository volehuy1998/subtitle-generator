#!/usr/bin/env python3
"""Run security injection tests and update data/security_assertions.json.

Usage:
    python scripts/update_security_assertions.py
    python scripts/update_security_assertions.py --commit-hash abc123

The script maps pytest test classes (owasp:<category> docstring marker) to
assertion categories, runs the tests, and writes pass/fail counts + status
to data/security_assertions.json.

Status values:
    secure   — all tests passed
    low_risk — >=80 % passed (minor gaps)
    at_risk  — <80 % passed
    untested — no tests ran for this category
"""

import argparse
import json
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).parent.parent
ASSERTIONS_FILE = ROOT / "data" / "security_assertions.json"
TEST_FILE = ROOT / "tests" / "test_security_injection.py"

# Map assertion id → pytest class name in test_security_injection.py
CATEGORY_CLASS = {
    "file_upload": "TestFileUploadSecurity",
    "path_traversal": "TestPathTraversal",
    "injection": "TestInjection",
    "sec_headers": "TestSecurityHeaders",
    "idor": "TestIDOR",
    "broken_auth": "TestBrokenAuth",
}

# Categories with no dedicated injection tests — keep existing status unless forced
STATIC_CATEGORIES = {"rate_limiting", "secrets", "csp", "dep_pinning"}


def run_tests(test_class: str) -> tuple[int, int]:
    """Run a specific test class; return (passed, total)."""
    target = f"{TEST_FILE}::{test_class}"
    result = subprocess.run(
        [sys.executable, "-m", "pytest", str(target), "-v", "--tb=no", "-q"],
        capture_output=True,
        text=True,
        cwd=ROOT,
    )
    passed = result.stdout.count(" PASSED")
    failed = result.stdout.count(" FAILED")
    error = result.stdout.count(" ERROR")
    total = passed + failed + error
    return passed, total


def status_from_counts(passed: int, total: int) -> str:
    if total == 0:
        return "untested"
    ratio = passed / total
    if ratio == 1.0:
        return "secure"
    if ratio >= 0.8:
        return "low_risk"
    return "at_risk"


def main():
    parser = argparse.ArgumentParser(description="Update security assertions from test results")
    parser.add_argument("--commit-hash", default=None, help="Git commit hash for record")
    parser.add_argument("--category", default=None, help="Run only a specific category (id)")
    args = parser.parse_args()

    # Load existing assertions
    with open(ASSERTIONS_FILE) as f:
        data = json.load(f)

    # Resolve commit hash
    commit = args.commit_hash
    if not commit:
        try:
            commit = subprocess.check_output(["git", "rev-parse", "--short", "HEAD"], cwd=ROOT, text=True).strip()
        except Exception:
            commit = "unknown"

    updated_count = 0
    for assertion in data["assertions"]:
        aid = assertion["id"]
        if args.category and aid != args.category:
            continue
        if aid in STATIC_CATEGORIES:
            # Static categories: run their matching tests from existing test_security.py
            # and reflect actual pass/fail counts
            if aid == "rate_limiting":
                passed, total = _run_rate_limit_tests()
            elif aid == "secrets":
                passed, total = _run_secrets_tests()
            elif aid == "sec_headers":
                passed, total = run_tests(CATEGORY_CLASS.get("sec_headers", ""))
            else:
                # No automated tests — leave as-is
                continue
        else:
            cls = CATEGORY_CLASS.get(aid)
            if not cls:
                continue
            print(f"  Running {cls}...", end=" ", flush=True)
            passed, total = run_tests(cls)
            print(f"{passed}/{total}")

        old_status = assertion["status"]
        new_status = status_from_counts(passed, total)
        assertion["tests_passed"] = passed
        assertion["tests_total"] = total
        assertion["status"] = new_status
        if old_status != new_status:
            print(f"    {aid}: {old_status} -> {new_status}")
        updated_count += 1

    data["last_updated"] = datetime.now(timezone.utc).isoformat()
    data["last_run_commit"] = commit

    with open(ASSERTIONS_FILE, "w") as f:
        json.dump(data, f, indent=2)

    print(f"\nUpdated {updated_count} assertion(s). Commit: {commit}")
    print(f"Written to: {ASSERTIONS_FILE}")


def _run_rate_limit_tests() -> tuple[int, int]:
    """Run rate-limit related tests across the test suite."""
    result = subprocess.run(
        [sys.executable, "-m", "pytest", "-k", "rate_limit or brute_force or throttle", "--tb=no", "-q"],
        capture_output=True,
        text=True,
        cwd=ROOT,
    )
    # Simple: count PASSED/FAILED markers
    passed = result.stdout.count(" PASSED")
    failed = result.stdout.count(" FAILED")
    return passed, passed + failed


def _run_secrets_tests() -> tuple[int, int]:
    """Run secrets/env var tests."""
    result = subprocess.run(
        [sys.executable, "-m", "pytest", "-k", "secret or env_var or api_key or jwt", "--tb=no", "-q"],
        capture_output=True,
        text=True,
        cwd=ROOT,
    )
    passed = result.stdout.count(" PASSED")
    failed = result.stdout.count(" FAILED")
    return passed, passed + failed


if __name__ == "__main__":
    main()
