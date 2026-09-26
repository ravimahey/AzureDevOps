#!/bin/sh
# ==============================================================================
# run_multi_os_tests.sh - Multi-OS Matrix Test Runner for Container Environments
# POSIX-compliant shell script for Ubuntu, Debian, Alpine (musl), and Fedora
# ==============================================================================
set -eu

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
OS_CLEAN=$(echo "$OS_NAME" | tr ' /' '_')

# 2. Package manager setup if python3 or venv is missing
SUDO=""
if [ "$(id -u 2>/dev/null || echo 1)" -ne 0 ] && command -v sudo >/dev/null 2>&1; then
    SUDO="sudo"
fi

if ! command -v python3 >/dev/null 2>&1; then
    echo "Python 3 not detected. Installing via system package manager..."
    if command -v apk >/dev/null 2>&1; then
        echo "Configuring Alpine package environment (musl libc)..."
        $SUDO apk update >/dev/null 2>&1 || true
        $SUDO apk add --no-cache python3 py3-pip py3-virtualenv py3-pytest >/dev/null 2>&1
    elif command -v apt-get >/dev/null 2>&1; then
        echo "Configuring Debian/Ubuntu package environment (glibc)..."
        export DEBIAN_FRONTEND=noninteractive
        $SUDO apt-get update -qq >/dev/null 2>&1 || true
        $SUDO apt-get install -y -qq python3 python3-pip python3-venv >/dev/null 2>&1
    elif command -v dnf >/dev/null 2>&1; then
        echo "Configuring Fedora package environment..."
        $SUDO dnf install -y -q python3 python3-pip findutils >/dev/null 2>&1
    fi
else
    echo "Python 3 is already installed: $(python3 --version 2>&1)"
    if command -v apk >/dev/null 2>&1; then
        $SUDO apk add --no-cache py3-virtualenv py3-pytest >/dev/null 2>&1 || true
    elif command -v apt-get >/dev/null 2>&1; then
        if ! python3 -m venv --help >/dev/null 2>&1; then
            export DEBIAN_FRONTEND=noninteractive
            $SUDO apt-get update -qq >/dev/null 2>&1 || true
            $SUDO apt-get install -y -qq python3-venv >/dev/null 2>&1 || true
        fi
    fi
fi

# 3. Detect Python Version
PYTHON_BIN="python3"
if ! command -v python3 >/dev/null 2>&1; then
    PYTHON_BIN="python"
fi
PY_VER=$($PYTHON_BIN --version 2>&1 | awk '{print $2}')

# 4. Locate Wheel
WHEEL_FILE=""
for f in "$WHEEL_DIR"/*.whl; do
    if [ -f "$f" ]; then
        WHEEL_FILE="$f"
        break
    fi
done

if [ -z "$WHEEL_FILE" ]; then
    echo "ERROR: No wheel (.whl) found in $WHEEL_DIR"
    exit 1
fi
echo "Found build artifact: $WHEEL_FILE"

# 5. Create clean isolated virtual environment
VENV_DIR="/tmp/test_venv_$$"
$PYTHON_BIN -m venv --system-site-packages "$VENV_DIR" 2>/dev/null || $PYTHON_BIN -m venv "$VENV_DIR"
# shellcheck disable=SC1090
. "$VENV_DIR/bin/activate"

# 6. Install wheel and test dependencies in clean venv
echo "Installing wheel artifact into test venv..."
pip install --break-system-packages "$WHEEL_FILE" 2>/dev/null || pip install "$WHEEL_FILE"
pip install --break-system-packages pytest 2>/dev/null || pip install pytest 2>/dev/null || true

# Prepare test output directories
mkdir -p test-results

UNIT_STATUS="FAIL"
INTEG_STATUS="FAIL"
LICENSE_STATUS="FAIL"
OBF_STATUS="FAIL"

# 7. Run Unit Tests
echo "=== Running Calculator Unit Tests ==="
if pytest "$TEST_DIR/test_calculator.py" --junitxml="test-results/unit-${OS_CLEAN}.xml" -v --tb=short; then
    UNIT_STATUS="PASS"
fi

# 8. Run License Tests
echo "=== Running License Validation Tests ==="
if pytest "$TEST_DIR/test_license.py" --junitxml="test-results/license-${OS_CLEAN}.xml" -v --tb=short; then
    LICENSE_STATUS="PASS"
fi

# 9. Run Obfuscation Integrity Tests
echo "=== Running Obfuscation Integrity Tests ==="
if pytest "$TEST_DIR/test_obfuscation.py" --junitxml="test-results/obfuscation-${OS_CLEAN}.xml" -v --tb=short; then
    OBF_STATUS="PASS"
fi

# 10. Run Integration Tests (CLI execution)
echo "=== Running CLI Integration Tests ==="
CLI_BIN="$VENV_DIR/bin/securemath"
if [ ! -f "$CLI_BIN" ]; then
    CLI_BIN="securemath"
fi

CLI_OUT_1=$($CLI_BIN add 10 20 2>&1 || true)
CLI_OUT_2=$($CLI_BIN multiply 5 10 2>&1 || true)

if [ "$CLI_OUT_1" = "30" ] && [ "$CLI_OUT_2" = "50" ]; then
    INTEG_STATUS="PASS"
else
    echo "ERROR: CLI Integration Output Mismatch:"
    echo "  securemath add 10 20 output: $CLI_OUT_1"
    echo "  securemath multiply 5 10 output: $CLI_OUT_2"
fi

# Clean up temporary venv
deactivate || true
rm -rf "$VENV_DIR"
chmod -R 777 test-results 2>/dev/null || true

# 11. Print standardized test banner matching Section 13
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
