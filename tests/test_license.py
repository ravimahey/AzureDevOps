"""Unit tests for the mock LicenseSpring license validation module."""

import pytest
from securemath.license import (
    LicenseStatus,
    LicenseValidationError,
    require_license,
    validate_license,
)


class TestLicenseValidation:
    """Test license validation rules and edge cases."""

    def test_valid_license(self, mock_valid_license_env):
        status = validate_license()
        assert status.is_valid is True
        assert status.key == "POC-VALID-123"
        assert status.environment == "test"
        assert "validated" in status.message.lower()

    def test_invalid_license_key(self, mock_invalid_license_env):
        status = validate_license()
        assert status.is_valid is False
        assert "invalid" in status.message.lower() or "unauthorized" in status.message.lower()

    def test_expired_license(self, mock_expired_license_env):
        status = validate_license()
        assert status.is_valid is False
        assert "expired" in status.message.lower()

    def test_missing_license_key(self, monkeypatch):
        monkeypatch.delenv("LICENSE_KEY", raising=False)
        status = validate_license()
        assert status.is_valid is False
        assert "missing" in status.message.lower()

    def test_explicit_arguments_override_env(self, mock_valid_license_env):
        # Override valid env with invalid explicit key
        status = validate_license(key="INVALID-OVERRIDE")
        assert status.is_valid is False

        # Override with explicit valid key
        status2 = validate_license(key="POC-VALID-123", environment="prod", expiry="2099-01-01")
        assert status2.is_valid is True
        assert status2.environment == "prod"

    def test_invalid_expiry_date_format(self):
        status = validate_license(key="POC-VALID-123", expiry="invalid-date-string")
        assert status.is_valid is False
        assert "invalid date format" in status.message.lower()

    def test_require_license_helper(self, mock_valid_license_env):
        # Should not raise
        require_license()

    def test_require_license_helper_raises(self, mock_invalid_license_env):
        with pytest.raises(LicenseValidationError):
            require_license()
