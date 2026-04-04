import subprocess
import time
import sys
import os

def main():
    print("=" * 50)
    print(" TikTok / YT Shorts Automation Batch Recorder ")
    print("=" * 50)
    
    try:
        count = int(input("How many videos would you like to record automatically? (Max: 15) "))
        if count <= 0:
            print("Please enter a number greater than 0.")
            return
        if count > 15:
            print("[INFO] To prevent system instability, limiting to a maximum of 15 videos.")
            count = 15
    except ValueError:
        print("Invalid input. Please enter a number.")
        return
    
    print(f"\n[INFO] Starting batch sequence for {count} videos.")
    print("[INFO] Please ensure OBS Studio is open in the background.\n")
    
    print("[INFO] Configure Colors for each video:")
    print("Options: 1=Red, 2=Orange, 3=Yellow, 4=Green, 5=Blue, 6=Violet")
    queue = []
    for i in range(count):
        print(f"\n--- Video {i+1} ---")
        c1 = input("Fighter 1 Color (1-6, Enter for random): ").strip()
        c2 = input("Fighter 2 Color (1-6, Enter for random): ").strip()
        queue.append((c1, c2))
    
    # Calculate path to main.py dynamically to ensure it runs from any directory config
    root_dir = os.path.dirname(os.path.abspath(__file__))
    main_script = os.path.join(root_dir, "src", "main.py")
    
    for i in range(count):
        c1, c2 = queue[i]
        print(f"\n{'='*40}")
        print(f"🎬 RECORDING VIDEO {i+1} OF {count}")
        print(f"{'='*40}")
        
        # Run the game in auto-start mode via subprocess
        # This will pause the script here until the game exits itself
        args = [sys.executable, main_script, "--auto-start"]
        if c1:
            args.extend(["--f1", c1])
        if c2:
            args.extend(["--f2", c2])
            
        subprocess.run(args)
        
        # If it's not the final video, rest for a few seconds to let OBS write to disk
        if i < count - 1:
            print("\n[INFO] Waiting 3 seconds for OBS to save the MP4 buffer...")
            time.sleep(3)
            
    print("\n" + "=" * 50)
    print("✅ BATCH RECORDING COMPLETE! All videos saved via OBS.")
    print("=" * 50)

if __name__ == "__main__":
    main()
