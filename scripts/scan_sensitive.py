#!/usr/bin/env python3
"""Sensitive data scanner for CI.

Scans changed files for patterns that should not be committed. Covers the
sensitive information categories agreed in issue #89 (Sentinel x Meridian RFC):

  Category 1 — Network & Infrastructure (HIGH)
    - Public IPv4 addresses (private/reserved ranges excluded)
    - Public IPv6 addresses (link-local / loopback excluded)
    - Exposed service port bindings (0.0.0.0:<port>)

  Category 2 — Credentials & Secrets (CRITICAL)
    - PEM private keys (RSA, EC, DSA, OpenSSH)
    - Database connection URLs with embedded credentials
    - AWS access key IDs (AKIA / ASIA / AROA / AIDA / AIPA)
    - GCP API keys (AIzaSy...)
    - GitHub tokens (ghp_, ghs_, gho_, github_pat_)
    - Slack tokens (xoxb-, xoxp-, xoxa-, xoxr-)
    - Generic API keys (sk-... with sufficient entropy)
    - JWT tokens (eyJ... header.payload.signature)
    - Hardcoded password assignments

  Category 3 — Configuration Secrets (HIGH)
    - Environment variable assignments with sensitive names + real values
    - Webhook/HMAC secret assignments

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

# ── Category 1: Network & Infrastructure ─────────────────────────────────

# Private/reserved IPv4 ranges (RFC 1918, RFC 5737, loopback, link-local,
# broadcast, unspecified). Matches are excluded from the public-IP rule.
_PRIVATE_IPV4 = re.compile(
    r"^(?:"
    r"10\.\d{1,3}\.\d{1,3}\.\d{1,3}|"  # 10/8
    r"172\.(?:1[6-9]|2\d|3[01])\.\d{1,3}\.\d{1,3}|"  # 172.16/12
    r"192\.168\.\d{1,3}\.\d{1,3}|"  # 192.168/16
    r"127\.\d{1,3}\.\d{1,3}\.\d{1,3}|"  # loopback
    r"0\.0\.0\.0|"  # unspecified
    r"255\.255\.255\.255|"  # broadcast
    r"169\.254\.\d{1,3}\.\d{1,3}|"  # link-local
    r"192\.0\.2\.\d{1,3}|"  # RFC 5737 TEST-NET-1
    r"198\.51\.100\.\d{1,3}|"  # RFC 5737 TEST-NET-2
    r"203\.0\.113\.\d{1,3}"  # RFC 5737 TEST-NET-3
    r")$"
)

_IPV4_PATTERN = re.compile(
    r"\b((?:(?:25[0-5]|2[0-4]\d|[01]?\d\d?)\.){3}"
    r"(?:25[0-5]|2[0-4]\d|[01]?\d\d?))\b"
)

# IPv6: global unicast (2000::/3) and unique local (fc00::/7).
# Excludes ::1 (loopback), fe80:: (link-local), :: (unspecified).
_IPV6_PATTERN = re.compile(
    r"(?<![:\w])"  # not preceded by colon or word char (avoids URLs)
    r"("
    r"(?:[0-9a-fA-F]{1,4}:){7}[0-9a-fA-F]{1,4}"  # full 8-group
    r"|(?:[0-9a-fA-F]{1,4}:){1,7}:"  # compressed trailing
    r"|:(?::[0-9a-fA-F]{1,4}){1,7}"  # compressed leading
    r"|(?:[0-9a-fA-F]{1,4}:){1,6}:[0-9a-fA-F]{1,4}"  # mixed
    r")"
    r"(?![:\w])"
)

_PRIVATE_IPV6 = re.compile(
    r"^(?:::1|fe80:|fc[0-9a-f]{2}:|fd[0-9a-f]{2}:|::$)",
    re.IGNORECASE,
)

# Service bound on all interfaces with a port: 0.0.0.0:5432 in config/docs
_BIND_ALL_PORT = re.compile(r"0\.0\.0\.0:\d{2,5}")

# ── All detection patterns ────────────────────────────────────────────────

_PATTERNS = [
    # --- Category 1 ---
    (
        "public-ipv4",
        "Public IPv4 address",
        _IPV4_PATTERN,
    ),
    (
        "public-ipv6",
        "Public IPv6 address",
        _IPV6_PATTERN,
    ),
    (
        "bind-all-port",
        "Service bound on all interfaces (0.0.0.0:<port>) outside config",
        _BIND_ALL_PORT,
    ),
    # --- Category 2 ---
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
        "aws-access-key",
        "AWS access key ID",
        re.compile(r"\b(AKIA|ASIA|AROA|AIDA|AIPA)[0-9A-Z]{16,128}\b"),
    ),
    (
        "gcp-api-key",
        "GCP API key",
        re.compile(r"\bAIzaSy[0-9A-Za-z_-]{33}\b"),
    ),
    (
        "github-token",
        "GitHub token",
        re.compile(r"\b(ghp_|ghs_|gho_|github_pat_)[0-9A-Za-z_]{36,}\b"),
    ),
    (
        "slack-token",
        "Slack token",
        re.compile(r"\b(xoxb|xoxp|xoxa|xoxr)-[0-9A-Za-z-]{16,}\b"),
    ),
    (
        "generic-api-key",
        "Generic API key (sk- prefix with sufficient entropy)",
        re.compile(r"\bsk-[0-9A-Za-z]{32,}\b"),
    ),
    (
        "jwt-token",
        "JWT token",
        re.compile(r"\beyJ[A-Za-z0-9_-]{10,}\.[A-Za-z0-9_-]{10,}\.[A-Za-z0-9_-]{10,}\b"),
    ),
    (
        "hardcoded-password",
        "Hardcoded password assignment",
        re.compile(r'(?:password|passwd|pwd)\s*=\s*["\'][^"\']{6,}["\']', re.IGNORECASE),
    ),
    # --- Category 3 ---
    (
        "env-credential",
        "Env var with embedded credential value",
        re.compile(
            r"^(?:export\s+)?(?:DATABASE_URL|SECRET_KEY|WEBHOOK_SECRET|API_SECRET"
            r"|JWT_SECRET|SIGNING_KEY|ENCRYPTION_KEY)\s*=\s*[\"']?[^\s\"'#]{8,}",
            re.MULTILINE,
        ),
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
    ".png",
    ".jpg",
    ".jpeg",
    ".gif",
    ".ico",
    ".svg",
    ".woff",
    ".woff2",
    ".ttf",
    ".eot",
    ".mp4",
    ".mp3",
    ".wav",
    ".pdf",
    ".zip",
    ".tar",
    ".gz",
    ".lock",
    ".pyc",
    ".pyo",
    ".so",
    ".dll",
    ".exe",
}

# Paths where IP-like decimal patterns are expected (version numbers, etc.)
_SKIP_IP_PATHS = {
    "package-lock.json",
    "yarn.lock",
    "frontend/dist",
    "frontend/build",
}

# Paths where 0.0.0.0:<port> bindings are legitimate configuration
_SKIP_BIND_ALL_PATHS = {
    "docker-compose.yml",
    "nginx.conf",
    "nginx.conf.example",
}


def _should_skip_file(path: Path) -> bool:
    return path.suffix.lower() in _SKIP_EXTENSIONS


def _should_skip_ip(path: Path) -> bool:
    return any(skip in str(path) for skip in _SKIP_IP_PATHS)


def _should_skip_bind_all(path: Path) -> bool:
    return any(path.name == skip or skip in str(path) for skip in _SKIP_BIND_ALL_PATHS)


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
    skip_bind = _should_skip_bind_all(path)
    lines = content.splitlines()

    for rule_id, description, pattern in _PATTERNS:
        if rule_id in ("public-ipv4", "public-ipv6") and skip_ip:
            continue
        if rule_id == "bind-all-port" and skip_bind:
            continue

        for match in pattern.finditer(content):
            matched_value = match.group(0)

            # Category 1: exclude private/reserved ranges
            if rule_id == "public-ipv4":
                ip = match.group(1)
                if _PRIVATE_IPV4.match(ip):
                    continue
            elif rule_id == "public-ipv6":
                addr = match.group(1)
                if _PRIVATE_IPV6.match(addr):
                    continue

            line_num = content[: match.start()].count("\n") + 1
            line_text = lines[line_num - 1] if line_num <= len(lines) else ""

            # Allowlist: skip if any pattern matches value or line
            if any(ap.search(matched_value) or ap.search(line_text) for ap in allowlist):
                continue

            findings.append(
                {
                    "rule": rule_id,
                    "description": description,
                    "file": str(path),
                    "line": line_num,
                    "match": matched_value[:80],
                }
            )

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
        file_list = [p for p in repo_root.rglob("*") if p.is_file() and ".git" not in p.parts]
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
