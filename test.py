import subprocess
import sys
import os

def main():
    print("=" * 50)
    print(" TikTok / YT Shorts Automation Test Mode ")
    print("=" * 50)
    
    try:
        count = int(input("How many matches would you like to run in test mode? (Max: 30) "))
        if count <= 0:
            print("Please enter a number greater than 0.")
            return
        if count > 30:
            print("[INFO] To prevent system instability, limiting to a maximum of 30 test matches.")
            count = 30
    except ValueError:
        print("Invalid input. Please enter a number.")
        return
    
    print(f"\n[INFO] Starting test sequence for {count} matches.")
    print("[INFO] Fighter colors will be randomized for each match.")
    print("[INFO] OBS recording is disabled.\n")
    
    # Calculate path to main.py dynamically to ensure it runs from any directory config
    root_dir = os.path.dirname(os.path.abspath(__file__))
    main_script = os.path.join(root_dir, "src", "main.py")
    
    for i in range(count):
        print(f"\n{'='*40}")
        print(f"🎬 TEST MATCH {i+1} OF {count}")
        print(f"{'='*40}")
        
        # Run the game in test mode via subprocess
        # Colors are randomized automatically inside main.py
        subprocess.run([sys.executable, main_script, "--test-mode"])
            
    print("\n" + "=" * 50)
    print("✅ TEST BATCH COMPLETE! All test matches finished.")
    print("=" * 50)

if __name__ == "__main__":
    main()
