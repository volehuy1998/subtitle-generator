"""E2E test fixtures using Playwright."""
import pytest
import os

BASE_URL = os.environ.get("E2E_BASE_URL", "https://openlabs.club")

@pytest.fixture(scope="session")
def base_url():
    return BASE_URL

@pytest.fixture(scope="session")
def browser_context_args():
    return {"ignore_https_errors": False}
