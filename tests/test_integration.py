"""Integration tests for securemath CLI and package workflows."""

import subprocess
import sys
from pathlib import Path
import pytest


repo_root = Path(__file__).resolve().parent.parent
src_dir = repo_root / "src"


def _run_cli(args):
    """Run securemath CLI with PYTHONPATH pointing to src."""
    import os
    env = os.environ.copy()
    env["PYTHONPATH"] = str(src_dir)
    cmd = [sys.executable, "-m", "securemath.cli"] + args
    return subprocess.run(cmd, capture_output=True, text=True, env=env)


class TestCLIIntegration:
    """Test CLI commands via subprocess."""

    def test_cli_add(self):
        res = _run_cli(["add", "10", "20"])
        assert res.returncode == 0
        assert res.stdout.strip() == "30"

    def test_cli_multiply(self):
        res = _run_cli(["multiply", "5", "10"])
        assert res.returncode == 0
        assert res.stdout.strip() == "50"

    def test_cli_subtract(self):
        res = _run_cli(["subtract", "20", "10"])
        assert res.returncode == 0
        assert res.stdout.strip() == "10"

    def test_cli_divide(self):
        res = _run_cli(["divide", "10", "2"])
        assert res.returncode == 0
        assert res.stdout.strip() == "5"

    def test_cli_divide_by_zero_exits_nonzero(self):
        res = _run_cli(["divide", "10", "0"])
        assert res.returncode != 0
        assert "Cannot divide by zero" in res.stderr

    def test_cli_version(self):
        res = _run_cli(["--version"])
        assert res.returncode == 0
        assert "securemath 0.1.0" in res.stdout


def test_wheel_isolated_venv_integration(tmp_path):
    """If a wheel exists in dist/, install into clean isolated venv and test binary."""
    repo_root = Path(__file__).resolve().parent.parent
    dist_dir = repo_root / "dist"
    wheels = list(dist_dir.glob("*.whl")) if dist_dir.exists() else []

    if not wheels:
        pytest.skip("No wheel found in dist/ to test isolated installation.")

    wheel_path = wheels[0]
    venv_dir = tmp_path / "test_venv"

    # Create virtual environment
    subprocess.run([sys.executable, "-m", "venv", str(venv_dir)], check=True)

    # Determine binary paths for Windows vs POSIX
    if sys.platform == "win32":
        pip_bin = venv_dir / "Scripts" / "pip.exe"
        cli_bin = venv_dir / "Scripts" / "securemath.exe"
    else:
        pip_bin = venv_dir / "bin" / "pip"
        cli_bin = venv_dir / "bin" / "securemath"

    # Install the built wheel
    subprocess.run([str(pip_bin), "install", str(wheel_path)], check=True)

    # Test CLI binary execution: add 10 20
    res_add = subprocess.run([str(cli_bin), "add", "10", "20"], capture_output=True, text=True, check=True)
    assert res_add.stdout.strip() == "30"

    # Test CLI binary execution: multiply 5 10
    res_mul = subprocess.run([str(cli_bin), "multiply", "5", "10"], capture_output=True, text=True, check=True)
    assert res_mul.stdout.strip() == "50"
