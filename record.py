import subprocess
import time
import sys
import os
import json
import random
import itertools

try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass


WEAPON_NAMES = ['sword', 'dagger', 'spear', 'axe', 'hammer']
ALL_COMBOS = list(itertools.combinations_with_replacement(WEAPON_NAMES, 2))
COMBO_TRACKER_FILE = "used_weapon_combos.json"


def pick_weapon(label):
    """Prompt the user to pick a single weapon for one fighter."""
    print(f"\n  Weapons available for {label}:")
    print(f"    0. random")
    for i, name in enumerate(WEAPON_NAMES, 1):
        print(f"    {i}. {name}")
    while True:
        choice = input(f"  Pick weapon for {label} (1-{len(WEAPON_NAMES)}): ").strip()
        if choice == '0':
            return random.choice(WEAPON_NAMES)
        if choice.isdigit() and 1 <= int(choice) <= len(WEAPON_NAMES):
            return WEAPON_NAMES[int(choice) - 1]
        print(f"    Please enter a number between 1 and {len(WEAPON_NAMES)}.")


def _load_used_indices():
    if os.path.exists(COMBO_TRACKER_FILE):
        with open(COMBO_TRACKER_FILE, 'r') as f:
            return json.load(f).get("used_combos", [])
    return []
 
 
def _save_used_indices(used):
    with open(COMBO_TRACKER_FILE, 'w') as f:
        json.dump({"used_combos": used}, f, indent=4)


def next_random_combo():
    """
    Pick a combo index that hasn't been used yet this cycle.
    When all 15 are exhausted the pool resets automatically.
    Returns (f1_weapon, f2_weapon) with fighter assignment randomised.
    """
    used = _load_used_indices()
 
    available = [i for i in range(len(ALL_COMBOS)) if i not in used]
    if not available:
        print(f"\n[INFO] All {len(ALL_COMBOS)} weapon combos used. Resetting pool.")
        used = []
        available = list(range(len(ALL_COMBOS)))
 
    chosen_idx = random.choice(available)
    used.append(chosen_idx)
    _save_used_indices(used)
 
    w1, w2 = ALL_COMBOS[chosen_idx]
    # Randomly flip so fighter assignment isn't always the same within a pair
    if random.random() < 0.5:
        w1, w2 = w2, w1
    return w1, w2, chosen_idx



def check_obs_connection():
    """Block until OBS is open and reachable, or user cancels."""
    print("\n[INFO] Checking OBS connection before proceeding...")
    while True:
        try:
            import obsws_python as obsws
            import io, contextlib

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
    print("          YT Shorts Automation Recorder  ")
    print("=" * 50)

    test_mode_input = input("Run in test mode? (y/n): ").strip().lower()
    is_test_mode = test_mode_input == 'y'
    mode_name = "Test Mode" if is_test_mode else "Batch Recording"

    root_dir = os.path.dirname(os.path.abspath(__file__))
    main_script = os.path.join(root_dir, "src", "main.py")

    # TEST MODE
    if is_test_mode:
        print("\n[TEST MODE] One match only — pick a weapon for each fighter.")
        f1_weapon = pick_weapon("Fighter 1")
        f2_weapon = pick_weapon("Fighter 2")
 
        print(f"\n[TEST MODE] Fighter 1: {f1_weapon.upper()}  |  Fighter 2: {f2_weapon.upper()}")
        print("[INFO] OBS recording is disabled.\n")
 
        subprocess.run([
            sys.executable, main_script,
            "--test-mode",
            "--f1-weapon", f1_weapon,
            "--f2-weapon", f2_weapon,
        ])
 
        print("\n" + "=" * 50)
        print("TEST MATCH COMPLETE!")
        print("=" * 50)
        return

    # BATCH RECORDING MODE
    if not check_obs_connection():
        return

    try:
        count = int(input("How many matches? (Max: 30): ").strip())
        if count <= 0:
            print("Please enter a number greater than 0.")
            return
        if count > 30:
            print("[INFO] Limiting to 30 matches.")
            count = 30
    except ValueError:
        print("Invalid input. Please enter a number.")
        return

    print(f"\n[INFO] Starting Batch Recording — {count} match(es) — weapons randomized per match")
    print(f"[INFO] Combo pool: {len(ALL_COMBOS)} unique matchups tracked in '{COMBO_TRACKER_FILE}'")
    print("[INFO] OBS confirmed open. Starting batch...\n")

    for i in range(count):
        f1_weapon, f2_weapon, combo_idx = next_random_combo()
        combo_label = f"{f1_weapon.upper()} vs {f2_weapon.upper()}"

        print(f"\n{'='*40}")
        print(f"[BATCH] MATCH {i+1} OF {count}  |  {combo_label}  (combo #{combo_idx})")
        print(f"{'='*40}")

        subprocess.run([
            sys.executable, main_script,
            "--auto-start",
            "--f1-weapon", f1_weapon,
            "--f2-weapon", f2_weapon
        ])

        if i < count - 1:
            print("\n[INFO] Waiting 3 seconds for OBS to save...")
            time.sleep(3)

    print("\n" + "=" * 50)
    print("BATCH RECORDING COMPLETE! All videos saved via OBS.")
    print("=" * 50)


if __name__ == "__main__":
    main()