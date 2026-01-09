"""
Tkinter Control Panel for Red vs Blue Battle.
Collects game configuration before launching Pygame.
"""

import tkinter as tk
from tkinter import ttk, colorchooser
import subprocess
import sys
import os


class ControlPanel:
    """Tkinter-based control panel for game configuration."""
    
    def __init__(self):
        self.root = tk.Tk()
        self.root.title("Red vs Blue Battle - Control Panel")
        self.root.geometry("400x500")
        self.root.resizable(False, False)
        
        # Default settings
        self.settings = {
            'num_rounds': 3,
            'best_of': 3,
            'blue_color': (50, 150, 255),
            'red_color': (255, 80, 80),
            'arena_size': 500,
            'slow_motion_death': True,
        }
        
        self._create_widgets()
    
    def _create_widgets(self):
        """Create all UI widgets."""
        # Title
        title = tk.Label(
            self.root, 
            text="⚔️ Red vs Blue Battle ⚔️",
            font=("Arial", 18, "bold")
        )
        title.pack(pady=15)
        
        # Main frame
        main_frame = ttk.Frame(self.root, padding="10")
        main_frame.pack(fill=tk.BOTH, expand=True)
        
        # Round Settings
        round_frame = ttk.LabelFrame(main_frame, text="Round Settings", padding="10")
        round_frame.pack(fill=tk.X, pady=5)
        
        ttk.Label(round_frame, text="Match Type:").grid(row=0, column=0, sticky=tk.W)
        self.match_type = ttk.Combobox(
            round_frame, 
            values=["Best of 1", "Best of 3", "Best of 5"],
            state="readonly",
            width=15
        )
        self.match_type.set("Best of 3")
        self.match_type.grid(row=0, column=1, padx=5)
        
        # Arena Settings
        arena_frame = ttk.LabelFrame(main_frame, text="Arena Settings", padding="10")
        arena_frame.pack(fill=tk.X, pady=5)
        
        ttk.Label(arena_frame, text="Arena Size:").grid(row=0, column=0, sticky=tk.W)
        self.arena_slider = ttk.Scale(
            arena_frame, 
            from_=350, 
            to=600, 
            orient=tk.HORIZONTAL,
            length=200
        )
        self.arena_slider.set(500)
        self.arena_slider.grid(row=0, column=1, padx=5)
        
        # Effects Settings
        effects_frame = ttk.LabelFrame(main_frame, text="Effects", padding="10")
        effects_frame.pack(fill=tk.X, pady=5)
        
        self.slow_mo_var = tk.BooleanVar(value=True)
        slow_mo_check = ttk.Checkbutton(
            effects_frame, 
            text="Slow-motion death sequence",
            variable=self.slow_mo_var
        )
        slow_mo_check.pack(anchor=tk.W)
        
        # Fighter Colors (display only, shows current defaults)
        color_frame = ttk.LabelFrame(main_frame, text="Fighter Colors", padding="10")
        color_frame.pack(fill=tk.X, pady=5)
        
        # Blue fighter color preview
        ttk.Label(color_frame, text="Blue Fighter:").grid(row=0, column=0, sticky=tk.W)
        self.blue_preview = tk.Canvas(color_frame, width=50, height=25, bg='#3296ff')
        self.blue_preview.grid(row=0, column=1, padx=5)
        
        # Red fighter color preview
        ttk.Label(color_frame, text="Red Fighter:").grid(row=1, column=0, sticky=tk.W, pady=5)
        self.red_preview = tk.Canvas(color_frame, width=50, height=25, bg='#ff5050')
        self.red_preview.grid(row=1, column=1, padx=5, pady=5)
        
        # Buttons
        button_frame = ttk.Frame(main_frame)
        button_frame.pack(fill=tk.X, pady=20)
        
        start_btn = ttk.Button(
            button_frame, 
            text="🎮 Start Game",
            command=self._start_game
        )
        start_btn.pack(side=tk.LEFT, expand=True, padx=5)
        
        quit_btn = ttk.Button(
            button_frame, 
            text="❌ Quit",
            command=self.root.destroy
        )
        quit_btn.pack(side=tk.RIGHT, expand=True, padx=5)
        
        # Info label
        info_label = tk.Label(
            self.root,
            text="Controls: SPACE to pause, R to reset, ESC to exit",
            font=("Arial", 9),
            fg="gray"
        )
        info_label.pack(pady=5)
    
    def _start_game(self):
        """Collect settings and launch the game."""
        # Parse match type
        match_type = self.match_type.get()
        if "1" in match_type:
            best_of = 1
        elif "3" in match_type:
            best_of = 3
        else:
            best_of = 5
        
        # Collect settings
        self.settings = {
            'num_rounds': best_of,
            'best_of': best_of,
            'arena_size': int(self.arena_slider.get()),
            'slow_motion_death': self.slow_mo_var.get(),
        }
        
        # Write settings to config
        self._write_settings()
        
        # Close control panel
        self.root.destroy()
        
        # Launch game
        self._launch_game()
    
    def _write_settings(self):
        """Write settings to a temporary file for the game to read."""
        settings_path = os.path.join(os.path.dirname(__file__), '_game_settings.py')
        with open(settings_path, 'w') as f:
            f.write("# Auto-generated game settings\n")
            f.write(f"SETTINGS = {repr(self.settings)}\n")
    
    def _launch_game(self):
        """Launch the Pygame game."""
        game_path = os.path.join(os.path.dirname(__file__), 'main.py')
        subprocess.Popen([sys.executable, game_path])
    
    def run(self):
        """Start the control panel."""
        self.root.mainloop()


def main():
    """Entry point for the control panel."""
    panel = ControlPanel()
    panel.run()


if __name__ == "__main__":
    main()
