"""Tests to verify obfuscation structure and integrity."""

from pathlib import Path
import pytest


def test_obfuscation_script_exists():
    """Ensure the obfuscation runner script exists and is defined."""
    repo_root = Path(__file__).resolve().parent.parent
    obf_script = repo_root / "scripts" / "obfuscate.py"
    assert obf_script.exists(), "scripts/obfuscate.py must exist"


def test_obfuscated_structure_if_present():
    """If obfuscation has run, verify output structure and plain-text masking."""
    repo_root = Path(__file__).resolve().parent.parent
    obf_dir = repo_root / "obfuscated" / "securemath"

    if not obf_dir.exists():
        pytest.skip("Obfuscated directory not yet generated (pre-build stage).")

    # Required files
    required_files = ["__init__.py", "calculator.py", "license.py", "cli.py"]
    for fname in required_files:
        fpath = obf_dir / fname
        assert fpath.exists(), f"Expected obfuscated file {fname} not found in {obf_dir}"

    # Verify sensitive implementation details are masked
    calc_path = obf_dir / "calculator.py"
    calc_content = calc_path.read_text(encoding="utf-8", errors="ignore")

    sensitive_tokens = [
        "def add(a: Number, b: Number) -> Number:",
        "def subtract(a: Number, b: Number) -> Number:",
        "raise ZeroDivisionError(\"Cannot divide by zero\")",
    ]

    for token in sensitive_tokens:
        assert token not in calc_content, (
            f"Plain-text source leaked into obfuscated file: '{token}'"
        )
