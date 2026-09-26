#!/usr/bin/env python3
"""Artifact Validator for Python Wheels.

Validates:
1. Wheel file existence in target directory.
2. Non-zero file size.
3. SHA-256 cryptographic digest calculation.
4. Wheel filename conformance with PEP 427 conventions.
5. Wheel internal structure and METADATA extraction.
"""

import argparse
import hashlib
import re
import sys
import zipfile
from pathlib import Path

# Wheel filename regex: {distribution}-{version}(-{build_tag})?-{python_tag}-{abi_tag}-{platform_tag}.whl
WHEEL_REGEX = re.compile(
    r"^(?P<distribution>[A-Za-z0-9_]+)-(?P<version>[0-9A-Za-z.+_-]+)"
    r"(-(?P<build>[0-9A-Za-z]+))?-(?P<python>[A-Za-z0-9.]+)"
    r"-(?P<abi>[A-Za-z0-9.]+)-(?P<platform>[A-Za-z0-9.]+)\.whl$"
)


def calculate_sha256(filepath: Path) -> str:
    """Calculate the SHA-256 checksum of a file."""
    sha256 = hashlib.sha256()
    with open(filepath, "rb") as f:
        while chunk := f.read(65536):
            sha256.update(chunk)
    return sha256.hexdigest()


def validate_wheel(wheel_path: Path, expected_name: str = "securemath") -> bool:
    print("Artifact validation started.\n")

    # Check 1: Existence
    if not wheel_path.exists():
        print(f"ERROR: Artifact file does not exist: {wheel_path}")
        print("\nArtifact status:\nINVALID")
        return False

    # Check 2: Non-zero size
    file_size = wheel_path.stat().st_size
    if file_size <= 0:
        print(f"ERROR: Artifact file is empty (0 bytes): {wheel_path}")
        print("\nArtifact status:\nINVALID")
        return False

    # Check 3 & 4: SHA-256 calculation
    sha256_hash = calculate_sha256(wheel_path)

    # Check 5: Filename validation
    match = WHEEL_REGEX.match(wheel_path.name)
    if not match:
        print(f"ERROR: Artifact does not match PEP 427 wheel naming convention: {wheel_path.name}")
        print("\nArtifact status:\nINVALID")
        return False

    pkg_name = match.group("distribution")
    if pkg_name.lower() != expected_name.lower():
        print(f"ERROR: Expected package name '{expected_name}', but wheel is '{pkg_name}'")
        print("\nArtifact status:\nINVALID")
        return False

    # Check 6: Inspect Wheel Metadata
    try:
        with zipfile.ZipFile(wheel_path, "r") as zf:
            namelist = zf.namelist()
            metadata_files = [f for f in namelist if f.endswith(".dist-info/METADATA")]
            if not metadata_files:
                print(f"ERROR: Wheel is missing .dist-info/METADATA inside archive.")
                print("\nArtifact status:\nINVALID")
                return False

            metadata_content = zf.read(metadata_files[0]).decode("utf-8", errors="ignore")
            if f"Name: {expected_name}" not in metadata_content:
                print(f"WARNING: 'Name: {expected_name}' not found in METADATA header.")

    except zipfile.BadZipFile:
        print(f"ERROR: File is not a valid zip/wheel archive: {wheel_path}")
        print("\nArtifact status:\nINVALID")
        return False

    # Print formatted output matching specification
    print(f"Artifact:\n{wheel_path.as_posix()}\n")
    print(f"Size:\n{file_size} bytes\n")
    print(f"SHA256:\n{sha256_hash}\n")
    print("Artifact status:\nVALID")

    # Save checksum file alongside artifact
    checksum_file = wheel_path.with_suffix(wheel_path.suffix + ".sha256")
    checksum_file.write_text(f"{sha256_hash}  {wheel_path.name}\n", encoding="utf-8")

    return True


def main() -> int:
    parser = argparse.ArgumentParser(description="Validate generated Python wheel artifact")
    parser.add_argument(
        "wheel",
        nargs="?",
        type=Path,
        help="Path to .whl file. If omitted, searches in dist/",
    )
    parser.add_argument(
        "--expected-name",
        type=str,
        default="securemath",
        help="Expected package name (default: securemath)",
    )

    args = parser.parse_args()

    if args.wheel:
        wheel_path = args.wheel
    else:
        dist_dir = Path("dist")
        wheels = list(dist_dir.glob("*.whl")) if dist_dir.exists() else []
        if not wheels:
            print(f"ERROR: No .whl found in {dist_dir.resolve()}. Run build first.")
            print("\nArtifact status:\nINVALID")
            return 1
        wheel_path = wheels[0]

    valid = validate_wheel(wheel_path.resolve(), expected_name=args.expected_name)
    return 0 if valid else 1


if __name__ == "__main__":
    sys.exit(main())
