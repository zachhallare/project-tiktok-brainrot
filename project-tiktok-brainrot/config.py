"""
Configuration constants for the Anime Sword Battle game.
Simplified for performance - square 1:1 arena.
"""

# Screen dimensions (1:1 square for simplified visuals)
SCREEN_WIDTH = 600
SCREEN_HEIGHT = 600

# Arena (square, smaller)
ARENA_MARGIN = 50
ARENA_WIDTH = SCREEN_WIDTH - ARENA_MARGIN * 2
ARENA_HEIGHT = SCREEN_HEIGHT - ARENA_MARGIN * 2

# Colors
BLACK = (0, 0, 0)
WHITE = (255, 255, 255)
DARK_GRAY = (30, 30, 30)
GRAY = (60, 60, 60)
BLUE = (50, 150, 255)
BLUE_BRIGHT = (120, 200, 255)
RED = (255, 80, 80)
RED_BRIGHT = (255, 150, 150)
YELLOW = (255, 220, 100)
GREEN = (100, 255, 150)
PURPLE = (200, 100, 255)
CYAN = (100, 255, 255)
ORANGE = (255, 180, 80)
GOLD = (255, 215, 0)
PINK = (255, 100, 200)

# Physics constants
DRAG = 1.0  # No drag - constant velocity like DVD logo
MAX_VELOCITY = 25  # Faster gameplay
MIN_VELOCITY = 6  # Higher minimum speed
BASE_KNOCKBACK = 10
BOUNCE_ENERGY = 1.0  # Full energy retained on wall bounce

# Game constants
FPS = 60
FIGHTER_RADIUS = 25  # Smaller fighters
SWORD_LENGTH = 45
SWORD_WIDTH = 4
BASE_HEALTH = 200  # Increased for ~30 second fights
DAMAGE_PER_HIT = 8  # Reduced damage for longer fights
ARENA_SHRINK_INTERVAL = 10
ARENA_SHRINK_AMOUNT = 12
POWERUP_SPAWN_MIN = 2.0
POWERUP_SPAWN_MAX = 4.0
MAX_POWERUPS = 3
ROUND_MIN_TIME = 6
ROUND_MAX_TIME = 45  # Longer max time

# Slow motion for death sequence
SLOW_MOTION_SPEED = 0.20  # 25% of normal speed

# Hit effects
HIT_STOP_FRAMES = 3
SCREEN_SHAKE_INTENSITY = 8
SCREEN_SHAKE_DECAY = 0.85

# Arena Escalation (Inactivity Handling)
INACTIVITY_PULSE_TIME = 5  # Seconds before Arena Pulse triggers
INACTIVITY_SHRINK_TIME = 3  # Additional seconds before shrinking starts
ARENA_PULSE_VELOCITY_BOOST = 4  # Velocity nudge toward center
ARENA_PULSE_SHAKE = 6  # Screen shake intensity for pulse
ESCALATION_SHRINK_SPEED = 0.3  # Pixels per frame during inactivity shrink

# Game Settings (configurable via Tkinter UI)
GAME_SETTINGS = {
    'num_rounds': 3,
    'best_of': 3,
    'blue_color': BLUE,
    'blue_bright': BLUE_BRIGHT,
    'red_color': RED,
    'red_bright': RED_BRIGHT,
    'arena_size': 500,  # Base arena dimension
    'slow_motion_death': True,
}

def update_settings(new_settings):
    """Update game settings from Tkinter UI."""
    global GAME_SETTINGS
    GAME_SETTINGS.update(new_settings)
