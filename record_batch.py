import subprocess
import time
import sys
import os

def main():
    print("=" * 50)
    print(" TikTok / YT Shorts Automation Batch Recorder ")
    print("=" * 50)
    
    try:
        count = int(input("How many videos would you like to record automatically? (Max: 30) "))
        if count <= 0:
            print("Please enter a number greater than 0.")
            return
        if count > 30:
            print("[INFO] To prevent system instability, limiting to a maximum of 30 videos.")
            count = 30
    except ValueError:
        print("Invalid input. Please enter a number.")
        return
    
    print(f"\n[INFO] Starting batch sequence for {count} videos.")
    print("[INFO] Fighter colors will be randomized for each video.")
    print("[INFO] Please ensure OBS Studio is open in the background.\n")
    
    # Calculate path to main.py dynamically to ensure it runs from any directory config
    root_dir = os.path.dirname(os.path.abspath(__file__))
    main_script = os.path.join(root_dir, "src", "main.py")
    
    for i in range(count):
        print(f"\n{'='*40}")
        print(f"🎬 RECORDING VIDEO {i+1} OF {count}")
        print(f"{'='*40}")
        
        # Run the game in auto-start mode via subprocess
        # Colors are randomized automatically inside main.py
        subprocess.run([sys.executable, main_script, "--auto-start"])
        
        # If it's not the final video, rest for a few seconds to let OBS write to disk
        if i < count - 1:
            print("\n[INFO] Waiting 3 seconds for OBS to save the MP4 buffer...")
            time.sleep(3)
            
    print("\n" + "=" * 50)
    print("✅ BATCH RECORDING COMPLETE! All videos saved via OBS.")
    print("=" * 50)

if __name__ == "__main__":
    main()
