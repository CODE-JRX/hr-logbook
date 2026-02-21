"""
setup_chrome_camera.py
======================
Automates Google Chrome setup on a target machine to allow camera access
over HTTP (insecure origin) for the HRMO e-Logbook web project.

What this script does:
  1. Locates Chrome's Default profile Preferences file.
  2. Grants camera permission for the specified HTTP origin in Chrome's
     content settings (equivalent to clicking "Allow" in the browser).
  3. Writes a small launcher batch file (run_chrome_logbook.bat) to the
     Desktop that launches Chrome with the --unsafely-treat-insecure-origin-as-secure
     flag as a belt-and-suspenders fallback.

Usage:
  python setup_chrome_camera.py [--url http://HOST:PORT]

Defaults to http://10.0.0.1:5000 if no --url is provided.
"""

import argparse
import json
import os
import platform
import shutil
import subprocess
import sys
import time
from pathlib import Path
from urllib.parse import urlparse

# ── Defaults ──────────────────────────────────────────────────────────────────
DEFAULT_URL = "http://10.0.0.1:5000"
LAUNCHER_NAME = "run_chrome_logbook.bat"

# ── Helpers ───────────────────────────────────────────────────────────────────

def find_chrome_user_data_dir() -> Path | None:
    """Return the Chrome user-data directory for the current OS/user."""
    system = platform.system()
    if system == "Windows":
        candidates = [
            Path(os.environ.get("LOCALAPPDATA", "")) / "Google" / "Chrome" / "User Data",
        ]
    elif system == "Darwin":
        candidates = [
            Path.home() / "Library" / "Application Support" / "Google" / "Chrome",
        ]
    else:  # Linux
        candidates = [
            Path.home() / ".config" / "google-chrome",
            Path.home() / ".config" / "chromium",
        ]

    for path in candidates:
        if path.exists():
            return path
    return None


def find_chrome_executable() -> str | None:
    """Return the path to the Chrome executable."""
    system = platform.system()
    if system == "Windows":
        candidates = [
            r"C:\Program Files\Google\Chrome\Application\chrome.exe",
            r"C:\Program Files (x86)\Google\Chrome\Application\chrome.exe",
            Path(os.environ.get("LOCALAPPDATA", "")) / "Google" / "Chrome" / "Application" / "chrome.exe",
        ]
        for c in candidates:
            if Path(c).exists():
                return str(c)
    elif system == "Darwin":
        path = Path("/Applications/Google Chrome.app/Contents/MacOS/Google Chrome")
        if path.exists():
            return str(path)
    else:
        for exe in ("google-chrome", "google-chrome-stable", "chromium-browser", "chromium"):
            found = shutil.which(exe)
            if found:
                return found
    return None


def url_to_origin(url: str) -> str:
    """Convert a full URL to its bare origin (scheme://host:port)."""
    parsed = urlparse(url)
    origin = f"{parsed.scheme}://{parsed.hostname}"
    if parsed.port:
        origin += f":{parsed.port}"
    return origin


def kill_chrome():
    """Attempt to gracefully kill running Chrome processes so we can edit prefs."""
    system = platform.system()
    print("  Attempting to close Chrome (needed to safely edit preferences)...")
    try:
        if system == "Windows":
            subprocess.run(["taskkill", "/F", "/IM", "chrome.exe"],
                           capture_output=True, check=False)
        else:
            subprocess.run(["pkill", "-x", "Google Chrome"],
                           capture_output=True, check=False)
            subprocess.run(["pkill", "-x", "chrome"],
                           capture_output=True, check=False)
        time.sleep(1)
    except Exception as exc:
        print(f"  Warning: could not close Chrome automatically: {exc}")


def patch_preferences(prefs_path: Path, origin: str) -> bool:
    """
    Add the HTTP origin to Chrome's camera allow-list in Preferences.
    Returns True if the file was modified, False if it was already set.
    """
    with open(prefs_path, "r", encoding="utf-8") as fh:
        prefs: dict = json.load(fh)

    # Navigate / create the nested key path safely
    profile = prefs.setdefault("profile", {})
    content_settings = profile.setdefault("content_settings", {})
    exceptions = content_settings.setdefault("exceptions", {})
    media_stream_camera = exceptions.setdefault("media_stream_camera", {})

    compound_key = f"{origin},*"

    already_set = (
        compound_key in media_stream_camera
        and media_stream_camera[compound_key].get("setting") == 1
    )

    if already_set:
        return False

    media_stream_camera[compound_key] = {
        "last_modified": str(int(time.time() * 1000000)),
        "setting": 1,          # 1 = ALLOW
    }

    # Back up the original
    backup = prefs_path.with_suffix(".bak")
    shutil.copy2(prefs_path, backup)
    print(f"  Backed up original Preferences → {backup}")

    with open(prefs_path, "w", encoding="utf-8") as fh:
        json.dump(prefs, fh, separators=(",", ":"))

    return True


