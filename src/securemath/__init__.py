"""securemath package.

A secure arithmetic library POC demonstrating multi-stage Azure DevOps
release pipelines with PyArmor obfuscation, artifact signing, and multi-OS testing.
"""

from securemath.calculator import add, divide, multiply, subtract
from securemath.license import LicenseStatus, validate_license

__version__ = "0.1.0"

__all__ = [
    "add",
    "subtract",
    "multiply",
    "divide",
    "validate_license",
    "LicenseStatus",
    "__version__",
]
