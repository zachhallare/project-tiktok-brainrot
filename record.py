import subprocess
import time
import sys
import os

def main():
    print("=" * 50)
    print(" TikTok / YT Shorts Automation Recorder ")
    print("=" * 50)
    
    test_mode_input = input("Run in test mode? (y/n) ").strip().lower()
    is_test_mode = test_mode_input == 'y'
    mode_name = "Test Mode" if is_test_mode else "Batch Recording"
    
    try:
        count = int(input(f"How many matches? (Max: 30) "))
        if count <= 0:
            print("Please enter a number greater than 0.")
            return
        if count > 30:
            print("[INFO] To prevent system instability, limiting to a maximum of 30 matches.")
            count = 30
    except ValueError:
        print("Invalid input. Please enter a number.")
        return
    
    print(f"\n[INFO] Starting {mode_name} sequence for {count} matches.")
    print("[INFO] Fighter colors will be randomized for each match.")
    
    if is_test_mode:
        print("[INFO] OBS recording is disabled.\n")
    else:
        print("[INFO] Please ensure OBS Studio is open in the background.\n")
    
    # Calculate path to main.py dynamically to ensure it runs from any directory config
    root_dir = os.path.dirname(os.path.abspath(__file__))
    main_script = os.path.join(root_dir, "src", "main.py")
    
    for i in range(count):
        print(f"\n{'='*40}")
        print(f"[{mode_name.upper()}] MATCH {i+1} OF {count}")
        print(f"{'='*40}")
        
        if is_test_mode:
            # Run the game in test mode via subprocess
            # Colors are randomized automatically inside main.py
            subprocess.run([sys.executable, main_script, "--test-mode"])
        else:
            # Run the game in auto-start mode via subprocess
            # Colors are randomized automatically inside main.py
            subprocess.run([sys.executable, main_script, "--auto-start"])
            
            # If it's not the final video, rest for a few seconds to let OBS write to disk
            if i < count - 1:
                print("\n[INFO] Waiting 3 seconds for OBS to save the MP4 buffer...")
                time.sleep(3)
                
    print("\n" + "=" * 50)
    if is_test_mode:
        print("TEST BATCH COMPLETE! All test matches finished.")
    else:
        print("BATCH RECORDING COMPLETE! All videos saved via OBS.")
    print("=" * 50)

if __name__ == "__main__":
    main()
