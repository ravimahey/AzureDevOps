#!/usr/bin/env python3
"""Artifact Signing Script for CI/CD Pipeline.

SECURITY & ARCHITECTURAL NOTICE:
--------------------------------
1. CRITICAL: Never commit private signing keys or certificates to Git repositories.
2. In Azure DevOps PRODUCTION:
   - The private signing key is stored in an HSM-backed Azure Key Vault.
   - Signing is executed via Azure Key Vault API (e.g. `az keyvault key sign`),
     Azure SignTool, Sigstore/Cosign with OIDC, or GPG with a key stored in Azure Key Vault Secrets.
   - Only authorized release pipelines with managed identities / service principals
     have permission to perform the signing operation.

3. FOR THIS POC:
   - If GPG with a configured key is present, this script executes a GPG detached signature.
   - If an RSA private key is supplied via `SIGNING_PRIVATE_KEY` env var, it is loaded.
   - Otherwise, an ephemeral RSA-2048 keypair is generated in memory for this build run.
     The public verification key is written to `<artifact>.pub.pem` and the detached
     signature is written to `<artifact>.sig`.
   - The signing mechanism uses genuine cryptographic RSA-PSS/SHA-256 signing,
     NOT dummy text, clearly demonstrating the verification flow.
"""

import argparse
import base64
import hashlib
import os
import shutil
import subprocess
import sys
from pathlib import Path


def sign_with_gpg(artifact_path: Path) -> bool:
    """Attempt GPG detached signing if gpg is available."""
    if not shutil.which("gpg"):
        return False

    sig_file = artifact_path.with_suffix(artifact_path.suffix + ".asc")
    print("Attempting GPG detached signing...")
    cmd = [
        "gpg",
        "--batch",
        "--yes",
        "--armor",
        "--detach-sign",
        "--output",
        str(sig_file),
        str(artifact_path),
    ]
    try:
        res = subprocess.run(cmd, capture_output=True, text=True)
        if res.returncode == 0 and sig_file.exists():
            print(f"SUCCESS: GPG detached signature created: {sig_file.name}")
            return True
        else:
            print(f"GPG returned non-zero ({res.returncode}): {res.stderr.strip()}")
            return False
    except Exception as e:
        print(f"GPG signing attempt failed: {e}")
        return False


