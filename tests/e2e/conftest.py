"""E2E test fixtures using Playwright."""

import os
import urllib.request

import pytest

BASE_URL = os.environ.get("E2E_BASE_URL", "https://openlabs.club")


def _server_reachable() -> bool:
    """Check if the target server is reachable and returns a 2xx/3xx response."""
    try:
        import ssl

        ctx = ssl.create_default_context()
        ctx.check_hostname = False
        ctx.verify_mode = ssl.CERT_NONE
        req = urllib.request.Request(BASE_URL, method="HEAD")
        with urllib.request.urlopen(req, timeout=5, context=ctx) as r:
            return r.status < 500
    except Exception:
        return False


_is_reachable = _server_reachable()

# Auto-skip all E2E tests when server is unreachable
if not _is_reachable:

    def pytest_collection_modifyitems(items):
        skip = pytest.mark.skip(reason=f"E2E server unreachable: {BASE_URL}")
        for item in items:
            item.add_marker(skip)


@pytest.fixture(scope="session")
def base_url():
    return BASE_URL


@pytest.fixture(scope="session")
def browser_context_args():
    return {"ignore_https_errors": False}
