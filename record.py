import subprocess
import time
import sys
import os

try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass


WEAPON_NAMES = ['sword', 'dagger', 'spear', 'axe', 'hammer']


def pick_weapon():
    print("\nAvailable weapons:")
    for i, name in enumerate(WEAPON_NAMES, 1):
        print(f"  {i}. {name}")
    while True:
        choice = input("Pick a weapon for both fighters (1-5): ").strip()
        if choice.isdigit() and 1 <= int(choice) <= len(WEAPON_NAMES):
            return WEAPON_NAMES[int(choice) - 1]
        print(f"  Please enter a number between 1 and {len(WEAPON_NAMES)}.")


def check_obs_connection():
    """Block until OBS is open and reachable, or user cancels."""
    print("\n[INFO] Checking OBS connection before proceeding...")
    while True:
        try:
            import obsws_python as obsws
            import io
            import contextlib

            port = int(os.environ.get("OBS_PORT", 4455))
            password = os.environ.get("OBS_PASSWORD", "")
            with contextlib.redirect_stderr(io.StringIO()):
                cl = obsws.ReqClient(host="localhost", port=port, password=password, timeout=3)
                cl.get_version()
                cl.disconnect()
            print("[OK] OBS is open and connected. Proceeding...\n")
            return True
        except ConnectionRefusedError:
            print(f"[WAITING] OBS is not open or WebSocket is not enabled (port {os.environ.get('OBS_PORT', 4455)}).")
            retry = input("Open OBS and press ENTER to retry, or type 'skip' to cancel: ").strip().lower()
            if retry == 'skip':
                print("[CANCELLED] Exiting.")
                return False
        except Exception as e:
            print(f"[WAITING] Could not connect to OBS: {type(e).__name__}: {e}")
            retry = input("Open OBS and press ENTER to retry, or type 'skip' to cancel: ").strip().lower()
            if retry == 'skip':
                print("[CANCELLED] Exiting.")
                return False


def main():
    print("=" * 50)
    print("  TikTok / YT Shorts Automation Recorder  ")
    print("=" * 50)

    test_mode_input = input("Run in test mode? (y/n): ").strip().lower()
    is_test_mode = test_mode_input == 'y'
    mode_name = "Test Mode" if is_test_mode else "Batch Recording"

    # Check OBS connection before anything else if recording
    if not is_test_mode:
        if not check_obs_connection():
            return

    weapon = pick_weapon()
    print(f"[INFO] Weapon selected: {weapon.upper()}")

    try:
        count = int(input(f"How many matches? (Max: 30): ").strip())
        if count <= 0:
            print("Please enter a number greater than 0.")
            return
        if count > 30:
            print("[INFO] Limiting to 30 matches.")
            count = 30
    except ValueError:
        print("Invalid input. Please enter a number.")
        return

    print(f"\n[INFO] Starting {mode_name} — {count} match(es) — weapon: {weapon.upper()}")
    if is_test_mode:
        print("[INFO] OBS recording is disabled.\n")
    else:
        print("[INFO] OBS confirmed open. Starting batch...\n")

    root_dir    = os.path.dirname(os.path.abspath(__file__))
    main_script = os.path.join(root_dir, "src", "main.py")

    for i in range(count):
        print(f"\n{'='*40}")
        print(f"[{mode_name.upper()}] MATCH {i+1} OF {count}  |  WEAPON: {weapon.upper()}")
        print(f"{'='*40}")

        flags = ["--weapon", weapon]

        if is_test_mode:
            subprocess.run([sys.executable, main_script, "--test-mode", *flags])
        else:
            subprocess.run([sys.executable, main_script, "--auto-start", *flags])
            if i < count - 1:
                print("\n[INFO] Waiting 3 seconds for OBS to save...")
                time.sleep(3)

    print("\n" + "=" * 50)
    if is_test_mode:
        print("TEST BATCH COMPLETE!")
    else:
        print("BATCH RECORDING COMPLETE! All videos saved via OBS.")
    print("=" * 50)


if __name__ == "__main__":
    main()