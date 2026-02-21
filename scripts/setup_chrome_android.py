"""
setup_chrome_android.py
=======================
Automates Google Chrome setup on an Android device to allow camera access
over HTTP for the HRMO e-Logbook web project.

How it works:
  Uses ADB (Android Debug Bridge) over USB or Wi-Fi to:
    1. Verify the device is connected and ADB is available.
    2. Write Chrome's command-line flags file with
       --unsafely-treat-insecure-origin-as-secure pointed at your HTTP origin.
    3. Grant the CAMERA permission to Chrome at the OS level.
    4. Force-stop Chrome so the new flags take effect on next launch.
    5. (Optional) Open Chrome directly to the logbook URL.

Prerequisites on the ANDROID DEVICE:
  • Developer Options must be enabled
      Settings → About Phone → tap "Build Number" 7 times
  • USB Debugging must be ON
      Settings → Developer Options → USB Debugging ✓
  • "Enable command line on non-rooted devices" in chrome://flags
      OR the device is rooted (script works without root via ADB shell)

Prerequisites on this PC:
  • ADB installed and in PATH
      Download: https://developer.android.com/studio/releases/platform-tools
  • USB cable (or ADB over Wi-Fi — see --connect option)

Usage:
  # Basic (USB, default URL)
  python setup_chrome_android.py

  # Custom server URL
  python setup_chrome_android.py --url http://192.168.1.100:5000

  # Connect via Wi-Fi (pair first with: adb pair <ip>:<port>)
  python setup_chrome_android.py --connect 192.168.1.50:5555

  # Also open Chrome to the app after setup
  python setup_chrome_android.py --open
"""

import argparse
import subprocess
import sys
import time

# ── Defaults ──────────────────────────────────────────────────────────────────
DEFAULT_URL = "http://10.0.0.1:5000"
CHROME_PKG  = "com.android.chrome"

# Path Chrome reads flags from on Android (no root needed via ADB)
CHROME_FLAGS_FILE = "/data/local/tmp/chrome-command-line"

# ── Helpers ───────────────────────────────────────────────────────────────────

def run_adb(*args: str, capture: bool = True, check: bool = False) -> subprocess.CompletedProcess:
    cmd = ["adb", *args]
    return subprocess.run(
        cmd,
        capture_output=capture,
        text=True,
        check=check,
    )


def adb_shell(command: str, capture: bool = True) -> subprocess.CompletedProcess:
    return run_adb("shell", command, capture=capture)


def check_adb_installed() -> bool:
    try:
        result = run_adb("version")
        return result.returncode == 0
    except FileNotFoundError:
        return False


def get_connected_devices() -> list[str]:
    result = run_adb("devices")
    lines = result.stdout.strip().splitlines()
    devices = []
    for line in lines[1:]:  # skip "List of devices attached"
        parts = line.split()
        if len(parts) >= 2 and parts[1] == "device":
            devices.append(parts[0])
    return devices


def url_to_origin(url: str) -> str:
    from urllib.parse import urlparse
    p = urlparse(url)
    origin = f"{p.scheme}://{p.hostname}"
    if p.port:
        origin += f":{p.port}"
    return origin


def write_chrome_flags(origin: str):
    """Push the Chrome command-line flags file to the device."""
    flags_content = f"_ --unsafely-treat-insecure-origin-as-secure={origin} --disable-features=IsolateOrigins"
    # Use adb shell to write; escape single quotes in content just in case
    cmd = f"echo '{flags_content}' > {CHROME_FLAGS_FILE}"
    result = adb_shell(cmd)
    if result.returncode != 0:
        raise RuntimeError(f"Failed to write flags file: {result.stderr.strip()}")

    # Make the file world-readable (Chrome requirement)
    chmod = adb_shell(f"chmod 755 {CHROME_FLAGS_FILE}")
    if chmod.returncode != 0:
        print("  Warning: chmod on flags file returned non-zero (may still work).")


def verify_chrome_flags():
    """Read back the flags file to confirm it was written correctly."""
    result = adb_shell(f"cat {CHROME_FLAGS_FILE}")
    return result.stdout.strip() if result.returncode == 0 else None


def grant_camera_permission():
    """Grant the CAMERA permission to Chrome at the Android OS level."""
    result = run_adb("shell", "pm", "grant", CHROME_PKG, "android.permission.CAMERA")
    return result.returncode == 0


def force_stop_chrome():
    result = run_adb("shell", "am", "force-stop", CHROME_PKG)
    return result.returncode == 0


def open_chrome(url: str):
    """Launch Chrome on the device and navigate to the given URL."""
    result = run_adb(
        "shell", "am", "start",
        "-a", "android.intent.action.VIEW",
        "-d", url,
        CHROME_PKG,
    )
    return result.returncode == 0


