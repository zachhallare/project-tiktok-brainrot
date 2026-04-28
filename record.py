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
    for i, name in enumerate(WEAPON_NAMES, 1):
        print(f"    {i}. {name}")
    while True:
        choice = input(f"  Pick weapon for {label} (1-{len(WEAPON_NAMES)}): ").strip()
        if choice.isdigit() and 1 <= int(choice) <= len(WEAPON_NAMES):
            return WEAPON_NAMES[int(choice) - 1]
        print(f"    Please enter a number between 1 and {len(WEAPON_NAMES)}.")


def _load_used_indices(tracker_file):
    if os.path.exists(tracker_file):
        with open(tracker_file, 'r') as f:
            return json.load(f).get("used_combos", [])
    return []
 
 
def _save_used_indices(used, tracker_file):
    with open(tracker_file, 'w') as f:
        json.dump({"used_combos": used}, f, indent=4)


def next_random_combo(active_combos, tracker_file):
    """
    Pick a combo index that hasn't been used yet this cycle.
    When all combos are exhausted the pool resets automatically.
    Returns (f1_weapon, f2_weapon) with fighter assignment randomised.
    """
    used = _load_used_indices(tracker_file)
 
    available = [i for i in range(len(active_combos)) if i not in used]
    if not available:
        print(f"\n[INFO] All {len(active_combos)} weapon combos used. Resetting pool.")
        used = []
        available = list(range(len(active_combos)))
 
    chosen_idx = random.choice(available)
    used.append(chosen_idx)
    _save_used_indices(used, tracker_file)
 
    w1, w2 = active_combos[chosen_idx]
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

    print("\nSelect Mode:")
    print("  1. Batch Recording")
    print("  2. Test Mode")
    print("  3. Exit")
    while True:
        mode_choice = input("Select option (1-3): ").strip()
        if mode_choice in ['1', '2', '3']:
            break
        print("Please enter 1, 2, or 3.")

    if mode_choice == '3':
        print("Exiting.")
        return

    is_test_mode = mode_choice == '2'
    mode_name = "Test Mode" if is_test_mode else "Batch Recording"

    root_dir = os.path.dirname(os.path.abspath(__file__))
    main_script = os.path.join(root_dir, "src", "main.py")

    # TEST MODE
    if is_test_mode:
        print("\n[TEST MODE] Select test type:")
        print("  1. Manual Test (pick weapons)")
        print("  2. Auto Test (all relevant matchups)")
        while True:
            test_choice = input("Select option (1-2): ").strip()
            if test_choice in ['1', '2']:
                break
            print("Please enter 1 or 2.")

        mute_choice = input("\nMute sound effects for this test? (y/n): ").strip().lower()
        mute_flag = ["--mute-sounds"] if mute_choice == 'y' else []

        # --- MANUAL TEST ---
        if test_choice == '1':
            print("\n[MANUAL TEST] Pick a weapon for each fighter.")
            f1_weapon = pick_weapon("Fighter 1")
            f2_weapon = pick_weapon("Fighter 2")

            try:
                count_str = input("\nHow many rounds to test? (Default: 1): ").strip()
                count = int(count_str) if count_str else 1
                if count <= 0:
                    count = 1
            except ValueError:
                count = 1

            print(f"\n[MANUAL TEST] Fighter 1: {f1_weapon.upper()}  |  Fighter 2: {f2_weapon.upper()}")
            print(f"[INFO] Running {count} round(s). OBS recording is disabled.\n")

            for i in range(count):
                print(f"\n{'='*40}")
                print(f"[TEST] ROUND {i+1} OF {count}")
                print(f"{'='*40}")
                subprocess.run([
                    sys.executable, main_script,
                    "--test-mode",
                    "--f1-weapon", f1_weapon,
                    "--f2-weapon", f2_weapon,
                ] + mute_flag)

            print("\n" + "=" * 50)
            print("TEST MATCH(ES) COMPLETE!")
            print("=" * 50)
            return

        # --- AUTO TEST ---
        AUTO_TEST_COMBOS = [
            ('dagger', 'hammer'),
            ('dagger', 'axe'),
            ('dagger', 'sword'),
            ('dagger', 'spear'),
            ('hammer', 'axe'),
            ('hammer', 'sword'),
            ('hammer', 'spear'),
            ('sword', 'spear'),
            ('sword', 'axe'),
            ('spear', 'axe'),
        ]

        try:
            count_str = input("\nHow many rounds per matchup? (Default: 5): ").strip()
            rounds = int(count_str) if count_str else 5
            if rounds <= 0:
                rounds = 5
        except ValueError:
            rounds = 5

        total_matches = len(AUTO_TEST_COMBOS) * rounds
        print(f"\n[AUTO TEST] Running {len(AUTO_TEST_COMBOS)} matchups × {rounds} rounds = {total_matches} total rounds")
        print(f"[INFO] OBS recording is disabled.\n")

        all_results = {}  # {(w1, w2): [(winner_weapon, hp_pct), ...]}

        for combo_idx, (w1, w2) in enumerate(AUTO_TEST_COMBOS, 1):
            combo_label = f"{w1.upper()} vs {w2.upper()}"
            all_results[(w1, w2)] = []

            print(f"\n{'='*50}")
            print(f"  MATCHUP {combo_idx}/{len(AUTO_TEST_COMBOS)}: {combo_label}")
            print(f"{'='*50}")

            for r in range(1, rounds + 1):
                start_time = time.time()
                result = subprocess.run(
                    [
                        sys.executable, main_script,
                        "--test-mode",
                        "--headless",
                        "--f1-weapon", w1,
                        "--f2-weapon", w2,
                    ] + mute_flag,
                    capture_output=True,
                    text=True,
                )
                elapsed_time = time.time() - start_time

                # Parse the [RESULT] line from stdout
                winner_weapon = "???"
                hp_pct = 0
                for line in result.stdout.splitlines():
                    if line.startswith("[RESULT]"):
                        parts = line.split()
                        for p in parts:
                            if p.startswith("winner="):
                                winner_weapon = p.split("=", 1)[1]
                            elif p.startswith("hp_pct="):
                                hp_pct = int(p.split("=", 1)[1])
                        break

                all_results[(w1, w2)].append((winner_weapon, hp_pct, elapsed_time))
                print(f"    Round {r}: {winner_weapon} won with {hp_pct}% HP left (total time: {elapsed_time:.2f})")

        # Print final summary
        print("\n\n" + "=" * 60)
        print("                    AUTO TEST RESULTS")
        print("=" * 60)

        for combo_idx, (w1, w2) in enumerate(AUTO_TEST_COMBOS, 1):
            results = all_results[(w1, w2)]
            w1_wins = sum(1 for w, _, _ in results if w == w1)
            w2_wins = sum(1 for w, _, _ in results if w == w2)
            combo_label = f"{w1} vs {w2}"

            print(f"\n{combo_idx}. {combo_label}  ({w1_wins}-{w2_wins})")
            for r_idx, (winner_weapon, hp_pct, elapsed_time) in enumerate(results, 1):
                print(f"    Round {r_idx}: {winner_weapon} won with {hp_pct}% HP left (total time: {elapsed_time:.2f})")

        print("\n" + "=" * 60)
        print("AUTO TEST COMPLETE!")
        print("=" * 60)
        return

    # BATCH RECORDING MODE
    if not check_obs_connection():
        return

    print("\n[BATCH MODE] Select weapon combination pool:")
    print("  1. Purely Sword vs Sword")
    print("  2. Randomized 12 specific combos")
    while True:
        pool_choice = input("Select option (1-2): ").strip()
        if pool_choice in ['1', '2']:
            break
        print("Please enter 1 or 2.")

    if pool_choice == '1':
        active_combos = [('sword', 'sword')]
        tracker_file = "used_combos_sword.json"
    else:
        active_combos = [
            ('sword', 'sword'), ('axe', 'axe'), ('dagger', 'hammer'),
            ('dagger', 'axe'), ('dagger', 'sword'), ('dagger', 'spear'),
            ('hammer', 'axe'), ('hammer', 'sword'), ('hammer', 'spear'),
            ('sword', 'spear'), ('sword', 'axe'), ('spear', 'axe')
        ]
        tracker_file = "used_combos_12.json"

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
    print(f"[INFO] Combo pool: {len(active_combos)} unique matchups tracked in '{tracker_file}'")
    print("[INFO] OBS confirmed open. Starting batch...\n")

    for i in range(count):
        f1_weapon, f2_weapon, combo_idx = next_random_combo(active_combos, tracker_file)
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