def create_launcher(chrome_exe: str, origin: str, url: str) -> Path:
    """
    Write a .bat launcher to the Desktop that opens Chrome with the
    --unsafely-treat-insecure-origin-as-secure flag pointing at the origin.
    """
    desktop = Path.home() / "Desktop"
    desktop.mkdir(exist_ok=True)
    launcher = desktop / LAUNCHER_NAME

    # Windows batch file
    content = f"""@echo off
:: HRMO e-Logbook – Chrome launcher (HTTP camera access enabled)
:: Generated by setup_chrome_camera.py
start "" "{chrome_exe}" ^
  --unsafely-treat-insecure-origin-as-secure={origin} ^
  --user-data-dir="%LOCALAPPDATA%\\Google\\Chrome\\User Data" ^
  {url}
"""
    launcher.write_text(content, encoding="utf-8")
    return launcher


# ── Main ──────────────────────────────────────────────────────────────────────

def main():
    parser = argparse.ArgumentParser(
        description="Configure Chrome to allow camera access over HTTP for the HRMO e-Logbook."
    )
    parser.add_argument(
        "--url",
        default=DEFAULT_URL,
        help=f"Full URL of the web app (default: {DEFAULT_URL})",
    )
    parser.add_argument(
        "--no-kill",
        action="store_true",
        help="Skip closing Chrome before editing preferences (risky).",
    )
    args = parser.parse_args()

    target_url = args.url.rstrip("/")
    origin = url_to_origin(target_url)

    print("=" * 60)
    print("  HRMO e-Logbook – Chrome Camera Setup")
    print("=" * 60)
    print(f"  Target URL    : {target_url}")
    print(f"  Origin        : {origin}")
    print()

    # ── Step 1: Find Chrome ───────────────────────────────────────────────────
    print("[1/4] Locating Chrome executable...")
    chrome_exe = find_chrome_executable()
    if not chrome_exe:
        print("  ERROR: Google Chrome not found. Please install Chrome first.")
        sys.exit(1)
    print(f"  Found: {chrome_exe}")

    # ── Step 2: Find user data directory ─────────────────────────────────────
    print("[2/4] Locating Chrome user data directory...")
    user_data_dir = find_chrome_user_data_dir()
    if not user_data_dir:
        print("  ERROR: Chrome user data directory not found.")
        sys.exit(1)
    print(f"  Found: {user_data_dir}")

    prefs_path = user_data_dir / "Default" / "Preferences"
    if not prefs_path.exists():
        print(f"  ERROR: Preferences file not found at: {prefs_path}")
        print("  Tip: Open Chrome at least once to create the Default profile.")
        sys.exit(1)

    # ── Step 3: Patch Preferences ─────────────────────────────────────────────
    print("[3/4] Patching Chrome Preferences to allow camera on HTTP...")
    if not args.no_kill:
        kill_chrome()

    try:
        modified = patch_preferences(prefs_path, origin)
        if modified:
            print(f"  ✔  Camera permission granted for: {origin}")
        else:
            print(f"  ✔  Camera permission was already set for: {origin} (no change needed)")
    except json.JSONDecodeError as exc:
        print(f"  ERROR: Could not parse Chrome Preferences: {exc}")
        print("  Chrome may have been running and locked the file. Try again after closing Chrome.")
        sys.exit(1)
    except Exception as exc:
        print(f"  ERROR: {exc}")
        sys.exit(1)

    # ── Step 4: Create desktop launcher ───────────────────────────────────────
    print("[4/4] Creating desktop launcher batch file...")
    launcher_path = create_launcher(chrome_exe, origin, target_url)
    print(f"  ✔  Launcher created: {launcher_path}")

    print()
    print("=" * 60)
    print("  Setup complete!")
    print()
    print("  HOW TO USE:")
    print(f"  • Double-click '{LAUNCHER_NAME}' on the Desktop, OR")
    print(f"  • Open Chrome normally — camera is now allowed for {origin}")
    print()
    print("  NOTE: The Preferences change applies immediately on next Chrome start.")
    print("  The launcher provides an extra flag as a fallback.")
    print("=" * 60)


if __name__ == "__main__":
    main()