# ── Main ──────────────────────────────────────────────────────────────────────

def main():
    parser = argparse.ArgumentParser(
        description="Configure Chrome on Android for HTTP camera access (HRMO e-Logbook)."
    )
    parser.add_argument(
        "--url",
        default=DEFAULT_URL,
        help=f"Full URL of the web app (default: {DEFAULT_URL})",
    )
    parser.add_argument(
        "--connect",
        metavar="IP:PORT",
        help="Connect to device over Wi-Fi before setup (e.g. 192.168.1.50:5555)",
    )
    parser.add_argument(
        "--open",
        action="store_true",
        help="Open Chrome to the app URL after setup.",
    )
    args = parser.parse_args()

    target_url = args.url.rstrip("/")
    origin = url_to_origin(target_url)

    print("=" * 60)
    print("  HRMO e-Logbook – Android Chrome Camera Setup")
    print("=" * 60)
    print(f"  Target URL : {target_url}")
    print(f"  Origin     : {origin}")
    print()

    # ── Step 1: Check ADB ─────────────────────────────────────────────────────
    print("[1/5] Checking ADB installation...")
    if not check_adb_installed():
        print("  ERROR: 'adb' not found in PATH.")
        print("  Download Android Platform Tools:")
        print("  https://developer.android.com/studio/releases/platform-tools")
        sys.exit(1)
    print("  ✔  ADB found.")

    # ── Step 2: Connect (Wi-Fi) ───────────────────────────────────────────────
    if args.connect:
        print(f"[2/5] Connecting to device at {args.connect} via Wi-Fi...")
        result = run_adb("connect", args.connect)
        if "connected" not in result.stdout.lower():
            print(f"  ERROR: Could not connect: {result.stdout.strip()}")
            sys.exit(1)
        print(f"  ✔  {result.stdout.strip()}")
        time.sleep(1)
    else:
        print("[2/5] Using USB connection (skipping Wi-Fi connect).")

    # ── Step 3: Verify device ─────────────────────────────────────────────────
    print("[3/5] Checking for connected Android device...")
    devices = get_connected_devices()
    if not devices:
        print("  ERROR: No authorised device found.")
        print()
        print("  Checklist:")
        print("  • Connect the phone via USB cable.")
        print("  • Enable Developer Options (tap Build Number 7×).")
        print("  • Enable USB Debugging in Developer Options.")
        print("  • On the phone, tap 'Allow' when the authorization dialog appears.")
        sys.exit(1)

    if len(devices) > 1:
        print(f"  Multiple devices found: {devices}")
        print("  Using first: {devices[0]}")
    print(f"  ✔  Device: {devices[0]}")

    # ── Step 4: Write flags + grant permission ────────────────────────────────
    print("[4/5] Configuring Chrome on device...")

    print("  Writing Chrome command-line flags file...")
    try:
        write_chrome_flags(origin)
    except RuntimeError as exc:
        print(f"  ERROR: {exc}")
        sys.exit(1)

    verified = verify_chrome_flags()
    if verified:
        print(f"  ✔  Flags file written: {verified}")
    else:
        print("  Warning: Could not verify flags file content.")

    print("  Granting OS-level camera permission to Chrome...")
    if grant_camera_permission():
        print("  ✔  Camera permission granted.")
    else:
        print("  Warning: Could not grant camera permission via pm.")
        print("          You may need to grant it manually in Android Settings.")

    print("  Force-stopping Chrome to apply new flags...")
    force_stop_chrome()
    print("  ✔  Chrome stopped (will re-read flags on next launch).")

    # ── Step 5: Optional launch ───────────────────────────────────────────────
    if args.open:
        print(f"[5/5] Opening Chrome → {target_url}")
        time.sleep(0.5)
        if open_chrome(target_url):
            print("  ✔  Chrome launched.")
        else:
            print("  Warning: Could not launch Chrome via ADB. Open it manually.")
    else:
        print("[5/5] Skipping auto-open (pass --open to launch Chrome automatically).")

    print()
    print("=" * 60)
    print("  Setup complete!")
    print()
    print("  NEXT STEPS on the Android device:")
    print(f"  1. Open Chrome and go to: {target_url}")
    print("  2. If prompted for camera permission, tap 'Allow'.")
    print()
    print("  IMPORTANT – one-time Chrome flag required:")
    print("  • In Chrome, go to: chrome://flags")
    print("  • Search: 'enable-command-line-on-non-rooted-devices'")
    print("  • Set to 'Enabled' and tap 'Relaunch'")
    print("  • This makes Chrome read the flags file on non-rooted devices.")
    print("=" * 60)


if __name__ == "__main__":
    main()
