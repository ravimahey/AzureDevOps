"""Pytest fixtures and configuration for securemath test suite."""

import os
import sys
from pathlib import Path
import pytest

# Ensure src/ is on sys.path
repo_root = Path(__file__).resolve().parent.parent
src_dir = repo_root / "src"
if str(src_dir) not in sys.path:
    sys.path.insert(0, str(src_dir))


@pytest.fixture
def mock_valid_license_env(monkeypatch):
    """Fixture to set valid mock license environment variables."""
    monkeypatch.setenv("LICENSE_KEY", "POC-VALID-123")
    monkeypatch.setenv("LICENSE_ENVIRONMENT", "test")
    monkeypatch.setenv("LICENSE_EXPIRY", "2099-12-31")


@pytest.fixture
def mock_invalid_license_env(monkeypatch):
    """Fixture to set an invalid mock license key."""
    monkeypatch.setenv("LICENSE_KEY", "INVALID-KEY-999")
    monkeypatch.setenv("LICENSE_ENVIRONMENT", "test")
    monkeypatch.setenv("LICENSE_EXPIRY", "2099-12-31")


@pytest.fixture
def mock_expired_license_env(monkeypatch):
    """Fixture to set an expired license."""
    monkeypatch.setenv("LICENSE_KEY", "POC-VALID-123")
    monkeypatch.setenv("LICENSE_ENVIRONMENT", "test")
    monkeypatch.setenv("LICENSE_EXPIRY", "2020-01-01")
