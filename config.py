# ==============================================================================
# Physics Battle Animation - Configuration
# All tweakable parameters for the simulation
# ==============================================================================

# --- Video Format (TikTok Vertical) ---
WIDTH = 1080
HEIGHT = 1920
FPS = 60
DURATION = 30  # seconds

# --- Colors ---
COLORS = {
    "red": (255, 60, 60),
    "blue": (60, 120, 255),
    "background": (15, 15, 20),
    "wall": (40, 40, 50),
}

# --- Physics ---
GRAVITY = 1800  # pixels/s² downward
FRICTION = 0.6
ELASTICITY = 0.75
DAMPING = 0.98  # velocity damping

# --- Teams ---
TEAM_SIZES = {"red": 12, "blue": 12}
BALL_MASS_RANGE = (1.0, 2.5)
BALL_RADIUS_RANGE = (28, 45)
INITIAL_HEALTH = 100

# --- Combat ---
DAMAGE_MULTIPLIER = 0.15  # damage = relative_velocity * mass * multiplier
CRITICAL_HIT_CHANCE = 0.12
CRITICAL_HIT_MULTIPLIER = 2.5
KNOCKBACK_FORCE = 800

# --- Visual Effects ---
PARTICLE_COUNT_ON_HIT = 8
PARTICLE_COUNT_ON_DEATH = 25
SCREEN_SHAKE_INTENSITY = 15
SCREEN_SHAKE_DECAY = 0.85
TRAIL_LENGTH = 5
GLOW_INTENSITY = 0.7

# --- Sound ---
SAMPLE_RATE = 44100
SOUND_VOLUME = 0.7

# --- Camera ---
CAMERA_SMOOTHING = 0.08
ZOOM_SMOOTHING = 0.05
MIN_ZOOM = 0.7
MAX_ZOOM = 1.2

# --- Slow Motion ---
SLOWMO_THRESHOLD = 3  # Trigger when <= this many balls remain
SLOWMO_FACTOR = 0.3
SLOWMO_DURATION = 2.0  # seconds

# --- Paths ---
OUTPUT_FILE = "output.mp4"
TEMP_FRAMES_DIR = "temp_frames"
