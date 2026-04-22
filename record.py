import subprocess
import time
import sys
import os


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


def main():
    print("=" * 50)
    print("  TikTok / YT Shorts Automation Recorder  ")
    print("=" * 50)

    test_mode_input = input("Run in test mode? (y/n): ").strip().lower()
    is_test_mode = test_mode_input == 'y'
    mode_name = "Test Mode" if is_test_mode else "Batch Recording"

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
        print("[INFO] Please ensure OBS Studio is open in the background.\n")

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