#!/usr/bin/env bash
# ==============================================================================
# run_multi_os_tests.sh - Multi-OS Matrix Test Runner for Container Environments
# ==============================================================================
set -euo pipefail

WHEEL_DIR="${1:-dist}"
TEST_DIR="${2:-tests}"

echo "Starting Multi-OS Test Execution..."

# 1. Detect OS from /etc/os-release
OS_NAME="Linux"
if [ -f /etc/os-release ]; then
    # shellcheck disable=SC1091
    . /etc/os-release
    OS_NAME="${NAME:-Linux}"
fi

# Package manager setup if running in minimal container
if command -v apk >/dev/null 2>&1; then
    # Alpine Linux (musl libc)
    echo "Configuring Alpine package environment..."
    apk update && apk add --no-cache python3 py3-pip py3-virtualenv bash
elif command -v apt-get >/dev/null 2>&1; then
    # Debian / Ubuntu (glibc)
    echo "Configuring Debian/Ubuntu package environment..."
    export DEBIAN_FRONTEND=noninteractive
    apt-get update -qq && apt-get install -y -qq python3 python3-pip python3-venv >/dev/null
elif command -v dnf >/dev/null 2>&1; then
    # Fedora / RHEL
    echo "Configuring Fedora package environment..."
    dnf install -y -q python3 python3-pip >/dev/null
fi

# 2. Detect Python Version
PYTHON_BIN="python3"
if ! command -v python3 >/dev/null 2>&1; then
    PYTHON_BIN="python"
fi
PY_VER=$($PYTHON_BIN --version 2>&1 | awk '{print $2}')

# 3. Locate Wheel
WHEEL_FILE=$(find "$WHEEL_DIR" -name "*.whl" | head -n 1)
if [ -z "$WHEEL_FILE" ]; then
    echo "ERROR: No wheel (.whl) found in $WHEEL_DIR"
    exit 1
fi
echo "Found build artifact: $WHEEL_FILE"

# 4. Create clean isolated virtual environment
VENV_DIR="/tmp/test_venv_$$"
$PYTHON_BIN -m venv "$VENV_DIR"
# shellcheck disable=SC1091
source "$VENV_DIR/bin/activate"

# 5. Install wheel and test dependencies in clean venv
pip install --upgrade pip >/dev/null 2>&1 || true
pip install "$WHEEL_FILE" >/dev/null
pip install pytest >/dev/null

# Prepare test output directories
mkdir -p test-results

UNIT_STATUS="FAIL"
INTEG_STATUS="FAIL"
LICENSE_STATUS="FAIL"
OBF_STATUS="FAIL"

# 6. Run Unit Tests
if pytest "$TEST_DIR/test_calculator.py" --junitxml="test-results/unit-${OS_NAME}.xml" -q; then
    UNIT_STATUS="PASS"
fi

# 7. Run License Tests
if pytest "$TEST_DIR/test_license.py" --junitxml="test-results/license-${OS_NAME}.xml" -q; then
    LICENSE_STATUS="PASS"
fi

# 8. Run Obfuscation Integrity Tests
if pytest "$TEST_DIR/test_obfuscation.py" --junitxml="test-results/obfuscation-${OS_NAME}.xml" -q; then
    OBF_STATUS="PASS"
fi

# 9. Run Integration Tests (CLI execution)
CLI_OUT_1=$(securemath add 10 20 || true)
CLI_OUT_2=$(securemath multiply 5 10 || true)

if [ "$CLI_OUT_1" = "30" ] && [ "$CLI_OUT_2" = "50" ]; then
    INTEG_STATUS="PASS"
fi

# Clean up temporary venv
deactivate
rm -rf "$VENV_DIR"

# 10. Print standardized test banner matching Section 13
echo ""
echo "================================"
echo "securemath test"
echo "OS: $OS_NAME"
echo "Python: $PY_VER"
echo "================================"
echo ""
echo "Unit tests: $UNIT_STATUS"
echo "Integration tests: $INTEG_STATUS"
echo "License tests: $LICENSE_STATUS"
echo "Obfuscation tests: $OBF_STATUS"
echo ""

if [ "$UNIT_STATUS" = "PASS" ] && [ "$INTEG_STATUS" = "PASS" ] && \
   [ "$LICENSE_STATUS" = "PASS" ] && [ "$OBF_STATUS" = "PASS" ]; then
    echo "RESULT: PASS"
    exit 0
else
    echo "RESULT: FAIL"
    exit 1
fi
