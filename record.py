"""
Automated recording orchestration script for AlgoRot.

This script manages the batch recording pipeline for YouTube Shorts content. 
It automates the process of selecting fighter matchups, launching the 
combat simulation, and ensuring OBS Studio is capturing the footage. 

Features:
    - Batch Recording: Automatically cycles through unique weapon combinations.
    - Test Mode: Allows for manual or automated balance testing without recording.
    - Pool Management: Tracks used weapon combinations to ensure content variety.
"""

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


def pick_weapon(label: str) -> str:
    """Prompt the user to pick a single weapon for one fighter via CLI.

    Args:
        label: Descriptive label for the fighter (e.g., "Fighter 1").

    Returns:
        str: The selected weapon name.
    """
    print(f"\n  Weapons available for {label}:")
    for i, name in enumerate(WEAPON_NAMES, 1):
        print(f"    {i}. {name}")
    while True:
        choice = input(f"  Pick weapon for {label} (1-{len(WEAPON_NAMES)}): ").strip()
        if choice.isdigit() and 1 <= int(choice) <= len(WEAPON_NAMES):
            return WEAPON_NAMES[int(choice) - 1]
        print(f"    Please enter a number between 1 and {len(WEAPON_NAMES)}.")


def _load_used_indices(tracker_file: str) -> list:
    """Load indices of weapon combinations already recorded.

    Args:
        tracker_file: Path to the JSON tracker file.

    Returns:
        list: List of integer indices corresponding to recorded combos.
    """
    if os.path.exists(tracker_file):
        with open(tracker_file, 'r') as f:
            return json.load(f).get("used_combos", [])
    return []
 
 
def _save_used_indices(used: list, tracker_file: str):
    """Persist used weapon combination indices to disk.

    Args:
        used: List of used indices.
        tracker_file: Target path for the JSON file.
    """
    with open(tracker_file, 'w') as f:
        json.dump({"used_combos": used}, f, indent=4)


