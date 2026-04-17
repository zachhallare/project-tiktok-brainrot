import os
import time
import glob

try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass

try:
    import obsws_python as obs
except ImportError:
    obs = None


class OBSManager:
    """Manages connection to OBS Studio via WebSocket, including start/stop recording routines."""
    
    def __init__(self, f1_name="Blue", f2_name="Red"):
        self.f1_name = f1_name
        self.f2_name = f2_name
        self.obs_client = None
        self.is_recording = False
        
    def connect(self):
        """Initialize connection to OBS WebSocket server."""
        if obs is None:
            print("[OBS] obsws-python library not found. Auto-recording disabled.")
            return
            
        try:
            port = int(os.getenv("OBS_PORT", "4455"))
            password = os.getenv("OBS_PASSWORD", "")
            
            if not password:
                print("[OBS] No OBS_PASSWORD found in .env. Auto-recording disabled.")
                return
                
            self.obs_client = obs.ReqClient(host='localhost', port=port, password=password)
            print("[OBS] Successfully hooked into OBS Studio!")
        except Exception as e:
            print(f"[OBS] Failed to connect: {e} (Is OBS open?)")
            self.obs_client = None

    def start_recording(self):
        """Start OBS recording if connected."""
        if self.obs_client and not self.is_recording:
            try:
                self.obs_client.start_record()
                self.is_recording = True
                print("[OBS] 🎥 Camera Rolling! Recording Started.")
            except Exception as e:
                print(f"[OBS] Start recording failed: {e}")

    def stop_recording(self, viral_title_idea=None):
        """Stop OBS recording and rename the file using the viral title if provided."""
        if self.obs_client and self.is_recording:
            try:
                # Retrieve Recording Path
                record_dir_resp = self.obs_client.get_record_directory()
                record_dir = record_dir_resp.record_directory
                
                # Execute Stop
                self.obs_client.stop_record()
                self.is_recording = False
                
                # The Renaming Sequence
                files = glob.glob(os.path.join(record_dir, "*.mp4"))
                if files:
                    latest_file = max(files, key=os.path.getctime)
                    name1 = self.f1_name.capitalize()
                    name2 = self.f2_name.capitalize()
                    
                    if viral_title_idea:
                        # Sanitize string for valid Windows filename format
                        safe_title = "".join(c for c in viral_title_idea if c not in r'\/:*?"<>|').strip()
                        new_filename = f"{safe_title}.mp4"
                        
                        # Handle Conflicts
                        new_path = os.path.join(record_dir, new_filename)
                        if os.path.exists(new_path):
                            new_filename = f"{safe_title}_{int(time.time())}.mp4"
                            new_path = os.path.join(record_dir, new_filename)
                    else:
                        new_filename = f"Who Wins {name1} vs {name2}.mp4"
                        new_path = os.path.join(record_dir, new_filename)
                        
                        # Handle Conflicts
                        if os.path.exists(new_path):
                            new_filename = f"Who Wins {name1} vs {name2}_{int(time.time())}.mp4"
                            new_path = os.path.join(record_dir, new_filename)
                        
                    # Retry loop to wait for OBS to release the file lock
                    max_retries = 20
                    retry_delay = 0.5
                    success = False
                    for i in range(max_retries):
                        try:
                            os.rename(latest_file, new_path)
                            print(f"[OBS] File renamed to: {new_filename}")
                            success = True
                            break
                        except OSError:
                            time.sleep(retry_delay)
                            
                    if not success:
                        print(f"[OBS] Failed to rename. File might still be locked: {latest_file}")
                else:
                    print("[OBS] ⏹️ CUT! Recording Saved.")
            except Exception as e:
                print(f"[OBS] Stop recording failed: {e}")
