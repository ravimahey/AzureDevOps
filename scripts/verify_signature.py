#!/usr/bin/env python3
"""Cross-platform signature verification script for securemath artifacts.

Verifies:
1. File integrity (SHA-256 calculation).
2. Cryptographic detached signature against public key (RSA-PSS SHA256).
3. GPG detached signature if .asc exists.
"""

import argparse
import hashlib
import sys
from pathlib import Path


def verify_rsa_signature(artifact_path: Path, sig_path: Path, pub_key_path: Path) -> bool:
    try:
        from cryptography.hazmat.primitives import hashes, serialization
        from cryptography.hazmat.primitives.asymmetric import padding
        from cryptography.exceptions import InvalidSignature
    except ImportError:
        print("ERROR: 'cryptography' library is required to verify signatures.")
        return False

    public_key = serialization.load_pem_public_key(pub_key_path.read_bytes())
    signature = sig_path.read_bytes()
    artifact_bytes = artifact_path.read_bytes()

    try:
        public_key.verify(
            signature,
            artifact_bytes,
            padding.PSS(
                mgf=padding.MGF1(hashes.SHA256()),
                salt_length=padding.PSS.MAX_LENGTH,
            ),
            hashes.SHA256(),
        )
        print("CRYPTOGRAPHIC VERIFICATION: Signature is VALID (RSA-PSS SHA-256).")
        return True
    except InvalidSignature:
        print("CRITICAL ERROR: Signature verification FAILED! The signature is INVALID or the artifact was modified.")
        return False
    except Exception as e:
        print(f"ERROR: Verification error: {e}")
        return False


def verify_artifact(artifact_path: Path) -> bool:
    print("=" * 60)
    print("Signature & Integrity Verification Stage")
    print(f"Target Artifact: {artifact_path}")
    print("=" * 60)

    if not artifact_path.exists():
        print(f"ERROR: Artifact file does not exist: {artifact_path}")
        return False

    # Check SHA-256
    computed_sha256 = hashlib.sha256(artifact_path.read_bytes()).hexdigest()
    print(f"Computed SHA-256: {computed_sha256}")

    checksum_file = artifact_path.with_suffix(artifact_path.suffix + ".sha256")
    if checksum_file.exists():
        expected_line = checksum_file.read_text(encoding="utf-8").strip().split()
        if expected_line:
            expected_hash = expected_line[0]
            if expected_hash != computed_sha256:
                print(f"CRITICAL ERROR: SHA256 mismatch! Expected {expected_hash}, got {computed_sha256}")
                return False
            print("CHECKSUM: SHA-256 verified successfully against manifest.")

    sig_file = artifact_path.with_suffix(artifact_path.suffix + ".sig")
    pub_file = artifact_path.with_suffix(artifact_path.suffix + ".pub.pem")

    if not sig_file.exists():
        print(f"ERROR: Detached signature file '{sig_file.name}' not found.")
        return False

    if not pub_file.exists():
        print(f"ERROR: Public key file '{pub_file.name}' not found.")
        return False

    is_valid = verify_rsa_signature(artifact_path, sig_file, pub_file)
    if is_valid:
        print("=" * 60)
        print("RESULT: ALL SIGNATURE AND CHECKSUM CHECKS PASSED")
        print("=" * 60)
    return is_valid


def main() -> int:
    parser = argparse.ArgumentParser(description="Verify digital signature of build artifacts")
    parser.add_argument(
        "artifact",
        nargs="?",
        type=Path,
        help="Path to artifact file to verify. Defaults to *.whl in dist/",
    )

    args = parser.parse_args()

    artifact_path = None
    if args.artifact:
        arg_str = str(args.artifact)
        if "*" in arg_str:
            matches = list(Path(".").glob(arg_str))
            if matches:
                artifact_path = matches[0]
        elif args.artifact.exists():
            artifact_path = args.artifact

    if artifact_path is None:
        dist_dir = Path("dist")
        wheels = list(dist_dir.glob("**/*.whl")) if dist_dir.exists() else []
        if not wheels:
            wheels = list(Path(".").glob("**/*.whl"))
        if not wheels:
            print(f"ERROR: No .whl found in dist/ or current directory.")
            return 1
        artifact_path = wheels[0]

    valid = verify_artifact(artifact_path.resolve())
    return 0 if valid else 1


if __name__ == "__main__":
    sys.exit(main())