def next_random_combo(active_combos: list, tracker_file: str) -> tuple:
    """Selects a unique weapon combination that hasn't been used in the current cycle.

    This ensures content variety by exhausting all permutations in the 
    provided 'active_combos' pool before resetting.

    Args:
        active_combos: The list of available (w1, w2) tuples.
        tracker_file: Path to the persistence file for this pool.

    Returns:
        tuple: (f1_weapon, f2_weapon, combo_index)
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


def check_obs_connection() -> bool:
    """Blocking safety gate that verifies OBS Studio is open and WebSocket-enabled.

    This prevents the automation script from launching dozens of matches 
    that aren't being recorded, which would waste local resources and 
    desynchronize the tracking logs.

    Returns:
        bool: True if connection is verified, False if user chooses to skip/cancel.
    """
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
    """Main entry point for the YT Shorts automation recording pipeline."""
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
        print("\n[TEST MODE] Select execution mode:")
        print("  1. Full Match (Visual)")
        print("  2. Headless Mode (Fast)")
        print("  3. Back")
        while True:
            exec_choice = input("Select option (1-3): ").strip()
            if exec_choice in ['1', '2', '3']:
                break
            print("Please enter 1, 2, or 3.")

        if exec_choice == '3':
            return main()

        is_headless = (exec_choice == '2')
        mute_flag = []
        if not is_headless:
            mute_choice = input("\nMute sound effects for this test? (y/n): ").strip().lower()
            mute_flag = ["--mute-sounds"] if mute_choice == 'y' else []

        print("\n[TEST MODE] Select test scope:")
        print("  1. One specific combo (pick weapons)")
        print("  2. All possible combos")
        while True:
            scope_choice = input("Select option (1-2): ").strip()
            if scope_choice in ['1', '2']:
                break
            print("Please enter 1 or 2.")

        if scope_choice == '1':
            f1 = pick_weapon("Fighter 1")
            f2 = pick_weapon("Fighter 2")
            AUTO_TEST_COMBOS = [(f1, f2)]
        else:
            AUTO_TEST_COMBOS = ALL_COMBOS

        try:
            count_str = input("\nHow many rounds per matchup? (Default: 5): ").strip()
            rounds = int(count_str) if count_str else 5
            if rounds <= 0:
                rounds = 5
        except ValueError:
            rounds = 5

        test_name = "HEADLESS TEST" if is_headless else "VISUAL TEST"
        total_matches = len(AUTO_TEST_COMBOS) * rounds
        print(f"\n[{test_name}] Running {len(AUTO_TEST_COMBOS)} matchups × {rounds} rounds = {total_matches} total rounds")
        print(f"[INFO] OBS recording is disabled.")
        print(f"[INFO] Side assignment randomized each round (left/right flips 50%).\n")

        all_results = {}  # {(w1, w2): [(winner_weapon, hp_pct, elapsed), ...]}

        for combo_idx, (w1, w2) in enumerate(AUTO_TEST_COMBOS, 1):
            canonical_label = f"{w1.upper()} vs {w2.upper()}"
            all_results[(w1, w2)] = []

            print(f"\n{'='*50}")
            print(f"  MATCHUP {combo_idx}/{len(AUTO_TEST_COMBOS)}: {canonical_label}")
            print(f"{'='*50}")

            for r in range(1, rounds + 1):
                f1_weapon, f2_weapon = (w2, w1) if random.random() < 0.5 else (w1, w2)
                side_label = f"L={f1_weapon.upper()} R={f2_weapon.upper()}"

                start_time = time.time()
                cmd = [
                    sys.executable, main_script,
                    "--test-mode",
                    "--f1-weapon", f1_weapon,
                    "--f2-weapon", f2_weapon,
                ] + mute_flag
                if is_headless:
                    cmd.append("--headless")

                result = subprocess.run(
                    cmd,
                    capture_output=True,
                    text=True,
                )
                elapsed_time = time.time() - start_time

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
                print(f"    Round {r} [{side_label}]: {winner_weapon} won with {hp_pct}% HP left ({elapsed_time:.2f}s)")

        print("\n\n" + "=" * 60)
        print(f"                    {test_name} RESULTS")
        print("=" * 60)

        for combo_idx, (w1, w2) in enumerate(AUTO_TEST_COMBOS, 1):
            results = all_results[(w1, w2)]
            w1_wins = sum(1 for w, _, _ in results if w == w1)
            w2_wins = sum(1 for w, _, _ in results if w == w2)
            other_wins = rounds - w1_wins - w2_wins
            combo_label = f"{w1} vs {w2}"

            print(f"\n{combo_idx}. {combo_label}  ({w1}: {w1_wins}  {w2}: {w2_wins}{'  ???: ' + str(other_wins) if other_wins else ''})")
            for r_idx, (winner_weapon, hp_pct, elapsed_time) in enumerate(results, 1):
                print(f"    Round {r_idx}: {winner_weapon} won with {hp_pct}% HP left ({elapsed_time:.2f}s)")

        print("\n" + "=" * 60)
        print(f"{test_name} COMPLETE!")
        print("=" * 60)
        return

    # BATCH RECORDING MODE
    if not check_obs_connection():
        return

    active_combos = [
        ('sword', 'sword'), ('axe', 'axe'), ('dagger', 'hammer'),
        ('dagger', 'axe'), ('dagger', 'sword'), ('dagger', 'spear'),
        ('hammer', 'axe'), ('hammer', 'sword'), ('hammer', 'spear'),
        ('sword', 'spear'), ('sword', 'axe'), ('spear', 'axe')
    ]
    tracker_file = "used_combos_12.json"

    try:
        count = int(input("How many matches? (Max: 100): ").strip())
        if count <= 0:
            print("Please enter a number greater than 0.")
            return
        if count > 100:
            print("[INFO] Limiting to 100 matches.")
            count = 100
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

    