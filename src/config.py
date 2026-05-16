"""
Configuration constants for the AlgoRot algorithmic battle simulation.

This module serves as the central source of truth for all simulation tuning,
physics constants, and weapon archetypes. The values are calibrated to 
produce high-impact, cinematic combat optimized for short-form video 
consumption (YouTube Shorts), prioritizing "game feel" and visual "juice" 
over realistic physics.

Design Philosophy:
    1. High Contrast: Neon visuals against dark backgrounds for clarity.
    2. Tactile Feedback: Heavy use of hit-stops, screen shake, and slow-mo.
    3. Three-Act Pacing: Combat progresses from "The Clash" (neutral) to 
       "The Break" (guard break) to "The Punish" (lethal damage).
    4. Archetypal Balance: Each weapon has a distinct role (e.g., the 
       disorienting Hammer vs. the rapid-fire Dagger).
"""

# --- Display & Arena ---
# Standard 9:16 aspect ratio (1080x1920 scaled down) for social media compatibility.
SCREEN_WIDTH = 600
SCREEN_HEIGHT = 600
CANVAS_WIDTH = 600
CANVAS_HEIGHT = 1067
DISPLAY_WIDTH = 540
DISPLAY_HEIGHT = 960

# ARENA_MARGIN provides a buffer to prevent fighters from clipping into UI elements.
ARENA_MARGIN = 40
ARENA_WIDTH = SCREEN_WIDTH - ARENA_MARGIN * 2
ARENA_HEIGHT = SCREEN_HEIGHT - ARENA_MARGIN * 2

# --- Color Palette ---
BLACK = (0, 0, 0)
ARENA_BG = (26, 26, 26)
WHITE = (255, 255, 255)
DARK_GRAY = (30, 30, 30)
GRAY = (60, 60, 60)
PULSE_WHITE = (220, 215, 200)  # Warm off-white for arena pulse — visible on dark BG, no fighter clash.
YELLOW = (255, 220, 100)
PURPLE = (200, 100, 255)

RED = (255, 0, 0)
ORANGE = (255, 128, 0)
YELLOW_WHEEL = (255, 255, 0)
LIME = (128, 255, 0)
GREEN = (0, 255, 0)
SPRING = (0, 255, 128)
CYAN = (0, 255, 255)
AZURE = (0, 128, 255)
BLUE = (0, 0, 255)
PURPLE_WHEEL = (128, 0, 255)
MAGENTA = (255, 0, 255)
ROSE = (255, 0, 128)

BASE_COLORS = {
    "RED": RED, "ORANGE": ORANGE, "YELLOW": YELLOW_WHEEL, "LIME": LIME,
    "GREEN": GREEN, "SPRING": SPRING, "CYAN": CYAN, "AZURE": AZURE,
    "BLUE": BLUE, "PURPLE": PURPLE_WHEEL, "MAGENTA": MAGENTA, "ROSE": ROSE
}

NEON_BG = (20, 20, 25)
NEON_GRID = (35, 35, 45)

# --- Rendering & "Juice" ---
GLOW_ALPHA = 50
GLOW_RADIUS_MULT = 1.8

# Trail length is a key visual indicator of speed and momentum.
TRAIL_LENGTH = 8        # Baseline trail length.
TRAIL_FADE_RATE = 0.7   # Speed at which trail segments disappear.

DAMAGE_NUMBER_LIFETIME = 45 # Frames before damage UI fades.
DAMAGE_NUMBER_SPEED = 2     # Upward drift of damage numbers.

# --- Physics & Movement ---
# DRAG 1.0 implies perfect conservation of energy; reduced if air resistance is needed.
DRAG = 1.0
# Velocity limits prevent fighters from "teleporting" (too fast) or becoming static (too slow).
MAX_VELOCITY = 15
MIN_VELOCITY = 6
BASE_KNOCKBACK = 10
# BOUNCE_ENERGY 1.0 preserves all momentum on wall hit, keeping the pace high.
BOUNCE_ENERGY = 1.0

FPS = 60
FIGHTER_RADIUS = 30
SWORD_LENGTH = 40
SWORD_WIDTH = 6

# --- Combat Dynamics ---
BASE_HEALTH = 250       # Normalized starting HP.
DAMAGE_PER_HIT = 15     # Baseline damage used for calculation.

# ROUND_MAX_TIME is strictly tuned for short-form retention (approx 15-20s).
ROUND_MAX_TIME = 18
SLOW_MOTION_SPEED = 0.20 # Intensity of the final blow's cinematic slowdown.

# --- Hit Feedback (Juice) ---
# Hit-stop (freezing the simulation) creates a sense of physical impact weight.
HIT_STOP_FRAMES = 8
HAMMER_NORMAL_HIT_STOP = 7      # Heavy weapon impact.
HAMMER_HIT_STOP_FRAMES = 13      # Critical heavy weapon impact.
SCREEN_SHAKE_INTENSITY = 15
SCREEN_SHAKE_DECAY = 0.85

# Brief time dilation after any hit to allow the viewer to process the impact.
HIT_SLOWMO_FRAMES = 5
HIT_SLOWMO_TIMESCALE = 0.60

# --- RNG & Momentum ---
CRIT_CHANCE = 0.20
CRIT_MULTIPLIER = 1.6
CRIT_IMPACT_FRAMES = 12
CRIT_IMPACT_TIMESCALE = 0.02
GOLD = (255, 215, 0)

# Reward for aggressive movement against walls.
WALL_BOOST_STRENGTH = 4

# Anti-staleness: pulses the arena to force interactions if no hits occur.
INACTIVITY_PULSE_TIME = 2.5
ARENA_PULSE_VELOCITY_BOOST = 4
ARENA_PULSE_SHAKE = 6

