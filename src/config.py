"""
Configuration constants for the Anime Sword Battle game.
DVD logo style - constant velocity bounce with rotating swords.
"""

SCREEN_WIDTH = 600
SCREEN_HEIGHT = 600
CANVAS_WIDTH = 600
CANVAS_HEIGHT = 1067
DISPLAY_WIDTH = 540
DISPLAY_HEIGHT = 960

ARENA_MARGIN = 40
ARENA_WIDTH = SCREEN_WIDTH - ARENA_MARGIN * 2
ARENA_HEIGHT = SCREEN_HEIGHT - ARENA_MARGIN * 2

BLACK = (0, 0, 0)
ARENA_BG = (26, 26, 26)
WHITE = (255, 255, 255)
DARK_GRAY = (30, 30, 30)
GRAY = (60, 60, 60)
YELLOW = (255, 220, 100)
PURPLE = (200, 100, 255)

RED = (255, 0, 0)
ORANGE = (255, 128, 0)
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
    "RED": RED, "ORANGE": ORANGE, "YELLOW": YELLOW_WHEEL, "LIME": LIME,
    "GREEN": GREEN, "SPRING": SPRING, "CYAN": CYAN, "AZURE": AZURE,
    "BLUE": BLUE, "PURPLE": PURPLE_WHEEL, "MAGENTA": MAGENTA, "ROSE": ROSE
}

NEON_BG = (20, 20, 25)
NEON_GRID = (35, 35, 45)

GLOW_ALPHA = 50
GLOW_RADIUS_MULT = 1.8

TRAIL_LENGTH = 8
TRAIL_FADE_RATE = 0.7

DAMAGE_NUMBER_LIFETIME = 45
DAMAGE_NUMBER_SPEED = 2

DRAG = 1.0
MAX_VELOCITY = 15
MIN_VELOCITY = 6
BASE_KNOCKBACK = 10
BOUNCE_ENERGY = 1.0

FPS = 60
FIGHTER_RADIUS = 30
SWORD_LENGTH = 40
SWORD_WIDTH = 6
BASE_HEALTH = 250
DAMAGE_PER_HIT = 15

ROUND_MAX_TIME = 18
SLOW_MOTION_SPEED = 0.20

HIT_STOP_FRAMES = 8
HAMMER_HIT_STOP_FRAMES = 30
SCREEN_SHAKE_INTENSITY = 15
SCREEN_SHAKE_DECAY = 0.85

HIT_SLOWMO_FRAMES = 5
HIT_SLOWMO_TIMESCALE = 0.60

CRIT_CHANCE = 0.20
CRIT_MULTIPLIER = 2.0
CRIT_IMPACT_FRAMES = 12
CRIT_IMPACT_TIMESCALE = 0.02
GOLD = (255, 215, 0)

WALL_BOOST_STRENGTH = 4

INACTIVITY_PULSE_TIME = 2.5
ARENA_PULSE_VELOCITY_BOOST = 4
ARENA_PULSE_SHAKE = 6

# ── Momentum System ───────────────────────────────────────────────────────────
# Fighters build momentum stacks by landing hits. Each stack adds
# MOMENTUM_DAMAGE_BONUS to the damage multiplier. Taking damage resets to 0.
MOMENTUM_MAX_STACKS   = 5
MOMENTUM_DAMAGE_BONUS = 0.06   # +6% per stack → max +30% at 5 stacks

GAME_SETTINGS = {
    'num_rounds': 3,
    'best_of': 3,
    'arena_size': 500,
    'slow_motion_death': True,
}

