"""
Configuration constants for the Anime Sword Battle game.
DVD logo style - constant velocity bounce with rotating swords.
"""

# Screen dimensions (1:1 square for simplified visuals)
SCREEN_WIDTH = 600
SCREEN_HEIGHT = 600

# Arena (square, smaller)
ARENA_MARGIN = 40
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

# Physics constants - DVD logo style (constant velocity, no drag)
DRAG = 1.0  # No drag - constant velocity like DVD logo
MAX_VELOCITY = 20  # Faster gameplay
MIN_VELOCITY = 10  # Higher minimum speed
BASE_KNOCKBACK = 10
BOUNCE_ENERGY = 1.0  # Full energy retained on wall bounce

# Game constants
FPS = 60
FIGHTER_RADIUS = 30  # Smaller fighters
SWORD_LENGTH = 55
SWORD_WIDTH = 6
BASE_HEALTH = 240  # Increased for ~30 second fights
DAMAGE_PER_HIT = 10  # Reduced damage for longer fights
ARENA_SHRINK_INTERVAL = 10
ARENA_SHRINK_AMOUNT = 12
POWERUP_SPAWN_MIN = 1.0
POWERUP_SPAWN_MAX = 3.0
MAX_POWERUPS = 10
ROUND_MIN_TIME = 6
ROUND_MAX_TIME = 45  # Longer max time

# Slow motion for death sequence
SLOW_MOTION_SPEED = 0.20  # 20% of normal speed

# Hit effects
HIT_STOP_FRAMES = 3
SCREEN_SHAKE_INTENSITY = 8
SCREEN_SHAKE_DECAY = 0.85

# Parry Slow-Motion Effect (samurai-style) - sword-sword parry
PARRY_SLOWMO_FRAMES = 10       # Duration in frames
PARRY_SLOWMO_TIMESCALE = 0.30  # Time scale (30% speed)
PARRY_HITSTOP_FRAMES = 2       # Small hit-stop stacked on slow-mo

# Hit Slow-Motion Effect (sword-body hit)
HIT_SLOWMO_FRAMES = 5          # Duration in frames
HIT_SLOWMO_TIMESCALE = 0.60    # Time scale (60% speed)

# Ninja Wall Boost
WALL_BOOST_STRENGTH = 4        # Extra velocity toward center on wall hit

# Rotational Weapon Attack System - CONSTANT rotation like DVD logo
WEAPON_ROTATION_SPEED = 0.18   # Radians per frame (~10.3°/frame)
ROTATION_PARRY_DISTANCE = 18   # Sword-to-sword collision threshold
ROTATION_BODY_HIT_BONUS = 6    # Extra hit radius for sword-to-body

# Arena Escalation (Inactivity Handling)
INACTIVITY_PULSE_TIME = 5  # Seconds before Arena Pulse triggers
INACTIVITY_SHRINK_TIME = 3  # Additional seconds before shrinking starts
ARENA_PULSE_VELOCITY_BOOST = 4  # Velocity nudge toward center
ARENA_PULSE_SHAKE = 6  # Screen shake intensity for pulse
ESCALATION_SHRINK_SPEED = 0.3  # Pixels per frame during inactivity shrink

# Game Settings
GAME_SETTINGS = {
    'num_rounds': 3,
    'best_of': 3,
    'blue_color': BLUE,
    'blue_bright': BLUE_BRIGHT,
    'red_color': RED,
    'red_bright': RED_BRIGHT,
    'arena_size': 500,
    'slow_motion_death': True,
}

def update_settings(new_settings):
    """Update game settings."""
    global GAME_SETTINGS
    GAME_SETTINGS.update(new_settings)
