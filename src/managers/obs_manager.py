"""
OBS Studio automation manager for AlgoRot.

This module provides a high-level interface for controlling OBS Studio via 
the WebSocket protocol (obsws-python). It handles the lifecycle of match 
recordings, from initial connection to post-match file renaming for 
viral metadata synchronization.
"""

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
    """Manages connection to OBS Studio via WebSocket.

    This class orchestrates the recording pipeline, ensuring that every 
    simulated match is captured as a high-quality video asset. It includes 
    automatic renaming logic to map internal match outcomes to viral-ready 
    filenames.

    Attributes:
        f1_name (str): Name of the first fighter.
        f2_name (str): Name of the second fighter.
        obs_client (obsws_python.ReqClient): The active WebSocket client.
        is_recording (bool): State tracker for the current recording session.
    """
    
    def __init__(self, f1_name="Blue", f2_name="Red"):
        """Initializes the OBS manager with fighter context.

        Args:
            f1_name: Name of fighter 1 (defaults to "Blue").
            f2_name: Name of fighter 2 (defaults to "Red").
        """
        self.f1_name = f1_name
        self.f2_name = f2_name
        self.obs_client = None
        self.is_recording = False
        
    def connect(self):
        """Initialize connection to OBS WebSocket server.

        Attempts to establish a connection using credentials stored in 
        environment variables (OBS_PORT, OBS_PASSWORD). If the library is 
        missing or the connection fails, auto-recording is gracefully 
        disabled.
        """
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
        """Signals OBS to start the recording process.

        This is typically called after the match countdown has finished or 
        immediately upon round start to ensure the full sequence is captured.
        """
        if self.obs_client and not self.is_recording:
            try:
                self.obs_client.start_record()
                self.is_recording = True
                print("[OBS] 🎥 Camera Rolling! Recording Started.")
            except Exception as e:
                print(f"[OBS] Start recording failed: {e}")

    def stop_recording(self, viral_title_idea=None):
        """Stops the current recording and executes the file synchronization logic.

        After stopping the recording, this method identifies the newly 
        created file and renames it. Renaming is a critical step for 
        automation, as it maps the generated match to a 'viral' title 
        suitable for social media platforms.

        Args:
            viral_title_idea (str, optional): The hook-driven title generated 
                by the titles module. If None, a default naming scheme is used.
        """
        if self.obs_client and self.is_recording:
            try:
                # Retrieve Recording Path
                record_dir_resp = self.obs_client.get_record_directory()
                record_dir = record_dir_resp.record_directory
                
                # Execute Stop
                self.obs_client.stop_record()
                self.is_recording = False
                
                # The Renaming Sequence
                # We identify the latest file in the recording directory to find the match footage
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
                        
                    # CRITICAL: OBS often keeps a file lock for several hundred milliseconds
                    # after 'stop_record' returns. We use a retry loop to wait for release.
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
                            # File likely still locked by OBS encoder/muxer
                            time.sleep(retry_delay)
                            
                    if not success:
                        print(f"[OBS] Failed to rename. File might still be locked: {latest_file}")
                else:
                    print("[OBS] ⏹️ CUT! Recording Saved.")
            except Exception as e:
                print(f"[OBS] Stop recording failed: {e}")
