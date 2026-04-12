import pygame
import math
import random
import os

try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass

try:
    import obsws_python as obs
except ImportError:
    obs = None

# Import constants and classes from other modules.
from config import (
    SCREEN_WIDTH, SCREEN_HEIGHT, CANVAS_WIDTH, CANVAS_HEIGHT, DISPLAY_WIDTH, DISPLAY_HEIGHT, FPS,
    WHITE, PURPLE, BLACK, DARK_GRAY, GRAY, YELLOW,
    ARENA_MARGIN, ARENA_WIDTH, ARENA_HEIGHT,
    ROUND_MAX_TIME, BASE_KNOCKBACK, DAMAGE_PER_HIT, SLOW_MOTION_SPEED,
    HIT_STOP_FRAMES, SCREEN_SHAKE_INTENSITY, SCREEN_SHAKE_DECAY,
    HIT_SLOWMO_FRAMES, HIT_SLOWMO_TIMESCALE,
    INACTIVITY_PULSE_TIME, ARENA_PULSE_VELOCITY_BOOST,
    ARENA_PULSE_SHAKE,
    NEON_RED, NEON_BLUE, NEON_BG, NEON_GRID,
    CRIT_CHANCE, CRIT_MULTIPLIER, CRIT_IMPACT_FRAMES, CRIT_IMPACT_TIMESCALE
)
from effects import ParticleSystem, ShockwaveSystem, ArenaPulseSystem, DamageNumberSystem
from fighter import Fighter
from chaos_manager import ChaosManager, ChaosTextRenderer


