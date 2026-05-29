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
ALL_COMBOS = list(itertools.combinations(WEAPON_NAMES, 2))
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


def _pick_next_combo(active_combos: list, tracker_file: str) -> tuple:
    """Pick the next combo from the pool WITHOUT committing it to the tracker.

    This is step 1 of a two-phase commit. The combo index is only saved to
    disk once the resulting video is confirmed within the duration limit.

    Args:
        active_combos: The list of available (w1, w2) tuples.
        tracker_file: Path to the JSON tracker file.

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
    w1, w2 = active_combos[chosen_idx]
    if random.random() < 0.5:
        w1, w2 = w2, w1
    return w1, w2, chosen_idx


def _commit_combo(chosen_idx: int, tracker_file: str):
    """Persist a combo index to the used-combos tracker.

    This is step 2 of a two-phase commit, called only after the resulting
    video is confirmed to be within the duration limit.

    Args:
        chosen_idx: The index of the combo in the active_combos list.
        tracker_file: Path to the JSON tracker file.
    """
    used = _load_used_indices(tracker_file)
    if chosen_idx not in used:
        used.append(chosen_idx)
        _save_used_indices(used, tracker_file)


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
                winner_side = "???"
                hp_pct = 0
                for line in result.stdout.splitlines():
                    if line.startswith("[RESULT]"):
                        parts = line.split()
                        for p in parts:
                            if p.startswith("winner="):
                                winner_weapon = p.split("=", 1)[1]
                            elif p.startswith("side="):
                                winner_side = p.split("=", 1)[1]
                            elif p.startswith("hp_pct="):
                                hp_pct = int(p.split("=", 1)[1])
                        break

                # No [RESULT] tag means both fighters died simultaneously — treat as DRAW.
                # winner_weapon stays "???" only in this case; relabel it so the summary
                # is readable and the existing other_wins counter handles it correctly.
                if winner_weapon == "???":
                    winner_weapon = "DRAW"
                    winner_side = "DRAW"

                all_results[(w1, w2)].append((winner_weapon, winner_side, hp_pct, elapsed_time))
                if winner_weapon == "DRAW":
                    print(f"    Round {r} [{side_label}]: DRAW (simultaneous death, {elapsed_time:.2f}s)")
                else:
                    print(f"    Round {r} [{side_label}]: {winner_side}-{winner_weapon} won with {hp_pct}% HP left ({elapsed_time:.2f}s)")

        print("\n\n" + "=" * 60)
        print(f"                    {test_name} RESULTS")
        print("=" * 60)

        for combo_idx, (w1, w2) in enumerate(AUTO_TEST_COMBOS, 1):
            results = all_results[(w1, w2)]
            combo_label = f"{w1} vs {w2}"
            
            if w1 == w2:
                left_wins = sum(1 for _, side, _, _ in results if side == "L")
                right_wins = sum(1 for _, side, _, _ in results if side == "R")
                other_wins = rounds - left_wins - right_wins
                print(f"\n{combo_idx}. {combo_label}  (Left: {left_wins}  Right: {right_wins}{'  ???: ' + str(other_wins) if other_wins else ''})")
            else:
                w1_wins = sum(1 for w, _, _, _ in results if w == w1)
                w2_wins = sum(1 for w, _, _, _ in results if w == w2)
                other_wins = rounds - w1_wins - w2_wins
                print(f"\n{combo_idx}. {combo_label}  ({w1}: {w1_wins}  {w2}: {w2_wins}{'  ???: ' + str(other_wins) if other_wins else ''})")
                
            for r_idx, (winner_weapon, winner_side, hp_pct, elapsed_time) in enumerate(results, 1):
                print(f"    Round {r_idx}: {winner_side}-{winner_weapon} won with {hp_pct}% HP left ({elapsed_time:.2f}s)")

        print("\n" + "=" * 60)
        print(f"{test_name} COMPLETE!")
        print("=" * 60)
        return

    # BATCH RECORDING MODE
    if not check_obs_connection():
        return

    active_combos = [
        ('dagger', 'hammer'),
        ('dagger', 'axe'), ('dagger', 'sword'), ('dagger', 'spear'),
        ('hammer', 'axe'), ('hammer', 'sword'), ('hammer', 'spear'),
        ('sword', 'spear'), ('sword', 'axe'), ('spear', 'axe')
    ]
    tracker_file = "used_combos_12.json"

    MAX_VIDEO_DURATION = 45.0   # seconds — videos over this are discarded and retried
    MAX_RETRIES = 3             # attempts per combo before moving on

    try:
        count = int(input("How many matches? (Max: 40): ").strip())
        if count <= 0:
            print("Please enter a number greater than 0.")
            return
        if count > 40:
            print("[INFO] Limiting to 40 matches to prevent OBS lag.")
            count = 40
    except ValueError:
        print("Invalid input. Please enter a number.")
        return

    try:
        cooldown_str = input("Cooldown between videos in seconds? (Default: 5): ").strip()
        cooldown = int(cooldown_str) if cooldown_str else 5
        if cooldown < 0:
            cooldown = 0
    except ValueError:
        cooldown = 5

    print(f"\n[INFO] Starting Batch Recording — {count} match(es) — weapons randomized per match")
    print(f"[INFO] Combo pool: {len(active_combos)} unique matchups tracked in '{tracker_file}'")
    print(f"[INFO] Duration gate: ≤{MAX_VIDEO_DURATION}s | Max retries per combo: {MAX_RETRIES}")
    print(f"[INFO] Inter-video cooldown: {cooldown}s")
    print("[INFO] OBS confirmed open. Starting batch...\n")

    successful = 0
    while successful < count:
        f1_weapon, f2_weapon, combo_idx = _pick_next_combo(active_combos, tracker_file)
        combo_label = f"{f1_weapon.upper()} vs {f2_weapon.upper()}"

        print(f"\n{'='*40}")
        print(f"[BATCH] VIDEO {successful + 1} OF {count}  |  {combo_label}  (combo #{combo_idx})")
        print(f"{'='*40}")

        video_accepted = False

        for attempt in range(1, MAX_RETRIES + 1):
            if attempt > 1:
                print(f"\n[RETRY] Attempt {attempt}/{MAX_RETRIES} — retrying same combo ({combo_label})...")

            # Stream subprocess output in real-time AND capture it for parsing
            cmd = [
                sys.executable, main_script,
                "--auto-start",
                "--f1-weapon", f1_weapon,
                "--f2-weapon", f2_weapon
            ]
            proc = subprocess.Popen(
                cmd,
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                text=True
            )
            output_lines = []
            for line in proc.stdout:
                print(line, end='', flush=True)
                output_lines.append(line)
            proc.wait()

            # Parse [VIDEO_DURATION] and [VIDEO_PATH] from output
            duration = None
            video_path = None
            for line in output_lines:
                if line.startswith("[VIDEO_DURATION]"):
                    try:
                        duration = float(line.split()[1])
                    except (IndexError, ValueError):
                        pass
                elif line.startswith("[VIDEO_PATH]"):
                    video_path = line[len("[VIDEO_PATH]"):].strip()

            print("\n[INFO] Waiting 3 seconds for OBS to finalize...")
            time.sleep(3)

            # Duration unknown — accept by default to avoid getting stuck
            if duration is None:
                print("[WARN] Could not read video duration. Accepting by default.")
                _commit_combo(combo_idx, tracker_file)
                successful += 1
                video_accepted = True
                break

            print(f"[INFO] Video duration: {duration:.1f}s")

            if duration <= MAX_VIDEO_DURATION:
                print(f"[OK] ✅ Accepted ({duration:.1f}s). [{successful + 1}/{count} complete]")
                _commit_combo(combo_idx, tracker_file)
                successful += 1
                video_accepted = True
                if cooldown > 0 and successful < count:
                    print(f"[INFO] Cooldown: waiting {cooldown}s before next video...")
                    time.sleep(cooldown)
                break
            else:
                print(f"[DISCARD] ❌ Too long ({duration:.1f}s > {MAX_VIDEO_DURATION}s). Discarding...")
                if video_path and os.path.exists(video_path):
                    try:
                        os.remove(video_path)
                        print(f"[DISCARD] Deleted: {os.path.basename(video_path)}")
                    except OSError as e:
                        print(f"[WARN] Could not delete file: {e}")
                else:
                    print("[WARN] File path not found — may need manual cleanup.")

                if attempt < MAX_RETRIES:
                    print(f"[INFO] Retrying in 2 seconds...")
                    time.sleep(2)

        if not video_accepted:
            print(f"\n[SKIP] ⚠️  {combo_label} failed all {MAX_RETRIES} attempts. Moving to next combo.")
            print(f"[INFO] Progress: {successful}/{count} videos accepted.")

    print("\n" + "=" * 50)
    print("BATCH RECORDING COMPLETE! All videos saved via OBS.")
    print(f"Total accepted: {successful}/{count}")
    print("=" * 50)


if __name__ == "__main__":
    main()