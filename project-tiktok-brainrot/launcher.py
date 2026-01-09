"""
Launcher for Red vs Blue Battle.
Opens Tkinter control panel, then launches Pygame game.
"""

import os
import sys

# Add current directory to path
sys.path.insert(0, os.path.dirname(__file__))


def main():
    """Main entry point - opens control panel."""
    from ui import ControlPanel
    panel = ControlPanel()
    panel.run()


if __name__ == "__main__":
    main()