# Main game class - DVD logo style combat with rotating swords.
class Game:    
    def __init__(self, f1_key='5', f2_key='1'):
        from config import NEON_PALETTE
        
        f1_name, f1_col, f1_bright = NEON_PALETTE.get(f1_key, NEON_PALETTE['5'])
        f2_name, f2_col, f2_bright = NEON_PALETTE.get(f2_key, NEON_PALETTE['1'])
        
        self.f1_color = f1_col
        self.f1_bright = f1_bright
        self.f1_name = f1_name
        self.f2_color = f2_col
        self.f2_bright = f2_bright
        self.f2_name = f2_name
        
        # Initialize pygame modules
        pygame.init()
        pygame.mixer.init()
        pygame.font.init()
        
        # Create the game window.
        self.window = pygame.display.set_mode((DISPLAY_WIDTH, DISPLAY_HEIGHT), pygame.NOFRAME)
        self.canvas = pygame.Surface((CANVAS_WIDTH, CANVAS_HEIGHT))
        self.screen = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT))
        pygame.display.set_caption("Red vs Blue Battle - YT Shorts Edition")
        self.clock = pygame.time.Clock()
        
        # Fonts for UI text
        self.font_large = pygame.font.Font(None, 120)
        self.font_medium = pygame.font.Font(None, 72)
        self.font_small = pygame.font.Font(None, 36)
        
        # Define the base arena square.
        self.base_arena = (ARENA_MARGIN, ARENA_MARGIN, ARENA_WIDTH, ARENA_HEIGHT)
        self.arena_bounds = list(self.base_arena)
        
        # Use neon colors for fighters
        spawn_margin = 100
        center_y = SCREEN_HEIGHT // 2
        self.blue = Fighter(ARENA_MARGIN + spawn_margin, center_y, 
                            self.f1_color, self.f1_bright, is_blue=True)
        self.red = Fighter(SCREEN_WIDTH - ARENA_MARGIN - spawn_margin, center_y, 
                            self.f2_color, self.f2_bright, is_blue=False)
        
        # Lock fighters for countdown
        self._lock_fighters_for_countdown()
        
        # Visual effect systems.
        self.particles = ParticleSystem()
        self.shockwaves = ShockwaveSystem()
        self.arena_pulses = ArenaPulseSystem()
        self.damage_numbers = DamageNumberSystem()
        
        # Chaos Manager for TikTok Brainrot events
        self.chaos = ChaosManager(self.f1_color, self.f2_color)
        self.chaos_text = ChaosTextRenderer()
        
        # Screen effects.
        self.screen_shake = 0
        self.hit_stop = 0
        self.hit_slowmo_frames = 0
        self.hit_slowmo_accumulator = 0.0
        
        # Critical Hit Impact Sequence
        self.crit_impact_frames = 0
        self.crit_impact_accumulator = 0.0
        self.crit_flash_phase = 0  # 0=none, 1=black, 2=white, 3+=done
        
        # Round state tracking.
        self.round_timer = 0
        self.round_ending = False
        self.winner = None
        self.winner_text = ""
        self.reset_timer = 0
        
        # UI controls.
        self.paused = False
        self.slow_motion = False
        self.slow_motion_accumulator = 0.0
        
        # Pre-fight countdown (rapid 0.25s ticks for Shorts retention)
        self.countdown_stage = 0
        self.countdown_timer = 0
        self.countdown_active = True
        self.countdown_texts = ["3", "2", "1", "FIGHT"]
        self.countdown_duration = 15   # 0.25s per tick (was 45 = 0.75s)
        self.fight_duration = 15       # 0.25s for FIGHT text (was 30 = 0.5s)
        
        # Opening chaos event pool (high-impact visual openers)
        self.OPENING_CHAOS_POOL = [
            "HYPER SPEED",
            "BLACKOUT",
            "ULTRA KNOCKBACK",
            "DISCO FEVER",
            "THE CRUSHER"
        ]
        
        # Delay before first chaos event (1 second = 60 frames at 60 FPS)
        self.opening_chaos_delay = 0  # 0 = not pending
        
        # Arena Escalation System
        self.inactivity_timer = 0
        
        # Game State
        self.game_state = 'TITLE'
        self.obs_startup_timer = 0
        
        # Seamless Loop Wipe System
        # Phases: 0=none, 1=flash_in (opacity rising), 2=solid (reset behind),
        #         3=flash_out (opacity falling, reveals new state)
        self.loop_wipe_phase = 0
        self.loop_wipe_timer = 0
        self.WIPE_FLASH_IN_FRAMES = 6
        self.WIPE_SOLID_FRAMES = 3
        self.WIPE_FLASH_OUT_FRAMES = 6
        self.loop_wipe_done = False  # True after end-of-match wipe completes (for single-run exit)
        self.loop_wipe_is_closing = False  # Only True when wipe is triggered by end-of-match
        
        # Load Arena Watermark Logo
        import os
        logo_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), "assets", "images", "logo-dark-grey-text.png")
        try:
            logo_img = pygame.image.load(logo_path).convert_alpha()
            # Scale down to be a watermark (max ~400px wide)
            scale_factor = 400.0 / max(logo_img.get_width(), 1)
            new_size = (int(logo_img.get_width() * scale_factor), int(logo_img.get_height() * scale_factor))
            self.bg_logo = pygame.transform.scale(logo_img, new_size)
            self.bg_logo.set_alpha(80) # Semi-transparent watermark
        except Exception as e:
            print(f"Failed to load background logo: {e}")
            self.bg_logo = None
        
        # OBS Integration
        self.obs_client = None
        self.is_recording = False
        self._init_obs_client()
        
        # Load sounds.
        self._setup_sounds()
        
    def _init_obs_client(self):
        """Initialize connection to OBS WebSocket server."""
        if obs is None:
            print("[OBS] obsws-python library not found. Auto-recording disabled.")
            return
            
        try:
            port = int(os.getenv("OBS_PORT", "4455"))
            password = os.getenv("OBS_PASSWORD", "")
            
            if not password:
                print("[OBS] No OBS_PASSWORD found in .env. Auto-recording disabled.")
                return
                
            self.obs_client = obs.ReqClient(host='localhost', port=port, password=password)
            print("[OBS] Successfully hooked into OBS Studio!")
        except Exception as e:
            print(f"[OBS] Failed to connect: {e} (Is OBS open?)")
            self.obs_client = None
            
    def _start_obs_recording(self):
        """Start OBS recording if connected."""
        if self.obs_client and not self.is_recording:
            try:
                self.obs_client.start_record()
                self.is_recording = True
                print("[OBS] 🎥 Camera Rolling! Recording Started.")
            except Exception as e:
                print(f"[OBS] Start recording failed: {e}")
                
    def _stop_obs_recording(self):
        """Stop OBS recording if connected."""
        if self.obs_client and self.is_recording:
            try:
                self.obs_client.stop_record()
                self.is_recording = False
                print("[OBS] ⏹️ CUT! Recording Saved.")
            except Exception as e:
                print(f"[OBS] Stop recording failed: {e}")
    
    def _lock_fighters_for_countdown(self):
        """Lock fighters in place for countdown."""
        self.blue.locked = True
        self.red.locked = True
        self.blue.vx = 0
        self.blue.vy = 0
        self.red.vx = 0
        self.red.vy = 0
        self.blue.sword_angle = 0
        self.red.sword_angle = math.pi
    
    def _unlock_fighters(self):
        """Unlock fighters with random velocity."""
        self.blue.locked = False
        self.red.locked = False
        self.blue.vx = random.uniform(-6, 6)
        self.blue.vy = random.uniform(-6, 6)
        self.red.vx = random.uniform(-6, 6)
        self.red.vy = random.uniform(-6, 6)
    
    def _trigger_opening_chaos(self):
        """Immediately trigger a random high-impact chaos event at match start."""
        # TEMPORARILY DISABLED for slash testing
        # opener = random.choice(self.OPENING_CHAOS_POOL)
        # self.chaos.trigger_specific_event(opener)
        # self._play_chaos_event_sound(opener)
        pass
    
    def _reset_inactivity(self):
        """Reset inactivity timer."""
        self.inactivity_timer = 0
    
    def _trigger_arena_pulse(self):
        """Trigger Arena Pulse."""
        self.arena_pulses.add(tuple(self.arena_bounds), PURPLE)
        self.screen_shake = ARENA_PULSE_SHAKE
        
        # Play arena pulse sound
        if self.sounds_enabled and self.arena_pulse_sound:
            self.arena_pulse_sound.play()
        
        center_x = SCREEN_WIDTH // 2
        center_y = SCREEN_HEIGHT // 2
        
        for fighter in [self.blue, self.red]:
            dx = center_x - fighter.x
            dy = center_y - fighter.y
            dist = max(1, math.hypot(dx, dy))
            fighter.vx += (dx / dist) * ARENA_PULSE_VELOCITY_BOOST
            fighter.vy += (dy / dist) * ARENA_PULSE_VELOCITY_BOOST
            speed = math.hypot(fighter.vx, fighter.vy)
            if speed > 0:
                fighter.vx *= 1.2
                fighter.vy *= 1.2

    def _setup_sounds(self):
        """Load all sound effects from audio files."""
        import os
        try:
            base_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), "assets", "audio")
            
            # Helper function to load a sound file
            def load_sound(subfolder, filename, volume=0.5):
                path = os.path.join(base_path, subfolder, filename)
                if os.path.exists(path):
                    sound = pygame.mixer.Sound(path)
                    sound.set_volume(volume)
                    return sound
                return None
            
            # === COMBAT SOUNDS ===
            self.hit_sounds = [
                load_sound("combat", "hit_1.mp3", 0.5),
                load_sound("combat", "hit_2.mp3", 0.5)
            ]
            self.hit_sound_index = 0  # Alternate between hit sounds
            self.critical_hit_sound = load_sound("combat", "critical_hit.mp3", 0.6)
            self.knockback_whoosh_sound = load_sound("combat", "knockback_whoosh.mp3", 0.5)
            self.sword_clash_sound = load_sound("combat", "sword_clash.mp3", 0.5)
            self.death_final_hit_sound = load_sound("combat", "death_final_hit.mp3", 0.7)
            self.sword_to_ground_sound = load_sound("combat", "sword_to_the_ground.mp3", 0.6)
            
            # === COUNTDOWN SOUNDS ===
            self.countdown_beep_sound = load_sound("countdown", "countdown_beep.mp3", 0.6)
            self.sword_fight_sound = load_sound("countdown", "sword-fight.mp3", 0.5)
            
            # === CHAOS EVENT SOUNDS (one-shots on event start) ===
            self.chaos_sounds = {
                "HYPER SPEED": load_sound("chaos_event", "hyper_speed.mp3", 0.5),
                "TINY TERROR": load_sound("chaos_event", "chaos_trigger.mp3", 0.5),  # Use generic trigger
                "DISCO FEVER": load_sound("chaos_event", "disco_fever.mp3", 0.5),
                "THE CRUSHER": load_sound("chaos_event", "the_crusher.mp3", 0.5),
                "BLACKOUT": load_sound("chaos_event", "blackout_start.mp3", 0.5),
                "TRON MODE": load_sound("chaos_event", "tron_mode.mp3", 0.5),
                "GLITCH TRAP": load_sound("chaos_event", "glitch_trap.mp3", 0.5),
                "BREATHING ROOM": load_sound("chaos_event", "breathing_room.mp3", 0.5),
                "MOVING WALLS": load_sound("chaos_event", "moving_walls.mp3", 0.5),
                "ULTRA KNOCKBACK": load_sound("chaos_event", "ultra_knockback.mp3", 0.5),
            }
            self.chaos_trigger_sound = load_sound("chaos_event", "chaos_trigger.mp3", 0.6)
            
            # === CONTINUOUS/LOOP SOUNDS ===
            self.arena_shrink_warning_sound = load_sound("continuous", "arena_shrink_warning.mp3", 0.4)
            self.disco_beat_sound = load_sound("continuous", "disco_beat.mp3", 0.4)
            self.tron_trail_hum_sound = load_sound("continuous", "tron_trail_hum.mp3", 0.3)
            
            # === FEEDBACK SOUNDS ===
            self.arena_pulse_sound = load_sound("feedback", "arena_pulse.mp3", 0.5)
            self.damage_tick_sound = load_sound("feedback", "damage_tick.mp3", 0.4)
            self.healing_life_steal_sound = load_sound("feedback", "healing_life_steal.mp3", 0.4)
            self.wall_boost_sound = load_sound("feedback", "wall_boost.mp3", 0.3)
            self.wall_bounce_sound = load_sound("feedback", "wall_bounce.mp3", 0.25)
            
            # Track currently playing looping sounds for chaos events
            self.active_loop_channel = None  # Channel for looping chaos sounds
            self.active_chaos_event_sound = None  # Currently playing event name
            self.escalation_loop_channel = None  # Channel for arena shrink warning
            
            # Track countdown sound state
            self.countdown_beep_played = [False, False, False]  # For 3, 2, 1
            self.fight_sound_played = False
            
            # Track death sequence sound state
            self.death_sound_phase = 0  # 0=none, 1=final_hit_played, 2=sword_to_ground_played
            
            self.sounds_enabled = True
        except Exception as e:
            print(f"Sound loading error: {e}")
            self.sounds_enabled = False
    
    def _play_hit_sound(self, is_crit=False):
        """Play appropriate hit sound."""
        if not self.sounds_enabled:
            return
        if is_crit and self.critical_hit_sound:
            self.critical_hit_sound.play()
        elif self.hit_sounds[0] and self.hit_sounds[1]:
            self.hit_sounds[self.hit_sound_index].play()
            self.hit_sound_index = (self.hit_sound_index + 1) % 2
    
    def _play_chaos_event_sound(self, event_name):
        """Play chaos event sound and start loops if needed."""
        if not self.sounds_enabled:
            return
        
        # Stop any currently playing chaos loops
        self._stop_chaos_loops()
        
        # Play the trigger sound
        if self.chaos_trigger_sound:
            self.chaos_trigger_sound.play()
        
        # Play event-specific sound
        if event_name in self.chaos_sounds and self.chaos_sounds[event_name]:
            self.chaos_sounds[event_name].play()
        
        # Start continuous loops for specific events
        if event_name == "DISCO FEVER" and self.disco_beat_sound:
            self.active_loop_channel = self.disco_beat_sound.play(loops=-1)
            self.active_chaos_event_sound = event_name
        elif event_name == "TRON MODE" and self.tron_trail_hum_sound:
            self.active_loop_channel = self.tron_trail_hum_sound.play(loops=-1)
            self.active_chaos_event_sound = event_name
    
    def _stop_chaos_loops(self):
        """Stop any chaos-related looping sounds."""
        if self.active_loop_channel:
            self.active_loop_channel.stop()
            self.active_loop_channel = None
        self.active_chaos_event_sound = None
    
    def _start_escalation_sound(self):
        """Start the escalation shrink warning loop."""
        if not self.sounds_enabled or not self.arena_shrink_warning_sound:
            return
        if self.escalation_loop_channel is None:
            self.escalation_loop_channel = self.arena_shrink_warning_sound.play(loops=-1)
    
    def _stop_escalation_sound(self):
        """Stop the escalation shrink warning loop."""
        if self.escalation_loop_channel:
            self.escalation_loop_channel.stop()
            self.escalation_loop_channel = None

    # Skills disabled - _spawn_skill_orb removed

    def _check_sword_hit(self, attacker, defender):
        """Check if sword tip hits defender body (always active in Beyblade mode)."""
        
        # Early-out: skip if defender is too far for any sword point to reach
        fighter_dist = math.hypot(attacker.x - defender.x, attacker.y - defender.y)
        scaled_sword_length = attacker.sword_length * attacker.sword_size_multiplier
        max_reach = attacker.current_radius + 3 + scaled_sword_length + defender.current_radius + 3
        if fighter_dist > max_reach:
            return None
        
        (base_x, base_y), (tip_x, tip_y) = attacker.get_sword_hitbox()
        
        # Check outer portion of blade only (skip midpoint to avoid body-overlap phantom hits)
        for t in [0.75, 1.0]:
            check_x = base_x + (tip_x - base_x) * t
            check_y = base_y + (tip_y - base_y) * t
            dist = math.hypot(check_x - defender.x, check_y - defender.y)
            # Tighter tolerance: current_radius + 3 (was +8)
            if dist < defender.current_radius + 3:
                return (check_x, check_y)
        return None

    @staticmethod
    def _cross(o, a, b):
        """2D cross product of vectors OA and OB."""
        return (a[0] - o[0]) * (b[1] - o[1]) - (a[1] - o[1]) * (b[0] - o[0])
    
    def _segments_intersect(self, p1, p2, p3, p4):
        """Check if line segment p1-p2 intersects p3-p4 using cross products."""
        d1 = self._cross(p3, p4, p1)
        d2 = self._cross(p3, p4, p2)
        d3 = self._cross(p1, p2, p3)
        d4 = self._cross(p1, p2, p4)
        
        if ((d1 > 0 and d2 < 0) or (d1 < 0 and d2 > 0)) and \
           ((d3 > 0 and d4 < 0) or (d3 < 0 and d4 > 0)):
            return True
        
        return False
    
    def _get_intersection_point(self, p1, p2, p3, p4):
        """Get the intersection point of segments p1-p2 and p3-p4."""
        x1, y1 = p1
        x2, y2 = p2
        x3, y3 = p3
        x4, y4 = p4
        
        denom = (x1 - x2) * (y3 - y4) - (y1 - y2) * (x3 - x4)
        if abs(denom) < 1e-10:
            return None
        
        t = ((x1 - x3) * (y3 - y4) - (y1 - y3) * (x3 - x4)) / denom
        
        ix = x1 + t * (x2 - x1)
        iy = y1 + t * (y2 - y1)
        return (ix, iy)

    def _handle_combat(self):
        """Detect and resolve combat interactions with sword-to-sword parry."""
        
        # === PARRY CHECK: Sword-to-Sword intersection ===
        blue_base, blue_tip = self.blue.get_sword_hitbox()
        red_base, red_tip = self.red.get_sword_hitbox()
        
        if self._segments_intersect(blue_base, blue_tip, red_base, red_tip):
            if self.blue.parry_cooldown <= 0 and self.red.parry_cooldown <= 0:
                # Reverse both spin directions
                self.blue.spin_direction *= -1
                self.red.spin_direction *= -1
                
                # Set parry cooldown
                self.blue.parry_cooldown = 15
                self.red.parry_cooldown = 15
                
                # Hit-stop and screen shake
                self.hit_stop = 8
                self.screen_shake = 12
                
                # Sparks at intersection point
                ix_point = self._get_intersection_point(blue_base, blue_tip, red_base, red_tip)
                if ix_point:
                    self.particles.emit(ix_point[0], ix_point[1], (255, 255, 200), count=20, size=4)
                
                # Play sword clash sound
                if self.sounds_enabled and self.sword_clash_sound:
                    self.sword_clash_sound.play()
        
        # === BODY HIT CHECK: Sword vs body (always active - Beyblade mode) ===
        for attacker, defender in [(self.blue, self.red), (self.red, self.blue)]:
            hit_pos = self._check_sword_hit(attacker, defender)
            if hit_pos:
                
                # Roll for critical hit (20% chance)
                is_crit = random.random() < CRIT_CHANCE
                crit_mult = CRIT_MULTIPLIER if is_crit else 1.0
                
                # Apply combo damage multiplier + chaos damage multiplier + crit
                damage_mult = attacker.get_attack_damage_multiplier()
                chaos_damage_mult = self.chaos.get_damage_mult()
                knockback_mult = self.chaos.get_knockback_mult() * crit_mult
                total_damage_mult = damage_mult * chaos_damage_mult * crit_mult
                
                angle = math.atan2(defender.y - attacker.y, defender.x - attacker.x)
                knockback = BASE_KNOCKBACK * knockback_mult * (1.0 + (total_damage_mult - 1.0) * 0.5) * 1.5
                damage = DAMAGE_PER_HIT * total_damage_mult
                
                # ULTRA KNOCKBACK: Massive screen shake + knockback whoosh
                if self.chaos.is_ultra_knockback():
                    self.screen_shake = max(self.screen_shake, SCREEN_SHAKE_INTENSITY * 3)
                    if self.sounds_enabled and self.knockback_whoosh_sound:
                        self.knockback_whoosh_sound.play()
                
                # Fixed hit-stop frames (no combo system)
                hit_stop_frames = HIT_STOP_FRAMES
                
                if defender.take_damage(damage, angle, knockback, self.particles):
                    self._trigger_hit(hit_pos[0], hit_pos[1], attacker.render_color, hit_stop_frames, damage, is_crit)
                    self.hit_slowmo_frames = HIT_SLOWMO_FRAMES
                    self._reset_inactivity()
                    
                    # Critical Hit: Trigger anime impact sequence
                    if is_crit:
                        self.crit_impact_frames = CRIT_IMPACT_FRAMES
                        self.crit_impact_accumulator = 0.0
                        self.crit_flash_phase = 1  # Start flash sequence
                        self.screen_shake = max(self.screen_shake, SCREEN_SHAKE_INTENSITY * 2)
                    
                    # DISCO FEVER: 100% Life Steal (vampirism)
                    life_steal = self.chaos.get_life_steal()
                    if life_steal > 0:
                        heal_amount = damage * life_steal
                        attacker.health = min(attacker.max_health, attacker.health + heal_amount)
                        # Visual feedback for healing
                        self.particles.emit(attacker.x, attacker.y, (100, 255, 100), count=6, size=3)
                        # Play life steal sound
                        if self.sounds_enabled and self.healing_life_steal_sound:
                            self.healing_life_steal_sound.play()

    def _trigger_hit(self, x, y, color, hit_stop_frames=None, damage=0, is_crit=False):
        """Apply hit effects including damage numbers."""
        self.particles.emit(x, y, WHITE, count=10 if not is_crit else 20, size=4 if not is_crit else 6)
        self.hit_stop = hit_stop_frames if hit_stop_frames else HIT_STOP_FRAMES
        self.screen_shake = SCREEN_SHAKE_INTENSITY
        
        # Spawn floating damage number (gold + larger for crits)
        if damage > 0:
            self.damage_numbers.spawn(x, y - 20, damage, color, is_crit)
        
        # Play hit sound (alternating hit_1/hit_2, or critical_hit for crits)
        self._play_hit_sound(is_crit)

    def _end_round(self, winner, loser):
        """Handle round end."""
        self.round_ending = True
        self.winner = winner
        # Extended from 120 to 300 to allow delay before displaying win text
        self.reset_timer = 60  # 1 second end sequence (60 frames at 60fps)
        
        if winner == self.blue:
            self.winner_text = "WINS"
        else:
            self.winner_text = "WINS"
        
        # Color state reversion and death animation rules
        if self.chaos.is_blackout():
            # Blackout Exception: Allow animation to run under blackout visual rules
            # Do NOT reset chaos, use either flashing white or current blackout color for chunks
            death_color = WHITE if loser.flash_timer > 0 else loser.render_color
        else:
            # Forcefully revert color state from critical hit white back to base default
            loser.flash_timer = 0
            death_color = loser.color
            
            # Reset chaos back to normal lighting/colors for physics death sequence
            self.chaos.reset_chaos()
            
            # Ensure render colors revert from any modified values back to defaults
            winner.render_color = winner.color
            winner.render_color_bright = winner.color_bright
            loser.render_color = loser.color
            loser.render_color_bright = loser.color_bright
            
        self.particles.emit_explosion(loser.x, loser.y, death_color, count=40)
        self.shockwaves.add(loser.x, loser.y, death_color, 100)
        winner.victory_bounce = 40
        
        self.slow_motion = True
        self.slow_motion_accumulator = 0.0
        
        # Death sound sequence: death_final_hit first, sword_to_ground after freeze
        self.death_sound_phase = 1
        if self.sounds_enabled and self.death_final_hit_sound:
            self.death_final_hit_sound.play()
        
        # Stop any chaos sounds
        self._stop_chaos_loops()
        self._stop_escalation_sound()

    def _reset_round(self):
        """Reset round."""
        self.blue.reset()
        self.red.reset()
        self.arena_bounds = list(self.base_arena)
        self.round_ending = False
        self.winner = None
        self.winner_text = ""
        self.round_timer = 0
        self.particles.clear()
        self.shockwaves.clear()
        self.arena_pulses.clear()
        self.damage_numbers.clear()
        
        # Reset chaos system and stop all chaos sounds
        self.chaos.reset_chaos()
        self._stop_chaos_loops()
        self._stop_escalation_sound()
        
        self.hit_slowmo_frames = 0
        self.hit_slowmo_accumulator = 0.0
        
        # Reset critical hit impact state
        self.crit_impact_frames = 0
        self.crit_impact_accumulator = 0.0
        self.crit_flash_phase = 0
        
        self.inactivity_timer = 0
        
        self._lock_fighters_for_countdown()
        self.countdown_stage = 0
        self.countdown_timer = 0
        self.countdown_active = True
        
        # Reset countdown and death sound state
        self.countdown_beep_played = [False, False, False]
        self.fight_sound_played = False
        self.death_sound_phase = 0
        self.opening_chaos_delay = 0
        
        # Delay for OBS startup between rounds
        self.obs_startup_timer = 60

    def update(self):
        """Main update loop."""
        if self.paused:
            return
        
        # Wait for OBS startup to finish before starting countdown
        if getattr(self, 'obs_startup_timer', 0) > 0:
            self.obs_startup_timer -= 1
            return
        
        if self.countdown_active:
            self.countdown_timer += 1
            duration = self.fight_duration if self.countdown_stage == 3 else self.countdown_duration
            
            # Play countdown beep sounds for stages 0, 1, 2 ("3", "2", "1")
            if self.countdown_stage < 3 and self.countdown_timer == 1:
                if not self.countdown_beep_played[self.countdown_stage]:
                    self.countdown_beep_played[self.countdown_stage] = True
                    if self.sounds_enabled and self.countdown_beep_sound:
                        self.countdown_beep_sound.play()
            
            # Play sword-fight sound when "FIGHT" appears
            if self.countdown_stage == 3 and self.countdown_timer == 1:
                if not self.fight_sound_played:
                    self.fight_sound_played = True
                    if self.sounds_enabled and self.sword_fight_sound:
                        self.sword_fight_sound.play()
            
            if self.countdown_timer >= duration:
                self.countdown_timer = 0
                self.countdown_stage += 1
                if self.countdown_stage > 3:
                    self.countdown_active = False
                    self._unlock_fighters()
                    self.opening_chaos_delay = FPS  # 1-second delay before first chaos event
            return
        
        if self.slow_motion and not self.round_ending:
            self.slow_motion = False
        
        if self.slow_motion:
            self.slow_motion_accumulator += SLOW_MOTION_SPEED
            if self.slow_motion_accumulator < 1.0:
                return
            self.slow_motion_accumulator -= 1.0
        
        if self.hit_stop > 0:
            self.hit_stop -= 1
            return
        
        if self.hit_slowmo_frames > 0:
            self.hit_slowmo_accumulator += HIT_SLOWMO_TIMESCALE
            self.hit_slowmo_frames -= 1
            if self.hit_slowmo_accumulator < 1.0:
                return
            self.hit_slowmo_accumulator -= 1.0
        
        # Critical Hit Impact Freeze (anime slowdown at 0.05x speed)
        if self.crit_impact_frames > 0:
            self.crit_impact_accumulator += CRIT_IMPACT_TIMESCALE
            self.crit_impact_frames -= 1
            # Advance flash phase during impact
            if self.crit_flash_phase == 1 and self.crit_impact_frames < CRIT_IMPACT_FRAMES - 3:
                self.crit_flash_phase = 2  # Black -> White
            elif self.crit_flash_phase == 2 and self.crit_impact_frames < CRIT_IMPACT_FRAMES - 6:
                self.crit_flash_phase = 3  # White -> Normal
            if self.crit_impact_accumulator < 1.0:
                return
            self.crit_impact_accumulator -= 1.0
        
        if self.screen_shake > 0:
            self.screen_shake *= SCREEN_SHAKE_DECAY
            if self.screen_shake < 0.5:
                self.screen_shake = 0
        

        
        if self.round_ending:
            self.reset_timer -= 1
            
            # Play sword_to_ground sound partway through the freeze (40 frames in)
            if self.death_sound_phase == 1 and self.reset_timer < 50:
                self.death_sound_phase = 2
                if self.sounds_enabled and self.sword_to_ground_sound:
                    self.sword_to_ground_sound.play()
            
            if self.reset_timer <= 0:
                # Game over — quit after the winner message
                pygame.event.post(pygame.event.Event(pygame.QUIT))
                return
            self.particles.update()
            self.shockwaves.update()
            self.arena_pulses.update()
            return
        
        self.round_timer += 1
        
        # Opening chaos event delay timer
        if self.opening_chaos_delay > 0:
            self.opening_chaos_delay -= 1
            if self.opening_chaos_delay <= 0:
                self._trigger_opening_chaos()
        
        # Arena Escalation (Repeating Pulse)
        self.inactivity_timer += 1
        if self.inactivity_timer >= INACTIVITY_PULSE_TIME * FPS:
            self._trigger_arena_pulse()
            self.inactivity_timer = 0  # Reset so it pulses again in 2 seconds if still inactive
        
        # ===== CHAOS SYSTEM UPDATE (TEMPORARILY DISABLED for slash testing) =====
        dt = 1.0 / FPS
        # prev_event = self.chaos.active_event  # Track for sound trigger
        # self.chaos.update(dt, self.particles, [self.blue, self.red])
        
        # # Trigger chaos event sound when new event starts
        # current_event = self.chaos.active_event
        # if current_event and current_event != prev_event:
        #     self._play_chaos_event_sound(current_event)
        # elif prev_event and not current_event:
        #     # Event ended, stop any loops
        #     self._stop_chaos_loops()
        
        # Ensure fighters use default colors and sizes (no chaos modifiers)
        for fighter in [self.blue, self.red]:
            fighter.body_size_multiplier = 1.0
            fighter.sword_size_multiplier = 1.0
            fighter.attack_speed_multiplier = 1.0
            fighter.speed_multiplier = 1.0
            fighter.render_color = fighter.color
            fighter.render_color_bright = fighter.color_bright
            fighter.health_bar_color = fighter.color
        
        # Calculate arena bounds with Crusher/Breathing Room modifier
        arena_mult = self.chaos.get_arena_mult()
        if arena_mult != 1.0:
            # Apply arena scaling (shrink for Crusher, pulse for Breathing Room)
            if arena_mult < 1.0:
                shrink = (1.0 - arena_mult) * min(self.arena_bounds[2], self.arena_bounds[3]) / 2
            else:
                # Expand for Breathing Room
                shrink = -(arena_mult - 1.0) * min(self.arena_bounds[2], self.arena_bounds[3]) / 2
            
            effective_arena = (
                max(10, self.arena_bounds[0] + shrink),
                max(10, self.arena_bounds[1] + shrink),
                max(200, min(SCREEN_WIDTH - 20, self.arena_bounds[2] - shrink * 2)),
                max(200, min(SCREEN_HEIGHT - 20, self.arena_bounds[3] - shrink * 2))
            )
            
            # Safety push - push fighters inside if outside bounds
            if self.chaos.needs_crusher_safety_push():
                for fighter in [self.blue, self.red]:
                    ax, ay, aw, ah = effective_arena
                    margin = fighter.current_radius + 5
                    fighter.x = max(ax + margin, min(ax + aw - margin, fighter.x))
                    fighter.y = max(ay + margin, min(ay + ah - margin, fighter.y))
        else:
            effective_arena = tuple(self.arena_bounds)
        
        # Update fighters with effective arena
        self.blue.update(self.red, effective_arena, self.particles, self.shockwaves)
        self.red.update(self.blue, effective_arena, self.particles, self.shockwaves)
        
        # Body-to-body collision separation (prevent overlap that causes phantom sword hits)
        dx = self.red.x - self.blue.x
        dy = self.red.y - self.blue.y
        body_dist = math.hypot(dx, dy)
        min_sep = self.blue.current_radius + self.red.current_radius
        if body_dist < min_sep and body_dist > 0:
            overlap = (min_sep - body_dist) / 2.0
            nx = dx / body_dist
            ny = dy / body_dist
            self.blue.x -= nx * overlap
            self.blue.y -= ny * overlap
            self.red.x += nx * overlap
            self.red.y += ny * overlap
        
        # ===== CHAOS EVENT HANDLERS =====
        
        # TRON MODE: Check trail collisions
        if self.chaos.is_tron_mode():
            self._handle_tron_mode(effective_arena)
        
        # GLITCH TRAP: Random teleports
        if self.chaos.is_glitch_trap():
            self._handle_glitch_trap(effective_arena)
        
        # MOVING WALLS: Push fighters
        if self.chaos.is_moving_walls():
            self._handle_moving_walls(effective_arena)
        
        self._handle_combat()
        
        self.particles.update()
        self.shockwaves.update()
        self.arena_pulses.update()
        self.damage_numbers.update()
        
        if self.blue.health <= 0:
            self._end_round(winner=self.red, loser=self.blue)
        elif self.red.health <= 0:
            self._end_round(winner=self.blue, loser=self.red)
    def _handle_tron_mode(self, arena_bounds):
        """Handle TRON MODE: Opponent's trail deals damage (1 per second)."""
        dt = 1.0 / FPS
        for fighter, other in [(self.blue, self.red), (self.red, self.blue)]:
            damage = self.chaos.check_tron_collision(fighter, other, dt)
            if damage > 0 and fighter.invincible <= 0:
                angle = math.atan2(fighter.y - other.y, fighter.x - other.x)
                if fighter.take_damage(damage, angle, BASE_KNOCKBACK * 2, self.particles):
                    self._trigger_hit(fighter.x, fighter.y, other.render_color, 3, damage)
                    # Play damage tick sound for TRON trail damage
                    if self.sounds_enabled and self.damage_tick_sound:
                        self.damage_tick_sound.play()
    
    def _handle_glitch_trap(self, arena_bounds):
        """Handle GLITCH TRAP: Random teleports with safe bounds."""
        if self.chaos.should_glitch_teleport():
            ax, ay, aw, ah = arena_bounds
            
            for fighter in [self.blue, self.red]:
                dx, dy = self.chaos.get_glitch_teleport_offset()
                new_x = fighter.x + dx
                new_y = fighter.y + dy
                
                # Safe teleport: clamp to arena bounds
                margin = fighter.current_radius + 5
                new_x = max(ax + margin, min(ax + aw - margin, new_x))
                new_y = max(ay + margin, min(ay + ah - margin, new_y))
                
                fighter.x = new_x
                fighter.y = new_y
                
                # Visual glitch effect
                self.particles.emit(fighter.x, fighter.y, (255, 0, 255), count=8, size=4)
    
    def _handle_moving_walls(self, arena_bounds):
        """Handle MOVING WALLS: Push fighters in wall's movement direction."""
        for fighter in [self.blue, self.red]:
            was_pushed = self.chaos.handle_moving_wall_collision(fighter, arena_bounds)
            # Play moving walls sound only when fighter is pushed
            if was_pushed and self.sounds_enabled and self.wall_bounce_sound:
                self.wall_bounce_sound.play()

    def _draw_title_screen(self):
        """Draw title screen."""
        self.screen.fill(DARK_GRAY)
        
        ax, ay, aw, ah = self.base_arena
        arena_rect = pygame.Rect(int(ax), int(ay), int(aw), int(ah))
        pygame.draw.rect(self.screen, BLACK, arena_rect)
        pygame.draw.rect(self.screen, GRAY, arena_rect, 4)
        
        title_text = "RED vs BLUE"
        title_surface = self.font_large.render(title_text, True, WHITE)
        title_rect = title_surface.get_rect(center=(SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2 - 80))
        
        shadow_surface = self.font_large.render(title_text, True, (50, 50, 50))
        shadow_rect = shadow_surface.get_rect(center=(SCREEN_WIDTH // 2 + 3, SCREEN_HEIGHT // 2 - 77))
        self.screen.blit(shadow_surface, shadow_rect)
        self.screen.blit(title_surface, title_rect)
        
        subtitle = "BATTLE"
        subtitle_surface = self.font_medium.render(subtitle, True, YELLOW)
        subtitle_rect = subtitle_surface.get_rect(center=(SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2 - 10))
        self.screen.blit(subtitle_surface, subtitle_rect)
        
        if (pygame.time.get_ticks() // 500) % 2 == 0:
            prompt = "Press SPACE or CLICK to Start"
            prompt_surface = self.font_small.render(prompt, True, WHITE)
            prompt_rect = prompt_surface.get_rect(center=(SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2 + 80))
            self.screen.blit(prompt_surface, prompt_rect)
        
        controls = "SPACE: Pause  |  R: Reset  |  ESC: Exit"
        controls_surface = self.font_small.render(controls, True, GRAY)
        controls_rect = controls_surface.get_rect(center=(SCREEN_WIDTH // 2, SCREEN_HEIGHT - 40))
        self.screen.blit(controls_surface, controls_rect)
        # Draw game surface to high-res canvas
        self.canvas.fill((15, 15, 15))  # Dark background for dead space
        y_offset = (CANVAS_HEIGHT - SCREEN_HEIGHT) // 2
        self.canvas.blit(self.screen, (0, y_offset))
        
        # Scale down and present to the laptop display window
        scaled_preview = pygame.transform.smoothscale(self.canvas, (DISPLAY_WIDTH, DISPLAY_HEIGHT))
        self.window.blit(scaled_preview, (0, 0))
        
        pygame.display.flip()

    def draw(self):
        """Draw game with neon visuals and chaos effects."""
        offset = (0, 0)
        if self.screen_shake > 0:
            offset = (random.uniform(-self.screen_shake, self.screen_shake),
                     random.uniform(-self.screen_shake, self.screen_shake))
        
        # Use chaos background color (NEON_BG normally, WHITE for Blackout)
        bg_color = self.chaos.get_bg_color()
        self.screen.fill(bg_color)
        
        # Draw grid (unless Blackout)
        if not self.chaos.is_blackout():
            self._draw_grid(offset)
        
        # Calculate effective arena for Crusher/Breathing Room
        arena_mult = self.chaos.get_arena_mult()
        if arena_mult != 1.0:
            if arena_mult < 1.0:
                shrink = (1.0 - arena_mult) * min(self.arena_bounds[2], self.arena_bounds[3]) / 2
            else:
                shrink = -(arena_mult - 1.0) * min(self.arena_bounds[2], self.arena_bounds[3]) / 2
            draw_arena = (
                max(10, self.arena_bounds[0] + shrink),
                max(10, self.arena_bounds[1] + shrink),
                max(200, min(SCREEN_WIDTH - 20, self.arena_bounds[2] - shrink * 2)),
                max(200, min(SCREEN_HEIGHT - 20, self.arena_bounds[3] - shrink * 2))
            )
        else:
            draw_arena = self.arena_bounds
        
        ax, ay, aw, ah = draw_arena
        arena_rect = pygame.Rect(int(ax + offset[0]), int(ay + offset[1]), int(aw), int(ah))
        
        # Arena fill color (dark, Blackout inverted, Tron very dark)
        if self.chaos.is_blackout():
            arena_fill = WHITE
        elif self.chaos.is_tron_mode():
            arena_fill = (5, 5, 10)
        else:
            arena_fill = BLACK
        pygame.draw.rect(self.screen, arena_fill, arena_rect)
        
        # Draw background logo watermark
        if hasattr(self, 'bg_logo') and self.bg_logo:
            # Center logo in current drawn arena
            logo_rect = self.bg_logo.get_rect(center=(int(ax + aw/2 + offset[0]), int(ay + ah/2 + offset[1])))
            self.screen.blit(self.bg_logo, logo_rect)
        
        # Base swap logic for border color (180 frames = 3 seconds at 60fps)
        base_border_color = self.f1_color if (self.round_timer // 180) % 2 == 0 else self.f2_color
        
        # Arena border
        if self.chaos.active_event in ["THE CRUSHER", "BREATHING ROOM"]:
            border_color = self.f2_color if not self.chaos.is_blackout() else BLACK
            border_width = 6
        elif self.chaos.is_tron_mode():
            border_color = base_border_color
            border_width = 6
        else:
            border_color = base_border_color if not self.chaos.is_blackout() else GRAY
            border_width = 4
        pygame.draw.rect(self.screen, border_color, arena_rect, border_width)
        
        # Draw TRON trails (solid neon walls)
        if self.chaos.is_tron_mode():
            self._draw_tron_trails(offset)
        
        # Draw GLITCH rectangles
        if self.chaos.is_glitch_trap():
            self._draw_glitch_rects()
        
        # Draw MOVING WALL
        if self.chaos.is_moving_walls():
            self._draw_moving_wall(offset, draw_arena)
        
        self.arena_pulses.draw(self.screen, offset)
        self.shockwaves.draw(self.screen, offset)
        
        # Draw fighters
        if not self.round_ending or self.winner == self.blue:
            self.blue.draw(self.screen, offset)
        if not self.round_ending or self.winner == self.red:
            self.red.draw(self.screen, offset)
        
        self.particles.draw(self.screen, offset)
        self.damage_numbers.draw(self.screen, offset)
        
        # Critical Hit Impact Flash (drawn AFTER fighters, BEFORE UI)
        if self.crit_flash_phase == 1:
            # Phase 1: Full screen BLACK flash
            self.screen.fill(BLACK)
        elif self.crit_flash_phase == 2:
            # Phase 2: Full screen WHITE flash
            self.screen.fill(WHITE)
        # Phase 3+: Normal render (no flash)
        
        # Draw chaos event banner (always visible, black text during Blackout)
        if self.chaos.active_event:
            self.chaos_text.draw_chaos_banner(self.screen, self.chaos)
        
        # Countdown overlay
        if self.countdown_active:
            countdown_text = self.countdown_texts[self.countdown_stage]
            
            if countdown_text == "FIGHT":
                text_surface = self.font_medium.render(countdown_text, True, WHITE)
                border_color = self.f1_color
            else:
                text_surface = self.font_large.render(countdown_text, True, WHITE)
                border_color = self.f2_color
            
            text_rect = text_surface.get_rect(center=(SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2))
            
            bg_rect = text_rect.inflate(50, 30)
            pygame.draw.rect(self.screen, NEON_BG, bg_rect)
            pygame.draw.rect(self.screen, border_color, bg_rect, 4)
            
            self.screen.blit(text_surface, text_rect)
        
        # Winner UI Announcement
        # Show winner text almost immediately after death (0.17s delay)
        if self.round_ending and self.winner_text and self.reset_timer < 50:
            text_surface = self.font_large.render(self.winner_text, True, WHITE)
            
            # Winner color info
            win_color = self.f1_color if self.winner == self.blue else self.f2_color
            win_color_bright = self.f1_bright if self.winner == self.blue else self.f2_bright
            border_color = win_color
            
            # Layout calculation
            circle_radius = 25
            gap = 15
            total_width = (circle_radius * 2) + gap + text_surface.get_width()
            
            cx = SCREEN_WIDTH // 2
            cy = SCREEN_HEIGHT // 2
            start_x = cx - total_width // 2
            
            text_rect = text_surface.get_rect(midleft=(start_x + circle_radius * 2 + gap, cy))
            
            # Pulsing box effect
            pulse = abs(math.sin(self.reset_timer * 0.05))
            pulse_inflate_w = 60 + 30 * pulse
            pulse_inflate_h = 40 + 30 * pulse
            
            bg_rect = pygame.Rect(0, 0, total_width + pulse_inflate_w, max(text_surface.get_height(), circle_radius * 2) + pulse_inflate_h)
            bg_rect.center = (cx, cy)
            
            # Give UI text a dark backing
            pygame.draw.rect(self.screen, NEON_BG, bg_rect)
            pygame.draw.rect(self.screen, border_color, bg_rect, max(4, int(6 + 4 * pulse)))
            
            # Draw circle indicator
            pygame.draw.circle(self.screen, win_color, (int(start_x + circle_radius), cy), circle_radius)
            pygame.draw.circle(self.screen, win_color_bright, (int(start_x + circle_radius), cy), int(circle_radius * 0.6))
            
            self.screen.blit(text_surface, text_rect)
        
        # Tekken-style HUD on top of everything
        self._draw_hud(self.screen)
        
        # Draw game surface to high-res canvas
        self.canvas.fill((15, 15, 15))  # Dark background for dead space
        y_offset = (CANVAS_HEIGHT - SCREEN_HEIGHT) // 2
        self.canvas.blit(self.screen, (0, y_offset))
        
        # Scale down and present to the laptop display window
        scaled_preview = pygame.transform.smoothscale(self.canvas, (DISPLAY_WIDTH, DISPLAY_HEIGHT))
        self.window.blit(scaled_preview, (0, 0))
        
        pygame.display.flip()
    
    def _draw_hud(self, surface):
        """Draw Tekken-style static health bars flush above the arena."""
        # Part 1: Dynamic arena positioning
        ax, ay, aw, ah = self.arena_bounds
        bar_width = (aw // 2) - 20
        bar_height = 20
        bar_y = ay - bar_height - 10  # 10px padding above arena top line
        
        bg_color = (30, 30, 30)
        dark_border_color = (60, 60, 60)  # Cel-shaded dark outline
        
        # --- Blue (Left) Bar: depletes right-to-left, anchored to left arena wall ---
        bar_x = ax
        blue_hp_ratio = max(0.0, self.blue.health / self.blue.max_health)
        blue_fill_w = int(bar_width * blue_hp_ratio)
        
        # Background (missing health)
        pygame.draw.rect(surface, bg_color, (bar_x, bar_y, bar_width, bar_height))
        # Health fill (anchored to left edge, depletes from right)
        if blue_fill_w > 0:
            pygame.draw.rect(surface, self.blue.render_color,
                            (bar_x, bar_y, blue_fill_w, bar_height))
        # Dark border outline
        pygame.draw.rect(surface, dark_border_color, (bar_x, bar_y, bar_width, bar_height), 2)
        
        # --- Red (Right) Bar: depletes left-to-right, anchored to right arena wall ---
        bar_x = ax + aw - bar_width
        red_hp_ratio = max(0.0, self.red.health / self.red.max_health)
        red_fill_w = int(bar_width * red_hp_ratio)
        
        # Background (missing health)
        pygame.draw.rect(surface, bg_color, (bar_x, bar_y, bar_width, bar_height))
        # Health fill (anchored to right edge, depletes from left)
        if red_fill_w > 0:
            fill_x = bar_x + (bar_width - red_fill_w)
            pygame.draw.rect(surface, self.red.render_color,
                            (fill_x, bar_y, red_fill_w, bar_height))
        # Dark border outline
        pygame.draw.rect(surface, dark_border_color, (bar_x, bar_y, bar_width, bar_height), 2)
        
        # --- VS Text (centered between the two bars) ---
        vs_font = self.font_small
        vs_surface = vs_font.render("VS", True, WHITE)
        vs_rect = vs_surface.get_rect(center=(ax + (aw // 2), bar_y + (bar_height // 2)))
        surface.blit(vs_surface, vs_rect)
    
    def _draw_grid(self, offset):
        """Draw faint grid for cyberpunk aesthetic."""
        ox, oy = offset
        grid_spacing = 40
        
        for x in range(0, SCREEN_WIDTH + grid_spacing, grid_spacing):
            pygame.draw.line(self.screen, NEON_GRID, 
                           (int(x + ox), 0), (int(x + ox), SCREEN_HEIGHT), 1)
        
        for y in range(0, SCREEN_HEIGHT + grid_spacing, grid_spacing):
            pygame.draw.line(self.screen, NEON_GRID,
                           (0, int(y + oy)), (SCREEN_WIDTH, int(y + oy)), 1)
    
    def _draw_tron_trails(self, offset):
        """Draw TRON MODE solid neon trail walls."""
        ox, oy = offset
        trails = self.chaos.get_tron_trails()
        
        # Draw blue fighter's trail in neon blue
        blue_trail = trails.get('blue', [])
        if len(blue_trail) >= 2:
            for i in range(1, len(blue_trail)):
                x1, y1 = blue_trail[i-1]
                x2, y2 = blue_trail[i]
                pygame.draw.line(self.screen, self.f1_color,
                               (int(x1 + ox), int(y1 + oy)),
                               (int(x2 + ox), int(y2 + oy)), 4)
        
        # Draw red fighter's trail in neon red
        red_trail = trails.get('red', [])
        if len(red_trail) >= 2:
            for i in range(1, len(red_trail)):
                x1, y1 = red_trail[i-1]
                x2, y2 = red_trail[i]
                pygame.draw.line(self.screen, self.f2_color,
                               (int(x1 + ox), int(y1 + oy)),
                               (int(x2 + ox), int(y2 + oy)), 4)
    
    def _draw_glitch_rects(self):
        """Draw GLITCH TRAP visual glitch rectangles."""
        for x, y, w, h, color in self.chaos.get_glitch_rects():
            surf = pygame.Surface((w, h), pygame.SRCALPHA)
            surf.fill((*color, 100))  # Semi-transparent
            self.screen.blit(surf, (x, y))
    
    def _draw_moving_wall(self, offset, arena_bounds):
        """Draw MOVING WALLS vertical bar."""
        ox, oy = offset
        ax, ay, aw, ah = arena_bounds
        
        wall_x, wall_width, wall_dir = self.chaos.get_moving_wall()
        
        # Draw glowing wall
        wall_rect = pygame.Rect(
            int(wall_x - wall_width // 2 + ox),
            int(ay + oy),
            wall_width,
            int(ah)
        )
        
        # Glow effect
        glow_rect = wall_rect.inflate(8, 0)
        glow_surf = pygame.Surface((glow_rect.width, glow_rect.height), pygame.SRCALPHA)
        pygame.draw.rect(glow_surf, (*self.f1_color, 60), glow_surf.get_rect())
        self.screen.blit(glow_surf, glow_rect)
        
        # Main wall
        pygame.draw.rect(self.screen, self.f1_color, wall_rect)

    def run(self):
        """Main loop."""
        import sys
        if "--auto-start" in sys.argv:
            self.game_state = 'PLAYING'
            self._start_obs_recording()
            self.obs_startup_timer = 60
        elif "--test-mode" in sys.argv:
            self.game_state = 'PLAYING'

        running = True
        while running:
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    running = False
                elif event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_ESCAPE:
                        running = False
                    elif event.key == pygame.K_SPACE:
                        if self.game_state == 'TITLE':
                            self.game_state = 'PLAYING'
                            self._start_obs_recording()  # Start OBS
                            self.obs_startup_timer = 60  # Delay on start
                        else:
                            self.paused = not self.paused
                    elif event.key == pygame.K_m:
                        # Manual delay
                        self.obs_startup_timer = 60
                    elif event.key == pygame.K_r:
                        self._reset_round()
                elif event.type == pygame.MOUSEBUTTONDOWN:
                    if self.game_state == 'TITLE':
                        self.game_state = 'PLAYING'
                        self._start_obs_recording()  # Start OBS
                        self.obs_startup_timer = 60  # Delay on start
            
            if self.game_state == 'TITLE':
                self._draw_title_screen()
            else:
                self.update()
                self.draw()
            self.clock.tick(FPS)
        
        # Stop OBS before shutting down entirely
        self._stop_obs_recording()
        pygame.quit()


if __name__ == "__main__":
    import sys
    import random
    from config import NEON_PALETTE
    
    # Randomize two distinct fighter colors
    f1_key = random.choice(list(NEON_PALETTE.keys()))
    available = [k for k in NEON_PALETTE.keys() if k != f1_key]
    f2_key = random.choice(available)
    
    print(f"[MATCH STARTING]")
    print(f"Fighter 1: {NEON_PALETTE[f1_key][0]}")
    print(f"Fighter 2: {NEON_PALETTE[f2_key][0]}")
    
    game = Game(f1_key, f2_key)
    game.run()
