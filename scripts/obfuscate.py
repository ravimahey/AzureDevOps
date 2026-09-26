#!/usr/bin/env python3
"""PyArmor Obfuscation Runner and Integrity Verifier.

SECURITY & ARCHITECTURAL NOTE:
-----------------------------
Source code obfuscation with PyArmor transforms Python source code into protected
bytecode and wraps modules with runtime protection.

IMPORTANT CAVEAT:
Obfuscation does NOT provide cryptographic secrecy or mathematical confidentiality.
Its purpose is source-code protection and significantly raising the effort and
economic cost required for reverse engineering, tampering, or intellectual property theft.

In the CI/CD pipeline, this script isolates the PyArmor invocation so changes
in PyArmor versions (e.g. PyArmor 8/9 vs 7) or target platforms (e.g. glibc vs musl)
do not require modifying the pipeline YAML.
"""

import argparse
import os
import shutil
import subprocess
import sys
from pathlib import Path


def run_obfuscation(
    source_dir: Path,
    output_dir: Path,
    target_platforms: str = None,
) -> bool:
    """Run PyArmor to obfuscate source files and verify output."""
    print("=" * 60)
    print("PyArmor Obfuscation Stage")
    print(f"Source Directory: {source_dir}")
    print(f"Output Directory: {output_dir}")
    print("=" * 60)

    if not source_dir.exists():
        print(f"ERROR: Source directory '{source_dir}' does not exist.")
        return False

    # Clean existing output directory if present
    if output_dir.exists():
        shutil.rmtree(output_dir)
    output_dir.parent.mkdir(parents=True, exist_ok=True)

    # Build pyarmor CLI command
    # -i: package runtime files inside the obfuscated package directory
    cmd = [sys.executable, "-m", "pyarmor.cli", "gen", "-i", "-O", str(output_dir)]

    if target_platforms:
        print(f"Targeting cross-platform runtimes: {target_platforms}")
        cmd.extend(["--platform", target_platforms])

    cmd.append(str(source_dir))

    print(f"Executing: {' '.join(cmd)}")
    try:
        result = subprocess.run(cmd, check=True, capture_output=True, text=True)
        print(result.stdout)
        if result.stderr:
            print("PyArmor Warnings/Messages:")
            print(result.stderr)
    except subprocess.CalledProcessError as e:
        print(f"ERROR: PyArmor obfuscation failed with exit code {e.returncode}:")
        print(e.stdout)
        print(e.stderr)
        return False
    except FileNotFoundError:
        print("ERROR: PyArmor is not installed or not in PATH.")
        return False

    # Verification Step 1: Verify files were generated
    obfuscated_pkg = output_dir / source_dir.name
    expected_files = ["__init__.py", "calculator.py", "license.py", "cli.py"]

    missing = []
    for fname in expected_files:
        fpath = obfuscated_pkg / fname
        if not fpath.exists():
            missing.append(fname)

    if missing:
        print(f"ERROR: The following expected obfuscated files are missing: {missing}")
        return False

    print("SUCCESS: All expected obfuscated Python files were generated.")

    # Verification Step 2: Verify plain-text sensitive source code is NOT present
    plain_calculator = source_dir / "calculator.py"
    obfuscated_calculator = obfuscated_pkg / "calculator.py"

    original_content = plain_calculator.read_text(encoding="utf-8")
    obfuscated_content = obfuscated_calculator.read_text(encoding="utf-8", errors="ignore")

    sensitive_tokens = [
        "def add(a: Number, b: Number) -> Number:",
        "def subtract(a: Number, b: Number) -> Number:",
        "return a * b",
        "raise ZeroDivisionError(\"Cannot divide by zero\")",
    ]

    leaked = []
    for token in sensitive_tokens:
        if token in obfuscated_content:
            leaked.append(token)

    if leaked:
        print("ERROR: Sensitive plain source code was found intact in obfuscated files:")
        for t in leaked:
            print(f"  - Leaked token: {t}")
        return False

    print("SUCCESS: Source code verification confirmed plain text logic is obfuscated.")
    print("=" * 60)
    return True


def main() -> int:
    parser = argparse.ArgumentParser(description="Run PyArmor obfuscation for securemath")
    parser.add_argument(
        "--source",
        type=Path,
        default=Path("src/securemath"),
        help="Source directory containing packages to obfuscate",
    )
    parser.add_argument(
        "--output",
        type=Path,
        default=Path("obfuscated"),
        help="Output directory for obfuscated package",
    )
    parser.add_argument(
        "--platform",
        type=str,
        default=os.getenv("PYARMOR_PLATFORMS", None),
        help="Target platform(s) for cross-platform runtime, e.g. 'linux.x86_64,alpine.x86_64'",
    )

    args = parser.parse_args()

    success = run_obfuscation(
        source_dir=args.source.resolve(),
        output_dir=args.output.resolve(),
        target_platforms=args.platform,
    )

    return 0 if success else 1


if __name__ == "__main__":
    sys.exit(main())
