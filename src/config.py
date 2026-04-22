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
ARENA_BG = (26, 26, 26)  # Dark grey arena fill (~#1a1a1a) for better trail/particle visibility
WHITE = (255, 255, 255)
DARK_GRAY = (30, 30, 30)
GRAY = (60, 60, 60)
YELLOW = (255, 220, 100)
PURPLE = (200, 100, 255)

# 12-Slice Color Wheel Palette
RED = (255, 0, 0)
ORANGE = (255, 128, 0)
# YELLOW already defined above as UI color; wheel yellow below is pure (255,255,0)
LIME = (128, 255, 0)
GREEN = (0, 255, 0)
SPRING = (0, 255, 128)
CYAN = (0, 255, 255)
AZURE = (0, 128, 255)
BLUE = (0, 0, 255)
PURPLE_WHEEL = (128, 0, 255)
MAGENTA = (255, 0, 255)
ROSE = (255, 0, 128)
YELLOW_WHEEL = (255, 255, 0)

BASE_COLORS = {
    "RED": RED,
    "ORANGE": ORANGE,
    "YELLOW": YELLOW_WHEEL,
    "LIME": LIME,
    "GREEN": GREEN,
    "SPRING": SPRING,
    "CYAN": CYAN,
    "AZURE": AZURE,
    "BLUE": BLUE,
    "PURPLE": PURPLE_WHEEL,
    "MAGENTA": MAGENTA,
    "ROSE": ROSE
}

# Background / Grid (kept for arena drawing)
NEON_BG = (20, 20, 25)
NEON_GRID = (35, 35, 45)

# Glow/Bloom settings
GLOW_ALPHA = 50
GLOW_RADIUS_MULT = 1.8



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
SWORD_LENGTH = 40
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
INACTIVITY_PULSE_TIME = 2.5  # Seconds of inactivity before Arena Pulse triggers
ARENA_PULSE_VELOCITY_BOOST = 4  # Velocity nudge toward center
ARENA_PULSE_SHAKE = 6  # Screen shake intensity for pulse

# Game Settings
GAME_SETTINGS = {
    'num_rounds': 3,
    'best_of': 3,
    'arena_size': 500,
    'slow_motion_death': True,
}

# ── Weapon Configurations ─────────────────────────────────────────────────────
# sprite_size  : (width, height) in pixels — sword is the reference at (87, 27)
# sword_length : reach in px from the body edge to the tip (drives hitbox)
# damage_mult  : multiplier applied to base damage (bigger/heavier = more damage)
# handle_ratio : t-values below this are handle — no damage zone
# hitbox_profile: list of (t, half_width_px)
#   t=0.0 = handle attachment point, t=1.0 = weapon tip
#   half_width_px = dangerous radius of the weapon cross-section at that point
WEAPON_CONFIGS = {
    'sword': {
        'sprite_file': 'sword.png',
        'sprite_size': (87, 27),
        'sword_length': 40,
        'damage_mult': 1.0,
        'handle_ratio': 0.25,
        'hitbox_profile': [
            (0.25, 6),
            (0.50, 9),
            (0.75, 7),
            (1.00, 4),
        ],
    },
    'dagger': {
        'sprite_file': 'dagger.png',
        'sprite_size': (38, 18),
        'sword_length': 17,
        'damage_mult': 0.75,
        'handle_ratio': 0.30,
        'hitbox_profile': [
            (0.30, 4),
            (0.60, 5),
            (0.85, 4),
            (1.00, 2),
        ],
    },
    'spear': {
        'sprite_file': 'spear.png',
        'sprite_size': (174, 18),
        'sword_length': 148,
        'damage_mult': 0.9,
        'handle_ratio': 0.72,   # almost all shaft — only tip scores
        'hitbox_profile': [
            (0.72,  3),
            (0.85,  6),
            (0.93,  7),
            (1.00,  3),
        ],
    },
    'axe': {
        'sprite_file': 'axe.png',
        'sprite_size': (70, 56),
        'sword_length': 33,
        'damage_mult': 1.4,
        'handle_ratio': 0.45,
        'hitbox_profile': [
            (0.45,  5),
            (0.62, 18),
            (0.78, 24),
            (0.90, 22),
            (1.00, 14),
        ],
    },
    'hammer': {
        'sprite_file': 'hammer.png',
        'sprite_size': (63, 50),
        'sword_length': 29,
        'damage_mult': 1.6,
        'handle_ratio': 0.48,
        'hitbox_profile': [
            (0.48,  4),
            (0.65, 20),
            (0.80, 22),
            (0.93, 22),
            (1.00, 18),
        ],
    },
}

