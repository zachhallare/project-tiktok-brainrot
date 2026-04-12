"""
Configuration constants for the Anime Sword Battle game.
DVD logo style - constant velocity bounce with rotating swords.
"""

# Game logic resolution (1:1 square for simplified visuals and physics)
SCREEN_WIDTH = 600
SCREEN_HEIGHT = 600

# High-resolution render canvas (9:16 vertical ratio)
CANVAS_WIDTH = 600
CANVAS_HEIGHT = 1067

# Actual window display resolution (Scaled down to fit comfortably on 1920x1080 screen)
DISPLAY_WIDTH = 540
DISPLAY_HEIGHT = 960

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

# Cyberpunk/Neon Color Palette (YT Shorts Brainrot Style)
NEON_PINK = (255, 110, 255)
NEON_BLUE = (0, 255, 255)
NEON_YELLOW = (255, 255, 0)
NEON_ORANGE = (255, 94, 0)
NEON_MAGENTA = (255, 0, 204)
NEON_GREEN = (204, 255, 0)
NEON_RED = (255, 53, 94)
NEON_PURPLE = (191, 0, 255)

NEON_BG = (20, 20, 25)
NEON_GRID = (35, 35, 45)

NEON_PALETTE = {
    '1': ('PINK', NEON_PINK, (255, 180, 255)),
    '2': ('BLUE', NEON_BLUE, (150, 255, 255)),
    '3': ('YELLOW', NEON_YELLOW, (255, 255, 150)),
    '4': ('ORANGE', NEON_ORANGE, (255, 170, 120)),
    '5': ('MAGENTA', NEON_MAGENTA, (255, 120, 230)),
    '6': ('GREEN', NEON_GREEN, (230, 255, 150)),
    '7': ('RED', NEON_RED, (255, 140, 160)),
    '8': ('PURPLE', NEON_PURPLE, (220, 130, 255))
}

# Glow/Bloom settings
GLOW_ALPHA = 50
GLOW_RADIUS_MULT = 1.8

# Chaos System Constants (tuned for ~15s matches)
CHAOS_MIN_INTERVAL = 1.5  # seconds before event triggers (high frequency)
CHAOS_MAX_INTERVAL = 3.0  # seconds max wait
CHAOS_DURATION = 3.5      # seconds each event lasts

# Motion Trail Settings
TRAIL_LENGTH = 8          # Number of trail positions to store
TRAIL_FADE_RATE = 0.7     # Alpha decay per trail step

# Floating Damage Numbers
DAMAGE_NUMBER_LIFETIME = 45  # frames
DAMAGE_NUMBER_SPEED = 2      # float up speed

# Physics constants - DVD logo style (constant velocity, no drag)
DRAG = 1.0  # No drag - constant velocity like DVD logo
MAX_VELOCITY = 15  # 40% faster for denser collisions
MIN_VELOCITY = 6  # Ensure constant high-energy motion
BASE_KNOCKBACK = 10
BOUNCE_ENERGY = 1.0  # Full energy retained on wall bounce

# Game constants (tuned for ~15s matches)
FPS = 60
FIGHTER_RADIUS = 30  # Smaller fighters
SWORD_LENGTH = 55
SWORD_WIDTH = 6
BASE_HEALTH = 250  # Increased for longer, more exciting fights
DAMAGE_PER_HIT = 15  # +50% damage for faster kills

ROUND_MAX_TIME = 18  # Hard cap prevents stalling

# Slow motion for death sequence
SLOW_MOTION_SPEED = 0.20  # 20% of normal speed

# Hit effects
HIT_STOP_FRAMES = 8
SCREEN_SHAKE_INTENSITY = 15
SCREEN_SHAKE_DECAY = 0.85

# Hit Slow-Motion Effect (sword-body hit)
HIT_SLOWMO_FRAMES = 5          # Duration in frames
HIT_SLOWMO_TIMESCALE = 0.60    # Time scale (60% speed)

# Critical Hit System
CRIT_CHANCE = 0.15             # 15% chance per attack (more spectacle in short matches)
CRIT_MULTIPLIER = 2.0          # 2x damage and knockback
CRIT_IMPACT_FRAMES = 12        # Frames of anime impact freeze
CRIT_IMPACT_TIMESCALE = 0.02   # 2% speed (near-frozen) during impact
GOLD = (255, 215, 0)           # Gold color for crit damage numbers

# Ninja Wall Boost
WALL_BOOST_STRENGTH = 4        # Extra velocity toward center on wall hit


# Arena Escalation (Inactivity Handling)
INACTIVITY_PULSE_TIME = 3.0  # Seconds of inactivity before Arena Pulse triggers
ARENA_PULSE_VELOCITY_BOOST = 4  # Velocity nudge toward center
ARENA_PULSE_SHAKE = 6  # Screen shake intensity for pulse

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