# ── Weapon Configurations ─────────────────────────────────────────────────────
# sprite_size          : (width, height) in pixels
# sword_length         : reach in px from body edge to tip (drives hitbox)
# damage_mult          : multiplier on base damage
# handle_ratio         : t-values below this = handle, no damage
# hitbox_profile       : list of (t, half_width_px)
#
# ── Behaviour fields ─────────────────────────────────────────────────────────
# spin_speed_mult      : multiplies base 0.25 rad/frame spin speed
# knockback_mult       : weapon knockback multiplier (stacks with chaos mult)
# sweet_spot_threshold : impact_ratio >= this → sweet-spot hit
#                        ignored when all_sweet_spot is True
# all_sweet_spot       : True → every hit treated as sweet-spot
# reverses_spin        : True → on body hit, flip defender spin_direction
# max_hitstop          : True → override hit_stop to HAMMER_HIT_STOP_FRAMES
# parry_drain_mult     : multiplier on defender parry_cost when blocking this weapon
# momentum_gain        : stacks added to attacker momentum per successful body hit
WEAPON_CONFIGS = {
    'sword': {
        'sprite_file': 'sword.png',
        'sprite_size': (87, 23),
        'sword_length': 40,
        'damage_mult': 1.0,
        'handle_ratio': 0.25,
        'hitbox_profile': [
            (0.25, 6),
            (0.50, 9),
            (0.75, 7),
            (1.00, 4),
        ],
        'spin_speed_mult': 1.0,
        'knockback_mult': 1.0,
        'sweet_spot_threshold': 0.70,
        'all_sweet_spot': False,
        'reverses_spin': False,
        'max_hitstop': False,
        'parry_drain_mult': 1.0,
        'momentum_gain': 1,
    },

    'dagger': {
        'sprite_file': 'dagger.png',
        'sprite_size': (48, 14),
        'sword_length': 20,
        'damage_mult': 1.1,
        'handle_ratio': 0.30,
        'hitbox_profile': [
            (0.30, 4),
            (0.60, 5),
            (0.85, 4),
            (1.00, 2),
        ],
        'spin_speed_mult': 2.2,
        'knockback_mult': 0.7,
        'sweet_spot_threshold': 0.70,
        'all_sweet_spot': False,
        'reverses_spin': False,
        'max_hitstop': False,
        'parry_drain_mult': 1.75,
        'momentum_gain': 2,
    },

    'spear': {
        'sprite_file': 'spear.png',
        'sprite_size': (174, 13),
        'sword_length': 148,
        'damage_mult': 1.3,
        'handle_ratio': 0.78,
        'hitbox_profile': [
            (0.72,  3),
            (0.85,  6),
            (0.93,  7),
            (1.00,  3),
        ],
        'spin_speed_mult': 0.75,
        'knockback_mult': 1.0,
        'sweet_spot_threshold': 0.90,
        'all_sweet_spot': False,
        'reverses_spin': False,
        'max_hitstop': False,
        'parry_drain_mult': 1.0,
        'momentum_gain': 1,
    },

    'axe': {
        'sprite_file': 'axe.png',
        'sprite_size': (70, 32),
        'sword_length': 33,
        'damage_mult': 1.2,
        'handle_ratio': 0.45,
        'hitbox_profile': [
            (0.45,  5),
            (0.62, 18),
            (0.78, 24),
            (0.90, 22),
            (1.00, 14),
        ],
        'spin_speed_mult': 0.6,
        'knockback_mult': 2.0,
        'sweet_spot_threshold': 0.0,
        'all_sweet_spot': True,
        'reverses_spin': False,
        'max_hitstop': False,
        'parry_drain_mult': 1.0,
        'momentum_gain': 1,
    },

    'hammer': {
        'sprite_file': 'hammer.png',
        'sprite_size': (63, 25),
        'sword_length': 29,
        # Low damage — hammer wins through disruption, not raw DPS.
        # Every hit reverses the defender's spin and locks both fighters in
        # maximum hitstop, turning the match into pure chaos.
        'damage_mult': 0.45,
        'handle_ratio': 0.48,
        'hitbox_profile': [
            (0.48,  4),
            (0.65, 20),
            (0.80, 22),
            (0.93, 22),
            (1.00, 18),
        ],
        'spin_speed_mult': 0.45,
        'knockback_mult': 1.5,
        'sweet_spot_threshold': 0.0,
        'all_sweet_spot': True,
        'reverses_spin': True,   # core identity — every hit disorients
        'max_hitstop': True,     # maximum freeze on every hit
        'parry_drain_mult': 1.0,
        'momentum_gain': 0,
    },
}