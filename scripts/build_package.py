#!/usr/bin/env python3
"""Build runner for securemath package.

Builds Python wheel and sdist into dist/ directory using PEP 517/518 'build'.
Supports packaging either standard development sources or obfuscated production sources.
"""

import argparse
import os
import shutil
import subprocess
import sys
from pathlib import Path


def build_package(use_obfuscated: bool = True, output_dir: Path = Path("dist")) -> bool:
    repo_root = Path(__file__).resolve().parent.parent
    obfuscated_dir = repo_root / "obfuscated" / "securemath"
    dist_dir = (repo_root / output_dir).resolve()
    dist_dir.mkdir(parents=True, exist_ok=True)

    print("=" * 60)
    print("Building securemath Distribution Package")
    print(f"Mode: {'Obfuscated (Production POC)' if use_obfuscated else 'Standard (Source)'}")
    print(f"Target dist directory: {dist_dir}")
    print("=" * 60)

    if use_obfuscated:
        if not obfuscated_dir.exists():
            print(f"ERROR: Obfuscated directory '{obfuscated_dir}' not found.")
            print("Run 'python scripts/obfuscate.py' before packaging.")
            return False

        # Stage files into isolated build staging directory
        staging_dir = repo_root / "build_stage"
        if staging_dir.exists():
            shutil.rmtree(staging_dir)
        staging_src = staging_dir / "src" / "securemath"
        staging_src.parent.mkdir(parents=True, exist_ok=True)

        print(f"Staging obfuscated package into: {staging_src}")
        shutil.copytree(obfuscated_dir, staging_src)

        # Copy packaging config files
        shutil.copy2(repo_root / "pyproject.toml", staging_dir / "pyproject.toml")
        shutil.copy2(repo_root / "README.md", staging_dir / "README.md")
        if (repo_root / "LICENSE").exists():
            shutil.copy2(repo_root / "LICENSE", staging_dir / "LICENSE")

        cmd = [
            sys.executable,
            "-m",
            "build",
            "--outdir",
            str(dist_dir),
            str(staging_dir),
        ]
        try:
            print(f"Running: {' '.join(cmd)}")
            subprocess.run(cmd, check=True)
        finally:
            # Clean staging directory
            if staging_dir.exists():
                shutil.rmtree(staging_dir)
    else:
        # Standard build from repository root
        cmd = [sys.executable, "-m", "build", "--outdir", str(dist_dir), str(repo_root)]
        print(f"Running: {' '.join(cmd)}")
        subprocess.run(cmd, check=True)

    print("Build completed successfully.")
    return True


def main() -> int:
    parser = argparse.ArgumentParser(description="Build securemath wheel and sdist")
    parser.add_argument(
        "--obfuscated",
        action="store_true",
        default=True,
        help="Build wheel from obfuscated code (default: True)",
    )
    parser.add_argument(
        "--plain",
        action="store_false",
        dest="obfuscated",
        help="Build wheel from plain source code",
    )
    parser.add_argument(
        "--outdir",
        type=Path,
        default=Path("dist"),
        help="Output directory for generated packages (default: dist)",
    )

    args = parser.parse_args()
    success = build_package(use_obfuscated=args.obfuscated, output_dir=args.outdir)
    return 0 if success else 1


if __name__ == "__main__":
    sys.exit(main())
