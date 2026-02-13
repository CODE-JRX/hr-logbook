"""Create a clean `dist/` package containing only files required to deploy the app.

Run from the repo root:
    python scripts/package_dist.py

This will create/overwrite the `dist/` directory.
"""
import os
import shutil
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DIST = ROOT / "dist"

# Files and directories to include (relative to repo root)
INCLUDE_FILES = [
    "app.py",
    "wsgi.py",
    "db.py",
    "init_mongo.py",
    "run.bat",
    "requirements.txt",
    "README_DEPLOY.md",
    ".env.example",
    "run_run.vbs",
]

INCLUDE_DIRS = [
    "models",
    "routes",
    "templates",
    "static",
]

IGNORE_DIRS = {"__pycache__", "backup", "logs", ".git", ".venv", "venv"}


def copy_file(src: Path, dest_dir: Path):
    dest = dest_dir / src.name
    dest_dir.mkdir(parents=True, exist_ok=True)
    shutil.copy2(src, dest)


def copy_dir(src: Path, dest_dir: Path):
    dest = dest_dir / src.name
    if dest.exists():
        shutil.rmtree(dest)
    shutil.copytree(src, dest, ignore=shutil.ignore_patterns("__pycache__", "*.pyc", "*.pyo", "*.swp"))


def main():
    if not ROOT.exists():
        print("Cannot determine repository root")
        return

    if DIST.exists():
        print(f"Removing existing {DIST}")
        shutil.rmtree(DIST)

    DIST.mkdir()

    # Copy files
    for f in INCLUDE_FILES:
        src = ROOT / f
        if src.exists():
            print(f"Copying file: {f}")
            copy_file(src, DIST)
        else:
            print(f"Warning: file not found: {f}")

    # Copy directories
    for d in INCLUDE_DIRS:
        src = ROOT / d
        if src.exists() and src.is_dir() and src.name not in IGNORE_DIRS:
            print(f"Copying dir: {d}")
            copy_dir(src, DIST)
        else:
            print(f"Warning: dir not found or ignored: {d}")

    print("Package ready in:", DIST)


if __name__ == "__main__":
    main()
