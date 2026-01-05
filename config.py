"""
Configuration constants for the Anime Sword Battle game.
Simplified for performance - square 1:1 arena.
"""

# Screen dimensions (1:1 square for simplified visuals)
SCREEN_WIDTH = 800
SCREEN_HEIGHT = 800

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

# Physics constants
DRAG = 0.995  # Very little drag - movement via bouncing
MAX_VELOCITY = 15
BASE_KNOCKBACK = 10
BOUNCE_ENERGY = 0.9  # Energy retained on wall bounce

# Game constants
FPS = 60
FIGHTER_RADIUS = 25  # Smaller fighters
SWORD_LENGTH = 50
SWORD_WIDTH = 4
BASE_HEALTH = 100
ARENA_SHRINK_INTERVAL = 8
ARENA_SHRINK_AMOUNT = 15
POWERUP_SPAWN_MIN = 2.5
POWERUP_SPAWN_MAX = 4.5
MAX_POWERUPS = 2
ROUND_MIN_TIME = 6
ROUND_MAX_TIME = 15

# Hit effects
HIT_STOP_FRAMES = 3
SCREEN_SHAKE_INTENSITY = 8
SCREEN_SHAKE_DECAY = 0.85