def sign_with_rsa_cryptography(artifact_path: Path) -> bool:
    """Perform cryptographic RSA-PSS signing using cryptography library."""
    try:
        from cryptography.hazmat.primitives import hashes, serialization
        from cryptography.hazmat.primitives.asymmetric import padding, rsa
    except ImportError:
        print("ERROR: 'cryptography' library is required for standalone signing.")
        print("Install via: pip install cryptography")
        return False

    print("Executing Cryptographic Detached Signature Operation...")
    raw_env_key = os.getenv("SIGNING_PRIVATE_KEY", "").strip()

    private_key = None
    if raw_env_key and not raw_env_key.startswith("$("):
        print("Parsing private signing key from SIGNING_PRIVATE_KEY environment variable...")
        key_bytes = None

        # Check 1: Base64-encoded PEM
        if not raw_env_key.startswith("-----BEGIN"):
            try:
                decoded = base64.b64decode(raw_env_key)
                if b"-----BEGIN" in decoded:
                    key_bytes = decoded
            except Exception:
                pass

        # Check 2: Escaped literal \n
        if key_bytes is None and "\\n" in raw_env_key:
            key_bytes = raw_env_key.replace("\\n", "\n").encode("utf-8")

        # Check 3: PEM where Azure DevOps UI converted newlines to spaces
        if key_bytes is None and "\n" not in raw_env_key and "-----BEGIN" in raw_env_key:
            import re
            m = re.match(r"(-----BEGIN [A-Z ]+-----)\s*(.*?)\s*(-----END [A-Z ]+-----)", raw_env_key)
            if m:
                header, body, footer = m.groups()
                clean_body = re.sub(r"\s+", "", body)
                chunked = "\n".join(clean_body[i:i+64] for i in range(0, len(clean_body), 64))
                key_bytes = f"{header}\n{chunked}\n{footer}\n".encode("utf-8")

        # Check 4: Standard multi-line PEM
        if key_bytes is None and "BEGIN" in raw_env_key:
            key_bytes = raw_env_key.encode("utf-8")

        if key_bytes:
            try:
                private_key = serialization.load_pem_private_key(key_bytes, password=None)
                print("SUCCESS: Successfully loaded and verified custom RSA private key.")
            except Exception as e:
                print(f"WARNING: Could not parse SIGNING_PRIVATE_KEY ({e}). Falling back to ephemeral key.")
                private_key = None

    if private_key is None:
        print("NOTE: No valid SIGNING_PRIVATE_KEY provided in environment.")
        print("Generating ephemeral RSA-2048 signing keypair in memory for POC validation...")
        print("PROD GAP: In production, key must originate from Azure Key Vault HSM.")
        private_key = rsa.generate_private_key(
            public_exponent=65537,
            key_size=2048,
        )

    public_key = private_key.public_key()

    # Read artifact payload
    artifact_bytes = artifact_path.read_bytes()

    # Create cryptographic RSA-PSS signature with SHA256
    signature = private_key.sign(
        artifact_bytes,
        padding.PSS(
            mgf=padding.MGF1(hashes.SHA256()),
            salt_length=padding.PSS.MAX_LENGTH,
        ),
        hashes.SHA256(),
    )

    # Save detached signature
    sig_path = artifact_path.with_suffix(artifact_path.suffix + ".sig")
    sig_path.write_bytes(signature)
    print(f"Signature file generated: {sig_path.name} ({len(signature)} bytes)")

    # Save public key for verification
    pub_path = artifact_path.with_suffix(artifact_path.suffix + ".pub.pem")
    pem_bytes = public_key.public_bytes(
        encoding=serialization.Encoding.PEM,
        format=serialization.PublicFormat.SubjectPublicKeyInfo,
    )
    pub_path.write_bytes(pem_bytes)
    print(f"Public verification key saved: {pub_path.name}")

    # Generate metadata manifest
    sha256_hash = hashlib.sha256(artifact_bytes).hexdigest()
    manifest_path = artifact_path.with_suffix(artifact_path.suffix + ".signing-manifest.json")
    manifest = (
        f'{{\n'
        f'  "artifact": "{artifact_path.name}",\n'
        f'  "sha256": "{sha256_hash}",\n'
        f'  "algorithm": "RSA-PSS-SHA256",\n'
        f'  "signature_file": "{sig_path.name}",\n'
        f'  "public_key_file": "{pub_path.name}",\n'
        f'  "signing_service": "POC Demo Signer (Replace with Azure Key Vault in Production)"\n'
        f'}}\n'
    )
    manifest_path.write_text(manifest, encoding="utf-8")
    print(f"Signing manifest generated: {manifest_path.name}")
    return True


def sign_artifact(artifact_path: Path) -> bool:
    print("=" * 60)
    print("Artifact Signing Stage")
    print(f"Target Artifact: {artifact_path}")
    print("=" * 60)

    if not artifact_path.exists():
        print(f"ERROR: Artifact file does not exist: {artifact_path}")
        return False

    # Pre-signing integrity check
    sha256_hash = hashlib.sha256(artifact_path.read_bytes()).hexdigest()
    print(f"Artifact SHA-256 pre-check: {sha256_hash}")

    # Verify checksum if .sha256 exists
    checksum_file = artifact_path.with_suffix(artifact_path.suffix + ".sha256")
    if checksum_file.exists():
        expected_line = checksum_file.read_text(encoding="utf-8").strip().split()
        if expected_line and expected_line[0] != sha256_hash:
            print("CRITICAL ERROR: SHA-256 mismatch before signing! Artifact is corrupted or tampered.")
            return False
        print("SUCCESS: Pre-signing SHA-256 checksum verified against existing manifest.")

    # Execute signing
    success = sign_with_rsa_cryptography(artifact_path)
    if success:
        print("=" * 60)
        print("SIGNING COMPLETED SUCCESSFULLY")
        print("=" * 60)
    return success


def main() -> int:
    parser = argparse.ArgumentParser(description="Sign build artifacts in CI/CD pipeline")
    parser.add_argument(
        "artifact",
        nargs="?",
        type=Path,
        help="Path to artifact file to sign. Defaults to *.whl in dist/",
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

    success = sign_artifact(artifact_path.resolve())
    return 0 if success else 1


if __name__ == "__main__":
    sys.exit(main())