# MOMENTUM: A snowball mechanic rewarding consecutive successful hits.
MOMENTUM_MAX_STACKS   = 3
MOMENTUM_DAMAGE_BONUS = 0.06   # +6% per stack → max +18% at 3 stacks

# --- Parry & Energy System (The Three-Act Pacing) ---
# Act 1: The Clash — Standard parries drain energy pool.
# Act 2: The Break — Energy depletion leads to Guard Break stun.
# Act 3: The Punish — Stunned fighters take significantly more damage.
BASE_PARRY_ENERGY       = 100       # Total parry/energy pool.
PARRY_DRAIN_BASE        = 12        # Energy cost per parry.
PARRY_REGEN_RATE        = 0.12      # Passive energy recovery per frame.
PARRY_COOLDOWN_FRAMES   = 12        # Prevents "spamming" parries.

# Guard Break sequence parameters for maximum drama.
GUARD_BREAK_STUN_FRAMES   = 45      # Total paralysis duration (0.75s).
GUARD_BREAK_KNOCKBACK     = 22      # Massive shove to isolate the target.
GUARD_BREAK_HIT_STOP      = 20      # Dramatic freeze on break.
GUARD_BREAK_DAMAGE_MIN    = 15      
GUARD_BREAK_DAMAGE_MAX    = 30      
GUARD_BREAK_SCREEN_SHAKE  = 30      

GAME_SETTINGS = {
    'num_rounds': 3,
    'best_of': 3,
    'arena_size': 500,
    'slow_motion_death': True,
}

# --- Weapon Configurations ---
# archetypes are defined by a mix of physical reach, damage potential, 
# and behavioral traits like 'reverses_spin' or 'momentum_gain'.

WEAPON_CONFIGS = {
    'sword': {
        'sprite_file': 'sword.png',
        'sprite_size': (87, 23),
        'sword_length': 40,
        'damage_mult': 1.20,
        'handle_ratio': 0.25,
        'hitbox_profile': [(0.25, 6), (0.50, 9), (0.75, 7), (1.00, 4)],
        'spin_speed_mult': 0.90, # Balanced rotation.
        'knockback_mult': 1.0,
        'sweet_spot_threshold': 0.70,
        'all_sweet_spot': False,
        'reverses_spin': False,
        'max_hitstop': False,
        'parry_drain_mult': 0.75, # Defensive specialist.
        'momentum_gain': 1,
        'base_health': 250,
        'move_speed_mult': 1.0,
        'trail_length': 8
    },

    'dagger': {
        'sprite_file': 'dagger.png',
        'sprite_size': (48, 14),
        'sword_length': 20,
        'damage_mult': 1.62, # Glass cannon — high damage, low reach.
        'handle_ratio': 0.30,
        'hitbox_profile': [(0.30, 4), (0.60, 5), (0.85, 4), (1.00, 2)],
        'spin_speed_mult': 1.0,   # Very fast rotation.
        'knockback_mult': 0.5,
        'sweet_spot_threshold': 0.70,
        'all_sweet_spot': False,
        'reverses_spin': False,
        'max_hitstop': False,
        'parry_drain_mult': 1.6,  # Aggressive: drains opponent's energy fast.
        'momentum_gain': 2,       
        'base_health': 250,       # Fragile.
        'move_speed_mult': 1.35,  # Highest agility.
        'trail_length': 12        # Enhanced visual flair.
    },

    'spear': {
        'sprite_file': 'spear.png',
        'sprite_size': (174, 13),
        'sword_length': 120, # Massive reach for spacing control.
        'damage_mult': 1.10,
        'handle_ratio': 0.8,
        'hitbox_profile': [(0.72, 3), (0.85, 6), (0.93, 7), (1.00, 3)],
        'spin_speed_mult': 0.58,  # Slower, deliberate rotation.
        'knockback_mult': 0.8,
        'sweet_spot_threshold': 0.82,
        'all_sweet_spot': False,
        'reverses_spin': False,
        'max_hitstop': False,
        'parry_drain_mult': 1.0,
        'momentum_gain': 1,
        'base_health': 255,
        'move_speed_mult': 1.05,
        'trail_length': 8
    },

    'axe': {
        'sprite_file': 'axe.png',
        'sprite_size': (70, 32),
        'sword_length': 33,
        'damage_mult': 1.27,
        'handle_ratio': 0.45,
        'hitbox_profile': [(0.45, 4), (0.62, 14), (0.78, 18), (0.90, 16), (1.00, 10)],
        'spin_speed_mult': 0.55,
        'knockback_mult': 1.05,    
        'sweet_spot_threshold': 0.68,
        'all_sweet_spot': False,
        'reverses_spin': False,
        'max_hitstop': False,
        'parry_drain_mult': 1.0,
        'momentum_gain': 1,
        'base_health': 215,
        'move_speed_mult': 0.85,
        'trail_length': 8
    },

    'hammer': {
        'sprite_file': 'hammer.png',
        'sprite_size': (63, 25),
        'sword_length': 29,
        'damage_mult': 0.88,
        'handle_ratio': 0.48,
        'hitbox_profile': [(0.48, 4), (0.65, 20), (0.80, 22), (0.93, 22), (1.00, 18)],
        'spin_speed_mult': 0.53,
        'knockback_mult': 0.9,
        'sweet_spot_threshold': 0.0,
        'all_sweet_spot': True,
        'reverses_spin': True,    # Core Identity: Every hit disorients opponent spin.
        'max_hitstop': True,      # Forces dramatic freeze frames on every hit.
        'parry_drain_mult': 1.0,
        'momentum_gain': 0,
        'base_health': 232,       # Tank profile.
        'move_speed_mult': 0.96,
        'trail_length': 8
    },
}