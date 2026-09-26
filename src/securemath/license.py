"""Mock LicenseSpring license validation module.

ARCHITECTURE NOTE:
------------------
This module implements an architectural mock of the LicenseSpring SDK (or similar
enterprise licensing service). In a production release pipeline:
1. This module would be replaced by the official LicenseSpring Python SDK
   (or a wrapper interacting with the LicenseSpring Cloud API).
2. Production credentials (API Key, Shared Key, Product Code) would be stored in
   Azure Key Vault and injected via Azure DevOps Variable Groups at runtime.
3. Node-locking, hardware IDs, and online activations would be managed against the
   LicenseSpring backend.

For this POC, validation rules evaluate environment variables:
- LICENSE_KEY: Must match 'POC-VALID-123'
- LICENSE_ENVIRONMENT: Deployment stage ('test', 'staging', 'production')
- LICENSE_EXPIRY: Expiry date in YYYY-MM-DD format (must be >= today's date)
"""

from dataclasses import dataclass
from datetime import date, datetime
import os
from typing import Optional

# Valid key configured for POC pipeline testing
MOCK_VALID_LICENSE_KEY = "POC-VALID-123"


class LicenseValidationError(Exception):
    """Raised when license validation fails."""
    pass


@dataclass
class LicenseStatus:
    """Represents the outcome of a license validation attempt."""
    is_valid: bool
    key: Optional[str]
    environment: str
    expiry: Optional[str]
    message: str

    def __str__(self) -> str:
        status_text = "VALID" if self.is_valid else "INVALID"
        return (
            f"License validation started...\n"
            f"Environment: {self.environment}\n"
            f"License: {self.key or '<not provided>'}\n"
            f"Expiry: {self.expiry or '<not provided>'}\n"
            f"Status: {status_text}"
        )


def validate_license(
    key: Optional[str] = None,
    environment: Optional[str] = None,
    expiry: Optional[str] = None,
) -> LicenseStatus:
    """Validate license parameters against mock licensing service rules.

    Args:
        key: The license key string. If None, read from LICENSE_KEY env var.
        environment: The target environment. If None, read from LICENSE_ENVIRONMENT env var.
        expiry: Expiry date in YYYY-MM-DD format. If None, read from LICENSE_EXPIRY env var.

    Returns:
        LicenseStatus: The structured validation result.
    """
    resolved_key = key if key is not None else os.getenv("LICENSE_KEY")
    resolved_env = (
        environment if environment is not None else os.getenv("LICENSE_ENVIRONMENT", "test")
    )
    resolved_expiry = expiry if expiry is not None else os.getenv("LICENSE_EXPIRY")

    # Rule 1: Check key presence
    if not resolved_key:
        return LicenseStatus(
            is_valid=False,
            key=resolved_key,
            environment=resolved_env,
            expiry=resolved_expiry,
            message="License key is missing or empty.",
        )

    # Rule 2: Check key authenticity
    if resolved_key != MOCK_VALID_LICENSE_KEY:
        return LicenseStatus(
            is_valid=False,
            key=resolved_key,
            environment=resolved_env,
            expiry=resolved_expiry,
            message=f"License key '{resolved_key}' is invalid or unauthorized.",
        )

    # Rule 3: Check expiry date if provided
    if resolved_expiry:
        try:
            exp_date = datetime.strptime(resolved_expiry, "%Y-%m-%d").date()
            if exp_date < date.today():
                return LicenseStatus(
                    is_valid=False,
                    key=resolved_key,
                    environment=resolved_env,
                    expiry=resolved_expiry,
                    message=f"License expired on {resolved_expiry}.",
                )
        except ValueError:
            return LicenseStatus(
                is_valid=False,
                key=resolved_key,
                environment=resolved_env,
                expiry=resolved_expiry,
                message=f"Invalid date format for LICENSE_EXPIRY: '{resolved_expiry}'. Expected YYYY-MM-DD.",
            )

    return LicenseStatus(
        is_valid=True,
        key=resolved_key,
        environment=resolved_env,
        expiry=resolved_expiry,
        message="License successfully validated against mock LicenseSpring service.",
    )


def require_license() -> None:
    """Enforce an active license or raise LicenseValidationError."""
    status = validate_license()
    if not status.is_valid:
        raise LicenseValidationError(f"License check failed: {status.message}")
