#!/usr/bin/env bash
# ==============================================================================
# verify_signature.sh - Artifact Signature & Integrity Verification Script
# ==============================================================================
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(dirname "$SCRIPT_DIR")"

echo "============================================================"
echo "Artifact Signature Verification (Shell Entrypoint)"
echo "============================================================"

# Check if Python 3 is available
if command -v python3 >/dev/null 2>&1; then
    exec python3 "${SCRIPT_DIR}/verify_signature.py" "$@"
elif command -v python >/dev/null 2>&1; then
    exec python "${SCRIPT_DIR}/verify_signature.py" "$@"
else
    echo "ERROR: python3 is required for signature verification."
    exit 1
fi
