#!/usr/bin/env python3
"""Sensitive data scanner for CI.

Scans changed files for patterns that should not be committed:
  - Public IPv4 addresses (private/loopback ranges excluded)
  - PEM private keys
  - Database connection strings with embedded credentials
  - Hardcoded password assignments

Exit codes:
  0 — clean (no findings)
  1 — findings detected (CI should fail)

Usage:
  python scripts/scan_sensitive.py --files /tmp/changed_files.txt
  python scripts/scan_sensitive.py --all                 # scan entire repo
"""

import argparse
import re
import sys
from pathlib import Path

# ── Pattern definitions ────────────────────────────────────────────────────

# IPv4: match any dotted-quad that is NOT in a private/reserved range.
# Private ranges excluded: 10.x, 172.16-31.x, 192.168.x, 127.x, 0.x, 255.x
_PRIVATE_IP = re.compile(
    r"^(?:"
    r"10\.\d{1,3}\.\d{1,3}\.\d{1,3}|"       # 10/8
    r"172\.(?:1[6-9]|2\d|3[01])\.\d{1,3}\.\d{1,3}|"  # 172.16/12
    r"192\.168\.\d{1,3}\.\d{1,3}|"           # 192.168/16
    r"127\.\d{1,3}\.\d{1,3}\.\d{1,3}|"       # loopback
    r"0\.0\.0\.0|"                            # unspecified
    r"255\.255\.255\.255|"                    # broadcast
    r"169\.254\.\d{1,3}\.\d{1,3}"            # link-local
    r")$"
)

_IPV4_PATTERN = re.compile(
    r"\b((?:(?:25[0-5]|2[0-4]\d|[01]?\d\d?)\.){3}"
    r"(?:25[0-5]|2[0-4]\d|[01]?\d\d?))\b"
)

_PATTERNS = [
    (
        "public-ipv4",
        "Public IPv4 address",
        _IPV4_PATTERN,
    ),
    (
        "pem-private-key",
        "PEM private key",
        re.compile(r"-----BEGIN (?:RSA |EC |DSA |OPENSSH )?PRIVATE KEY-----"),
    ),
    (
        "db-credentials",
        "Database URL with embedded credentials",
        re.compile(r"(?:postgresql|mysql|mongodb|redis)://[^@\s]+:[^@\s]+@", re.IGNORECASE),
    ),
    (
        "hardcoded-password",
        "Hardcoded password assignment",
        re.compile(r'(?:password|passwd|pwd)\s*=\s*["\'][^"\']{6,}["\']', re.IGNORECASE),
    ),
]

# ── Allowlist ─────────────────────────────────────────────────────────────

def _load_allowlist(repo_root: Path) -> list[re.Pattern]:
    """Load per-line regex patterns from .scanignore."""
    scanignore = repo_root / ".scanignore"
    patterns = []
    if scanignore.exists():
        for line in scanignore.read_text().splitlines():
            line = line.strip()
            if line and not line.startswith("#"):
                try:
                    patterns.append(re.compile(line))
                except re.error:
                    pass
    return patterns


# ── File filters ──────────────────────────────────────────────────────────

# Extensions that are binary or irrelevant — skip scanning
_SKIP_EXTENSIONS = {
    ".png", ".jpg", ".jpeg", ".gif", ".ico", ".svg", ".woff", ".woff2",
    ".ttf", ".eot", ".mp4", ".mp3", ".wav", ".pdf", ".zip", ".tar",
    ".gz", ".lock", ".pyc", ".pyo", ".so", ".dll", ".exe",
}

# Paths that intentionally contain IP-like patterns (e.g. version numbers in
# package-lock.json) — skip public-IP checks only for these paths
_SKIP_IP_PATHS = {
    "package-lock.json",
    "yarn.lock",
    "frontend/dist",
    "frontend/build",
}


def _should_skip_file(path: Path) -> bool:
    return path.suffix.lower() in _SKIP_EXTENSIONS


def _should_skip_ip(path: Path) -> bool:
    return any(skip in str(path) for skip in _SKIP_IP_PATHS)


# ── Scanner ───────────────────────────────────────────────────────────────

def scan_file(path: Path, allowlist: list[re.Pattern]) -> list[dict]:
    """Scan a single file for sensitive patterns. Returns list of findings."""
    if not path.exists() or not path.is_file():
        return []
    if _should_skip_file(path):
        return []

    try:
        content = path.read_text(encoding="utf-8", errors="replace")
    except Exception:
        return []

    findings = []
    skip_ip = _should_skip_ip(path)

    for rule_id, description, pattern in _PATTERNS:
        if rule_id == "public-ipv4" and skip_ip:
            continue

        for match in pattern.finditer(content):
            matched_value = match.group(0)

            # For public-ipv4: skip private ranges
            if rule_id == "public-ipv4":
                ip = match.group(1)
                if _PRIVATE_IP.match(ip):
                    continue

            # Check allowlist: if any allowlist pattern matches the line context,
            # skip this finding
            line_num = content[: match.start()].count("\n") + 1
            line_text = content.splitlines()[line_num - 1] if line_num <= len(content.splitlines()) else ""
            if any(ap.search(matched_value) or ap.search(line_text) for ap in allowlist):
                continue

            findings.append({
                "rule": rule_id,
                "description": description,
                "file": str(path),
                "line": line_num,
                "match": matched_value[:80],
            })

    return findings


def scan_files(file_list: list[Path], repo_root: Path) -> list[dict]:
    allowlist = _load_allowlist(repo_root)
    all_findings = []
    for path in file_list:
        all_findings.extend(scan_file(path, allowlist))
    return all_findings


# ── Entry point ───────────────────────────────────────────────────────────

def main():
    parser = argparse.ArgumentParser(description="Scan changed files for sensitive data")
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument("--files", metavar="FILE", help="Path to newline-separated list of changed files")
    group.add_argument("--all", action="store_true", help="Scan entire repository")
    args = parser.parse_args()

    repo_root = Path(__file__).parent.parent

    if args.all:
        file_list = [p for p in repo_root.rglob("*") if p.is_file()
                     and ".git" not in p.parts]
    else:
        changed = Path(args.files).read_text().splitlines()
        file_list = [repo_root / f for f in changed if f.strip()]

    findings = scan_files(file_list, repo_root)

    if not findings:
        print("CLEAN: No sensitive data detected.")
        sys.exit(0)

    print(f"FAIL: {len(findings)} sensitive data finding(s) detected:\n")
    for f in findings:
        print(f"  [{f['rule']}] {f['file']}:{f['line']}")
        print(f"    {f['description']}: {f['match']!r}")
        print()

    print("To suppress a false positive, add a regex to .scanignore.")
    sys.exit(1)


if __name__ == "__main__":
    main()
