#!/usr/bin/env python3
"""Standalone script to validate license configuration during CI/CD build.

ARCHITECTURE NOTE:
------------------
This script acts as the pipeline gatekeeper simulating LicenseSpring license
verification. In an enterprise production pipeline:
1. This script interacts with the LicenseSpring Cloud API using credentials
   injected from Azure Key Vault.
2. If the build environment or target release license is revoked, expired,
   or unauthorized, the pipeline stops immediately before any artifact creation.

For this POC:
- Reads LICENSE_KEY, LICENSE_ENVIRONMENT, LICENSE_EXPIRY from environment variables.
- Validates against mock licensing rules (Key: 'POC-VALID-123').
- Exits 0 on valid license; exits 1 on failure.
"""

import os
import sys
from pathlib import Path

# Ensure src/ is importable even before package installation
repo_root = Path(__file__).resolve().parent.parent
src_dir = repo_root / "src"
if str(src_dir) not in sys.path:
    sys.path.insert(0, str(src_dir))

from securemath.license import validate_license


def main() -> int:
    env_name = os.getenv("LICENSE_ENVIRONMENT", "test")
    license_key = os.getenv("LICENSE_KEY")
    expiry = os.getenv("LICENSE_EXPIRY")

    print("License validation started...")
    if license_key:
        print(f"Environment: {env_name}")
        print(f"License: {license_key}")
        if expiry:
            print(f"Expiry: {expiry}")

    status = validate_license(key=license_key, environment=env_name, expiry=expiry)

    if status.is_valid:
        print(f"Status: VALID")
        print(f"Details: {status.message}")
        return 0
    else:
        print(f"Status: INVALID")
        print(f"Details: {status.message}")
        print("ERROR: Build cannot continue.")
        return 1


if __name__ == "__main__":
    sys.exit(main())
