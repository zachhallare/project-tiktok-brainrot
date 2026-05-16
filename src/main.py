"""
Core orchestration engine for AlgoRot combat simulations.

This module serves as the central entry point and game loop for the simulation. 
It integrates physics (DVD-logo style), combat logic, visual effects, and 
automated recording via OBS Studio.

The engine is specifically tuned for short-form video production (YT Shorts), 
featuring high-impact cinematic hooks, dynamic title generation, and 
automated batch processing.
"""

import pygame
import math
import random
import os
import json
import time

from titles import get_title_pools
from config import FIGHTER_RADIUS

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
    WHITE, PURPLE, BLACK, ARENA_BG, DARK_GRAY, GRAY, YELLOW, PULSE_WHITE,
    ARENA_MARGIN, ARENA_WIDTH, ARENA_HEIGHT,
    ROUND_MAX_TIME, BASE_KNOCKBACK, DAMAGE_PER_HIT, SLOW_MOTION_SPEED,
    HIT_STOP_FRAMES, SCREEN_SHAKE_INTENSITY, SCREEN_SHAKE_DECAY,
    HIT_SLOWMO_FRAMES, HIT_SLOWMO_TIMESCALE,
    INACTIVITY_PULSE_TIME, ARENA_PULSE_VELOCITY_BOOST,
    ARENA_PULSE_SHAKE,
    NEON_BG, NEON_GRID,
    CRIT_CHANCE, CRIT_MULTIPLIER, CRIT_IMPACT_FRAMES, CRIT_IMPACT_TIMESCALE
)

from effects import ParticleSystem, ShockwaveSystem, ArenaPulseSystem, DamageNumberSystem
from entities.fighter import Fighter
from managers.obs_manager import OBSManager
from managers.combat_manager import CombatManager
from renderers.ui_renderer import UIRenderer


class Game:
    """Central game controller for the AlgoRot simulation.

    The Game class manages the lifecycle of a match, including initialization, 
    the frame-by-frame physics loop, event handling, and the transition 
    between combat and victory states.

    Attributes:
        is_test_mode (bool): If True, disables persistent tracking and OBS.
        is_headless (bool): If True, runs without a visible Pygame window.
        obs_manager (OBSManager): Orchestrates recording via WebSocket.
        combat_manager (CombatManager): Handles collision detection/resolution.
        ui_renderer (UIRenderer): Manages the Tekken-style HUD and victory screens.
    """
    def __init__(self, f1_color, f2_color, f1_name="Blue", f2_name="Red", f1_weapon="sword", f2_weapon="sword"):
        import sys
        self.is_test_mode = "--test-mode" in sys.argv
        self.is_headless = "--headless" in sys.argv
        self.f1_weapon = f1_weapon
        self.f2_weapon = f2_weapon
        self.f1_name = f1_name
        self.f2_name = f2_name
        self.f1_color = f1_color
        self.f1_bright = tuple(min(255, c + 100) for c in f1_color)
        self.f2_color = f2_color
        self.f2_bright = tuple(min(255, c + 100) for c in f2_color)
        
        # Initialize pygame modules
        pygame.init()
        pygame.font.init()
        
        # Create the game window.
        flags = pygame.NOFRAME | pygame.HIDDEN if getattr(self, 'is_headless', False) else pygame.NOFRAME
        self.window = pygame.display.set_mode((DISPLAY_WIDTH, DISPLAY_HEIGHT), flags)
        self.canvas = pygame.Surface((CANVAS_WIDTH, CANVAS_HEIGHT))
        self.screen = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT))
        pygame.display.set_caption("Red vs Blue Battle - YT Shorts Edition")
        self.clock = pygame.time.Clock()

        # Border Flash State
        self.border_flash_timer = 0
        self.border_flash_max = 0
        self.border_flash_color = WHITE
        
        # Fonts for UI text
        self.font_large = pygame.font.Font(None, 120)
        self.font_medium = pygame.font.Font(None, 72)
        self.font_small = pygame.font.Font(None, 36)
        self.momentum_bias = 0.0  # -1.0 = f2 dominating, +1.0 = f1 dominating
        
        # Define the base arena square.
        self.base_arena = (ARENA_MARGIN, ARENA_MARGIN, ARENA_WIDTH, ARENA_HEIGHT)
        self.arena_bounds = list(self.base_arena)
        
        # Use neon colors for fighters
        # Spawn 60-70% in from their edges so weapons nearly touch at center
        arena_half = (SCREEN_WIDTH - ARENA_MARGIN * 2) / 2
        spawn_inset = arena_half * 0.65  # 65% in from edge
        center_y = SCREEN_HEIGHT // 2
        self.blue = Fighter(ARENA_MARGIN + spawn_inset, center_y, 
                            self.f1_color, self.f1_bright, is_blue=True, weapon=f1_weapon)
        self.red = Fighter(SCREEN_WIDTH - ARENA_MARGIN - spawn_inset, center_y, 
                            self.f2_color, self.f2_bright, is_blue=False, weapon=f2_weapon)
        
        # Lock fighters for countdown
        self._lock_fighters_for_countdown()
        
        # Visual effect systems.
        self.particles = ParticleSystem()
        self.shockwaves = ShockwaveSystem()
        self.arena_pulses = ArenaPulseSystem()
        self.damage_numbers = DamageNumberSystem()
                
        # Screen effects.
        self.screen_shake = 0
        self.hit_stop = 0
        self.hit_slowmo_frames = 0
        self.hit_slowmo_accumulator = 0.0
        
        # Decomposition Effect
        self.decomp_slowmo_frames = 0
        self.decomp_slowmo_accumulator = 0.0
        
        # Critical Hit Impact Sequence
        self.crit_impact_frames = 0
        self.crit_impact_accumulator = 0.0
        self.crit_flash_phase = 0  # 0=none, 1=black, 2=white, 3+=done
        
        # Round state tracking.
        self.round_timer = 0
        self.round_ending = False
        self.winner = None
        self.winner_text = ""
        self.winner_particles_spawned = False
        self.reset_timer = 0
        self.lead_changes = 0
        self.current_leader = None
        self.max_blue_lead = 0.0
        self.max_red_lead = 0.0
        
        # UI controls.
        self.paused = False
        self.slow_motion = False
        self.slow_motion_accumulator = 0.0
        
        # Pre-fight countdown (cinematic hook for Shorts retention)
        self.countdown_stage = 0
        self.countdown_timer = 0
        self.countdown_active = True
        self.countdown_texts = ["3", "2", "1", "FIGHT"]
        self.countdown_durations = [22, 22, 28, 45]
        self.fight_punch_frame = False      # 1-frame camera punch on FIGHT reveal.
        self.countdown_flash_timer = 0
        self.countdown_flash_duration = 1  # tracks starting flash length for alpha calc
        
        # Arena Escalation System
        self.inactivity_timer = 0
        
        # Game State
        self.game_state = 'TITLE'
        self.obs_startup_timer = 0
        self.match_start_real_time = 0
        
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
        
        self._wipe_surf = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT))
        self._wipe_surf.fill(WHITE)

        # Load Arena Watermark Logo
        import os
        logo_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), "assets", "images", "logos", "logo-dark-grey-text.png")
        try:
            logo_img = pygame.image.load(logo_path).convert_alpha()
            scale_factor = 400.0 / max(logo_img.get_width(), 1)
            new_size = (int(logo_img.get_width() * scale_factor), int(logo_img.get_height() * scale_factor))
            self.bg_logo = pygame.transform.scale(logo_img, new_size)
            self.bg_logo.set_alpha(60) 
        except Exception as e:
            print(f"Failed to load background logo: {e}")
            self.bg_logo = None
        
        # Main Component Managers
        self.obs_manager = OBSManager(self.f1_name, self.f2_name)
        self.obs_manager.connect()
        self.combat_manager = CombatManager()
        self.ui_renderer = UIRenderer(self.screen, self.font_medium, self.font_small)
        
        # Intro and Outro Renderers
        from renderers.intro_renderer import IntroRenderer
        from renderers.outro_renderer import OutroRenderer

        self.intro_renderer = IntroRenderer(
            screen=self.screen,
            clock=self.clock,
            f1_name=self.f1_name,
            f2_name=self.f2_name,
            f1_color=self.f1_color,
            f2_color=self.f2_color,
            font_large=self.font_large,
            f1_weapon=self.f1_weapon,
            f2_weapon=self.f2_weapon,
        )

        self.outro_renderer = OutroRenderer(self.screen, self.clock, self.font_large)
        
        # Initialize centralized SoundManager
        from managers.sound_manager import SoundManager
        self.sound_manager = SoundManager()
        if "--mute-sounds" in sys.argv or getattr(self, 'is_headless', False):
            self.sound_manager.muted = True
        

    def _lock_fighters_for_countdown(self):
        """Lock fighters in place for countdown — weapons keep spinning."""
        self.blue.locked = True
        self.red.locked  = True
        self.blue.vx = self.blue.vy = 0
        self.red.vx  = self.red.vy  = 0

        # Angle weapons ~60° outward so long weapons don't overlap at center
        # Blue spins clockwise (spin_direction=1), so starting angled up-right
        # means it naturally sweeps toward the opponent — feels aggressive
        self.blue.rotation_angle = -(math.pi / 3)   # ~-60° (upper-right)
        self.blue.sword_angle    = self.blue.rotation_angle

        self.red.rotation_angle  = math.pi + (math.pi / 3)  # ~240° (upper-left)
        self.red.sword_angle     = self.red.rotation_angle
        

    def _unlock_fighters(self):
        """Unlock fighters and launch them at each other from close range."""
        self.blue.locked = False
        self.red.locked = False
        self.match_start_real_time = time.time()
        self._trigger_arena_pulse()     # Trigger the visual and audio pulse effect
        
        # Launch directly at each other — close spawn means first clash is near-instant
        from config import SCREEN_WIDTH, SCREEN_HEIGHT
        import math
        
        center_x = SCREEN_WIDTH // 2
        center_y = SCREEN_HEIGHT // 2

        vertical_jitter = random.uniform(-4, 4)

        # Calculate launch vectors (high speed for immediate collision)
        dx_b = center_x - self.blue.x
        dy_b = center_y - self.blue.y
        dist_b = max(1, math.hypot(dx_b, dy_b))
        self.blue.vx = (dx_b / dist_b) * 20  # Faster launch from closer position
        self.blue.vy = (dy_b / dist_b) * 20 + vertical_jitter
        
        dx_r = center_x - self.red.x
        dy_r = center_y - self.red.y
        dist_r = max(1, math.hypot(dx_r, dy_r))
        self.red.vx = (dx_r / dist_r) * 20
        self.red.vy = (dy_r / dist_r) * 20 - vertical_jitter


    def _reset_inactivity(self):
        """Reset inactivity timer."""
        self.inactivity_timer = 0
    

    def _trigger_arena_pulse(self):
        """Trigger Arena Pulse."""
        self.arena_pulses.add(tuple(self.arena_bounds), PULSE_WHITE)
        self.screen_shake = ARENA_PULSE_SHAKE
        
        # Play arena pulse sound
        if hasattr(self, 'sound_manager'):
            self.sound_manager.play_arena_pulse()
        
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


    def _start_escalation_sound(self):
        pass

    def _stop_escalation_sound(self):
        pass


    def _trigger_hit(self, x, y, color, hit_stop_frames=None, damage=0, is_crit=False):
        """Apply hit effects including damage numbers."""
        self.particles.emit(x, y, WHITE, count=10 if not is_crit else 20, size=4 if not is_crit else 6)
        self.hit_stop = hit_stop_frames if hit_stop_frames else HIT_STOP_FRAMES
        self.screen_shake = SCREEN_SHAKE_INTENSITY

        # Border flash: crits punch harder and hold longer
        self.border_flash_timer = 28 if is_crit else 16
        self.border_flash_max = self.border_flash_timer
        self.border_flash_color = color

        if damage > 0:
            self.damage_numbers.spawn(x, y - 20, damage, color, is_crit)

        if is_crit:
            self.sound_manager.play_crit()
        else:
            self.sound_manager.play_hit()

        # Momentum bias: crits push harder than normal hits
        bias_push = 0.25 if is_crit else 0.12

        if color == self.f1_color:
            self.momentum_bias = min(1.0, self.momentum_bias + bias_push)
        else:
            self.momentum_bias = max(-1.0, self.momentum_bias - bias_push)


    def _end_round(self, winner, loser):
        """Handle round end."""
        self.round_ending = True
        self.winner = winner
        self.reset_timer = 0 if getattr(self, 'is_headless', False) else 75
        
        if winner == self.blue:
            self.winner_text = "WINS"
        else:
            self.winner_text = "WINS"
        
        # Color state reversion and death animation rules
        loser.flash_timer = 0
        winner.flash_timer = 0
        death_color = loser.color
            
        self.particles.emit_explosion(loser.x, loser.y, death_color, count=40)
        self.shockwaves.add(loser.x, loser.y, death_color, 100)
        winner.victory_bounce = 40
        
        # Transition to Slow-Motion for the final blow
        self.slow_motion = True
        self.slow_motion_accumulator = 0.0
        
        # Audio Pacing: Play the final impact sound immediately, then wait for 
        # the freeze frame to clear before playing the environmental death cues.
        self.death_sound_phase = 1
        if hasattr(self, 'sound_manager'):
            self.sound_manager.play_death_final_hit()
        
        self._stop_escalation_sound()
        
        # Calculate winner's remaining health percentage (clamp to 0 — both fighters
        # can take lethal damage in the same frame, leaving the "winner" below zero)
        hp_percent = max(0, (winner.health / winner.max_health) * 100)
        winner_color_name = self.f1_name if winner == self.blue else self.f2_name
        loser_color_name = self.f2_name if winner == self.blue else self.f1_name
        winner_weapon = self.f1_weapon if winner == self.blue else self.f2_weapon
        loser_weapon = self.f2_weapon if winner == self.blue else self.f1_weapon

        # Structured result for auto-test parsing
        if self.is_test_mode:
            duration = time.time() - self.match_start_real_time
            winner_side = "L" if winner == self.blue else "R"
            print(f"[RESULT] winner={winner_weapon} side={winner_side} hp_pct={hp_percent:.0f} time={duration:.2f}s")

        # Determine HP Category
        if hp_percent == 0:
            hp_category = "ghost"
        elif hp_percent <= 10:
            hp_category = "clutch"
        elif hp_percent >= 60:
            hp_category = "stomp"
        elif hp_percent >= 40:
            hp_category = "blowout"
        else:
            hp_category = "standard"
            
        # Determine Lead Category
        winner_max_lead = self.max_blue_lead if winner == self.blue else self.max_red_lead
        loser_max_lead = self.max_red_lead if winner == self.blue else self.max_blue_lead
        
        lead_category = None
        if self.lead_changes == 0 and winner_max_lead >= 0.10:
            lead_category = "wire_to_wire"
        elif loser_max_lead >= 0.3:
            lead_category = "comeback_choke"
        elif self.lead_changes >= 3:
            lead_category = "contested"
            
        # Title Pools (loaded from titles.py)
        title_pools = get_title_pools(self.f1_name, self.f2_name)
        
        # Priority Selection:
        # 1. ghost            — 0% HP, always overrides everything
        # 2. clutch           — 1-10% HP, too extreme to suppress; blends with narrative if present
        # 3. comeback_choke   — loser had 30%+ lead; comeback + choke pools merged (same event, two angles)
        # 4. wire_to_wire     — zero lead changes; blends with stomp/blowout pool if margin is dominant
        # 5. contested + HP   — 3+ lead changes; blends narrative and margin pools
        # 6. pure HP margin   — standard/blowout/stomp with no narrative arc

        if hp_category == "ghost":
            category = "ghost"
            titles = title_pools["ghost"]

        elif hp_category == "clutch":
            # Clutch is priority 2 — surviving on 1-10% HP is always the headline.
            # Blend in the narrative pool for extra variety if a story arc also exists.
            if lead_category == "comeback_choke":
                category = "clutch_comeback_choke"
                titles = title_pools["clutch"] + title_pools["comeback"] + title_pools["choke"]
            elif lead_category == "wire_to_wire":
                category = "clutch_wire_to_wire"
                titles = title_pools["clutch"] + title_pools["wire_to_wire"]
            elif lead_category == "contested":
                category = "clutch_contested"
                titles = title_pools["clutch"] + title_pools["contested"]
            else:
                category = "clutch"
                titles = title_pools["clutch"]

        elif lead_category == "comeback_choke":
            # Comeback and choke describe the same match from opposite sides.
            # Blend both pools — doubles non-repeating runway.
            category = "comeback_choke"
            titles = title_pools["comeback"] + title_pools["choke"]

        elif lead_category == "wire_to_wire":
            # Wire-to-wire dominant wins blend margin context into the narrative pool.
            if hp_category in ("stomp", "blowout"):
                category = f"wire_to_wire_{hp_category}"
                titles = title_pools["wire_to_wire"] + title_pools[hp_category]
            else:
                category = "wire_to_wire"
                titles = title_pools["wire_to_wire"]

        elif lead_category == "contested":
            # Contested blended with HP margin — already correct, kept as-is.
            category = f"contested_{hp_category}"
            titles = title_pools["contested"] + title_pools[hp_category]

        else:
            # No narrative arc — pure HP margin result.
            category = hp_category
            titles = title_pools[hp_category]


        # Persistent JSON Tracker Logic (INDEX-BASED)
        tracker_file = "used_titles.json"
        
        # Load existing tracker data
        if os.path.exists(tracker_file):
            with open(tracker_file, 'r') as f:
                tracker_data = json.load(f)
        else:
            tracker_data = {}
            
        # Ensure category exists
        if category not in tracker_data:
            tracker_data[category] = []
            
        # Find available indices (0 to len(titles)-1)
        available_indices = [i for i in range(len(titles)) if i not in tracker_data[category]]
        
        # If all indices in this category have been used, reset the pool
        if not available_indices:
            print(f"[INFO] All '{category}' titles used. Resetting pool.")
            tracker_data[category] = []
            available_indices = list(range(len(titles)))
            
        # Pick a random index from the available ones
        chosen_index = random.choice(available_indices)
        title_idea = titles[chosen_index]
        self.viral_title_idea = title_idea
        
        # Viral Metadata Synchronization: Persist the used title index to prevent 
        # content duplication across batch recording sessions.
        if not self.is_test_mode:
            tracker_data[category].append(chosen_index)
            with open(tracker_file, 'w') as f:
                json.dump(tracker_data, f, indent=4)
            

    def _reset_round(self):
        """Reset round."""
        self.blue.reset()
        self.red.reset()
        self.arena_bounds = list(self.base_arena)
        self.round_ending = False
        self.winner = None
        self.winner_text = ""
        self.winner_particles_spawned = False

        self.round_timer = 0
        self.particles.clear()
        self.shockwaves.clear()
        self.arena_pulses.clear()
        self.damage_numbers.clear()
        
        self._stop_escalation_sound()
        
        self.hit_slowmo_frames = 0
        self.hit_slowmo_accumulator = 0.0

        self.border_flash_timer = 0
        self.momentum_bias = 0.0

        self.lead_changes = 0
        self.current_leader = None
        self.max_blue_lead = 0.0
        self.max_red_lead = 0.0
        
        self.lead_changes = 0
        self.current_leader = None
        self.max_blue_lead = 0.0
        self.max_red_lead = 0.0
        
        self.decomp_slowmo_frames = 0
        self.decomp_slowmo_accumulator = 0.0
        
        # Reset critical hit impact state
        self.crit_impact_frames = 0
        self.crit_impact_accumulator = 0.0
        self.crit_flash_phase = 0
        
        self.inactivity_timer = 0
        
        self._lock_fighters_for_countdown()
        self.countdown_stage = 0
        self.countdown_timer = 0
        self.countdown_active = True
        self.countdown_flash_timer = 0
        self.countdown_flash_duration = 1
        
        # Reset countdown and death sound state
        self.countdown_beep_played = [False, False, False]
        self.fight_sound_played = False
        self.death_sound_phase = 0

        # Delay for OBS startup between rounds
        self.obs_startup_timer = 60


    def _snap_fighters_to_intro(self):
        """Silently teleport both fighters back to spawn under the solid-white frame."""
        for f in [self.blue, self.red]:
            f.x, f.y = f.start_x, f.start_y
            f.vx = f.vy = 0
            f.health = f.max_health  # full bars match the intro state
            f.locked = True
            f.trail.clear()
            f.rotation_angle = -(math.pi / 3) if f.is_blue else math.pi + (math.pi / 3)
            f.sword_angle    = f.rotation_angle

        self.particles.clear()
        self.shockwaves.clear()
        self.damage_numbers.clear()
        self.screen_shake = 0
        self.round_timer = 0
        self.momentum_bias = 0.0
        self.border_flash_timer = 0
        self.crit_flash_phase = 0
        self.crit_impact_frames = 0


    def update(self):
        """Main update loop driven by the game clock.

        This method orchestrates the 'Three-Act' structure of an AlgoRot match:
        1. Act I (Countdown): High-impact 'hook' to grab viewer attention.
        2. Act II (Combat): Physics-driven simulation with hit-stops and slow-mo.
        3. Act III (Victory): Viral title selection and recording finalization.

        Bottlenecks: Synchronous OBS communication (rename calls) occurs at the 
        end of the match, which can cause a brief hang if the disk is busy.
        """
        if self.paused:
            return
        
        # Wait for OBS startup to finish before starting countdown
        if getattr(self, 'obs_startup_timer', 0) > 0:
            self.obs_startup_timer -= 1
            return
        
        if self.countdown_active:
            self.countdown_timer += 1
            duration = self.countdown_durations[self.countdown_stage]
            
            # Retention Strategy: Keep weapons spinning during the countdown to 
            # maintain visual motion while the fighters are locked in place.
            self.blue.update_rotation(self.red, 0)
            self.blue.sword_angle = self.blue.rotation_angle
            self.red.update_rotation(self.blue, 0)
            self.red.sword_angle = self.red.rotation_angle
            
            # Decrement flash timer
            if self.countdown_flash_timer > 0:
                self.countdown_flash_timer -= 1
            
            # Play countdown beep sounds for stages 0, 1, 2 ("3", "2", "1")
            if self.countdown_stage < 3 and self.countdown_timer == 1:
                if not hasattr(self, 'countdown_beep_played'):
                    self.countdown_beep_played = [False, False, False]
                if not self.countdown_beep_played[self.countdown_stage]:
                    self.countdown_beep_played[self.countdown_stage] = True
                    if hasattr(self, 'sound_manager'):
                        self.sound_manager.play_countdown_beep()
            
            # Play sword-fight sound when "FIGHT" appears
            if self.countdown_stage == 3 and self.countdown_timer == 1:
                if not hasattr(self, 'fight_sound_played'):
                    self.fight_sound_played = False
                if not self.fight_sound_played:
                    self.fight_sound_played = True
                    if hasattr(self, 'sound_manager'):
                        self.sound_manager.play_sword_fight()
                    # "FIGHT" visual punch: shockwave + particles + shake
                    self.countdown_flash_timer = 6
                    self.countdown_flash_duration = 6
                    self.screen_shake = SCREEN_SHAKE_INTENSITY * 2.0
                    self.fight_punch_frame = True       # Separate 1-frame spike
                    cx = SCREEN_WIDTH // 2
                    cy = SCREEN_HEIGHT // 2
                    self.shockwaves.add(cx, cy, WHITE, 250)
                    self.particles.emit_explosion(cx, cy, self.f1_color, count=30)
                    self.particles.emit_explosion(cx, cy, self.f2_color, count=30)
            
            if self.countdown_timer >= duration:
                self.countdown_timer = 0
                self.countdown_stage += 1
                # Flash on each number transition — escalates toward "1"
                # Stage 0→1 (3→2): 3 frames, Stage 1→2 (2→1): 5 frames, Stage 2→3 (1→FIGHT): 9 frames
                flash_durations = [3, 5, 9, 6]
                flash_val = flash_durations[min(self.countdown_stage - 1, 3)]
                self.countdown_flash_timer = flash_val
                self.countdown_flash_duration = flash_val
                if self.countdown_stage > 3:
                    self.countdown_active = False
                    self._unlock_fighters()

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
            
        # Decomposition Slow-Mo Phase 2 (10% timescale)
        if self.decomp_slowmo_frames > 0:
            self.decomp_slowmo_accumulator += 0.10
            self.decomp_slowmo_frames -= 1
            if self.decomp_slowmo_accumulator < 1.0:
                self.particles.update()
                self.damage_numbers.update()
                return
            self.decomp_slowmo_accumulator -= 1.0
        
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

        # Decrement border flash.
        if self.border_flash_timer > 0:
            self.border_flash_timer -= 1    

        # Momentum bias drifts back to 0 when no hits are landing
        if self.momentum_bias > 0:
            self.momentum_bias = max(0.0, self.momentum_bias - 0.003)
        elif self.momentum_bias < 0:
            self.momentum_bias = min(0.0, self.momentum_bias + 0.003)
        
        if self.round_ending:
            self.reset_timer -= 1
            
            # Play sword_to_ground sound partway through the freeze
            if getattr(self, 'death_sound_phase', 0) == 1 and self.reset_timer < 100:
                self.death_sound_phase = 2
                if hasattr(self, 'sound_manager'):
                    self.sound_manager.play_sword_to_ground()
            
            # ── Loop wipe trigger: 18 sim-frames = 1.5s at 5× slow-mo ───────
            if self.reset_timer <= 18 and not self.loop_wipe_is_closing and not self.loop_wipe_done:
                self.loop_wipe_phase = 1
                self.loop_wipe_timer = 0
                self.loop_wipe_is_closing = True

            if self.reset_timer <= 0:    
                pygame.event.post(pygame.event.Event(pygame.QUIT))
                return

            # Stop updating effects once wipe has started — kills the lingering particle bug
            if not self.loop_wipe_is_closing:
                self.particles.update()
                self.shockwaves.update()
                self.arena_pulses.update()
            return
        
        self.round_timer += 1
        

        # Arena Escalation (Repeating Pulse)
        self.inactivity_timer += 1
        if self.inactivity_timer >= INACTIVITY_PULSE_TIME * FPS:
            self._trigger_arena_pulse()
            self.inactivity_timer = 0  # Reset so it pulses again in 2 seconds if still inactive
        
        effective_arena = tuple(self.arena_bounds)

        # Update fighters with effective arena (pass sound_manager for wall-bounce audio)
        sm = getattr(self, 'sound_manager', None)
        self.blue.update(self.red, effective_arena, self.particles, self.shockwaves, sm)
        self.red.update(self.blue, effective_arena, self.particles, self.shockwaves, sm)
    
        self.combat_manager.handle_collisions(self.blue, self.red, self)
        
        self.particles.update()
        self.shockwaves.update()
        self.arena_pulses.update()
        self.damage_numbers.update()
        
        # Lead tracking
        blue_pct = self.blue.health / max(1, self.blue.max_health)
        red_pct = self.red.health / max(1, self.red.max_health)
        
        if blue_pct > red_pct:
            leader = self.blue
            self.max_blue_lead = max(self.max_blue_lead, blue_pct - red_pct)
        elif red_pct > blue_pct:
            leader = self.red
            self.max_red_lead = max(self.max_red_lead, red_pct - blue_pct)
        else:
            leader = None
            
        if leader and leader != self.current_leader:
            if self.current_leader is not None:
                self.lead_changes += 1
            self.current_leader = leader
        
        if self.blue.health <= 0:
            self._end_round(winner=self.red, loser=self.blue)
        elif self.red.health <= 0:
            self._end_round(winner=self.blue, loser=self.red)


    def draw(self):
        """Draw coordinator. Each section is isolated — edit one without touching others."""
        offset = self._compute_shake_offset()

        self.screen.fill(NEON_BG)
        self._draw_grid(offset)
        self._draw_arena(offset)
        self._draw_effects(offset)
        self._draw_fighters(offset)
        self._draw_crit_flash()
        self._draw_countdown_overlay()
        self._draw_winner_outro()
        self.ui_renderer.draw(self)
        self._draw_loop_reveal_overlay()    # ← labels + weapon spin, under the wipe
        self._draw_loop_wipe()              # ← white flash on top of everything
        self._present_to_window()


    def _draw_countdown_overlay(self):
        """
        Countdown overlay drawn during pre-fight sequence.
        Delegate to intro_renderer so this method never needs to be edited directly.
        """
        if not self.countdown_active:
            return
        self.intro_renderer.draw_countdown(
            screen=self.screen,
            stage=self.countdown_stage,
            timer=self.countdown_timer,
            durations=self.countdown_durations,
            texts=self.countdown_texts,
            f1_color=self.f1_color,
            f2_color=self.f2_color,
            f1_bright=self.f1_bright,
            f2_bright=self.f2_bright,
            flash_timer=self.countdown_flash_timer,
            flash_duration=self.countdown_flash_duration,
            font_large=self.font_large,
        )


    def _draw_loop_wipe(self):
        """
        Full-screen white flash bridging outro → intro for a seamless loop.
        Timer advances every real frame (smooth alpha), not every sim frame.

        Phase 1 — fade to white  (18 real frames, ~0.30 s)
        Phase 2 — solid white    ( 9 real frames, ~0.15 s)  ← snap happens here
        Phase 3 — fade back in   (18 real frames, ~0.30 s)
        """
        if self.loop_wipe_phase == 0:
            return

        FLASH_IN  = 18
        SOLID     = 9
        FLASH_OUT = 18

        self.loop_wipe_timer += 1

        if self.loop_wipe_phase == 1:                           # fade to white
            alpha = int(255 * min(1.0, self.loop_wipe_timer / FLASH_IN))
            if self.loop_wipe_timer >= FLASH_IN:
                self.loop_wipe_phase = 2
                self.loop_wipe_timer = 0

        elif self.loop_wipe_phase == 2:                         # solid white
            alpha = 255
            if self.loop_wipe_timer == 1:                       # first solid frame: snap
                self._snap_fighters_to_intro()
            if self.loop_wipe_timer >= SOLID:
                self.loop_wipe_phase = 3
                self.loop_wipe_timer = 0

        elif self.loop_wipe_phase == 3:                         # fade back in
            alpha = int(255 * max(0.0, 1.0 - self.loop_wipe_timer / FLASH_OUT))
            if self.loop_wipe_timer >= FLASH_OUT:
                self.loop_wipe_phase      = 0
                self.loop_wipe_done       = True
                self.loop_wipe_is_closing = False
                return

        self._wipe_surf.set_alpha(alpha)
        self.screen.blit(self._wipe_surf, (0, 0))
        
    
    def _draw_loop_reveal_overlay(self):
        """
        During wipe flash-out and the tail frames, draw the same matchup labels
        the intro shows during 3/2/1 — making the loop visually seamless.
        Also spins weapons every real frame so they're live, not frozen.
        """
        if not (self.loop_wipe_phase == 3 or self.loop_wipe_done):
            return

        # Reuse the intro renderer's matchup card layout directly
        self.intro_renderer._draw_matchup_labels(
            self.screen,
            self.f1_color, self.f2_color,
            self.f1_name, self.f2_name,
            self.f1_bright, self.f2_bright,
        )


    def _draw_winner_outro(self):
        """
        Winner announcement screen. Delegate to outro_renderer.
        Editing outro_renderer.py cannot affect combat draw logic.
        """
        if not (self.round_ending and self.winner_text and self.reset_timer < 55):
            return
        if self.loop_wipe_is_closing or self.loop_wipe_done:       # wipe has begun, hide winner screen
            return
        self.outro_renderer.draw_winner(
            screen=self.screen,
            winner=self.winner,
            winner_text=self.winner_text,
            f1_color=self.f1_color,
            f2_color=self.f2_color,
            blue=self.blue,
            red=self.red,
            particles=self.particles,
            damage_numbers=self.damage_numbers,
            arena_bounds=self.arena_bounds,
            sound_manager=self.sound_manager,
            winner_particles_spawned=self.winner_particles_spawned,
        )
        # Sync back the spawned flag (renderer can't mutate game state directly)
        self.winner_particles_spawned = True


    def _compute_shake_offset(self) -> tuple:
        if getattr(self, 'fight_punch_frame', False):
            punch = SCREEN_SHAKE_INTENSITY * 7
            self.fight_punch_frame = False
            return (random.uniform(-punch, punch), random.uniform(-punch, punch))
        elif self.screen_shake > 0:
            return (random.uniform(-self.screen_shake, self.screen_shake),
                    random.uniform(-self.screen_shake, self.screen_shake))
        return (0, 0)


    def _draw_arena(self, offset):
        """Arena background, logo watermark, and momentum border."""
        ax, ay, aw, ah = self.arena_bounds
        ox, oy = offset
        arena_rect = pygame.Rect(int(ax + ox), int(ay + oy), int(aw), int(ah))

        pygame.draw.rect(self.screen, ARENA_BG, arena_rect)

        if self.bg_logo:
            logo_rect = self.bg_logo.get_rect(
                center=(int(ax + aw / 2 + ox), int(ay + ah / 2 + oy))
            )
            self.screen.blit(self.bg_logo, logo_rect)

        # Skip momentum color until combat starts (keeps it neutral until the first hit)
        if self.round_timer == 0:
            pulse_color = self.f1_color if (pygame.time.get_ticks() // 333) % 2 == 0 else self.f2_color
            border_color = tuple(max(0, int(c * 0.7)) for c in pulse_color)
            border_width = 4
        else:
            # Momentum border (copied verbatim from your original draw())
            if self.momentum_bias >= 0:
                t = self.momentum_bias
                cycle_color = self.f1_color if (self.round_timer // 180) % 2 == 0 else self.f2_color
                base_border = tuple(int(self.f1_color[i] * t + cycle_color[i] * (1 - t)) for i in range(3))
            else:
                t = -self.momentum_bias
                cycle_color = self.f1_color if (self.round_timer // 180) % 2 == 0 else self.f2_color
                base_border = tuple(int(self.f2_color[i] * t + cycle_color[i] * (1 - t)) for i in range(3))

            if self.border_flash_timer > 0:
                blend = self.border_flash_timer / max(1, self.border_flash_max)
                fc = self.border_flash_color
                border_color = tuple(int(fc[i] * blend + base_border[i] * (1 - blend)) for i in range(3))
                border_width = int(4 + 8 * blend)
            else:
                border_color = base_border
                border_width = 4

            pygame.draw.rect(self.screen, border_color, arena_rect, border_width)


    def _draw_effects(self, offset):
        """Arena pulses and shockwaves."""
        self.arena_pulses.draw(self.screen, offset)
        self.shockwaves.draw(self.screen, offset)


    def _draw_fighters(self, offset):
        """Fighter draw routing based on round state."""
        if not self.round_ending:
            self.blue.draw(self.screen, offset)
            self.red.draw(self.screen, offset)
        elif self.loop_wipe_phase == 3 or self.loop_wipe_done:
            # Wipe is pulling back — reveal fighters at intro positions
            self.blue.draw(self.screen, offset)
            self.red.draw(self.screen, offset)
        elif self.reset_timer > 55:
            winner = self.winner
            if winner:
                winner.draw(self.screen, offset)
        self.particles.draw(self.screen, offset)
        self.damage_numbers.draw(self.screen, offset)


    def _draw_crit_flash(self):
        """Critical hit full-screen flash phases."""
        if self.crit_flash_phase == 1:
            self.screen.fill(BLACK)
        elif self.crit_flash_phase == 2:
            self.screen.fill(WHITE)


    def _present_to_window(self):
        """Canvas scaling and final display flip. Always the last draw call."""
        self.canvas.fill((15, 15, 15))
        y_offset = (CANVAS_HEIGHT - SCREEN_HEIGHT) // 2
        self.canvas.blit(self.screen, (0, y_offset))
        scaled_preview = pygame.transform.smoothscale(self.canvas, (DISPLAY_WIDTH, DISPLAY_HEIGHT))
        self.window.blit(scaled_preview, (0, 0))
        pygame.display.flip()
    

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
    

    def run(self):
        """Main loop."""
        import sys
        if "--auto-start" in sys.argv:
            self.game_state = 'PLAYING'
            if not getattr(self, 'is_headless', False):
                self.obs_manager.start_recording()
                self.recording_start_time = time.time()
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
                            self.obs_manager.start_recording()  # Start OBS
                            self.recording_start_time = time.time()
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
                        self.obs_manager.start_recording()  # Start OBS
                        self.recording_start_time = time.time()
                        self.obs_startup_timer = 60  # Delay on start
            
            if self.game_state == 'TITLE':
                if not getattr(self, 'is_headless', False):
                    should_start = self.intro_renderer.draw_title()
                    self._present_to_window()          # always scale + flip after any draw
                    if should_start:
                        self.game_state = 'PLAYING'
                        self.obs_manager.start_recording()
                        self.recording_start_time = time.time()
                        self.obs_startup_timer = 60
            else:
                self.update()
                if not getattr(self, 'is_headless', False):
                    self.draw()
            
            if not getattr(self, 'is_headless', False):
                self.clock.tick(FPS)
        
        # Stop OBS before shutting down entirely
        if not getattr(self, 'is_headless', False):
            video_duration = time.time() - getattr(self, 'recording_start_time', time.time())
            print(f"[VIDEO_DURATION] {video_duration:.2f}")
            self.obs_manager.stop_recording(getattr(self, 'viral_title_idea', None))
        pygame.quit()


if __name__ == "__main__":
    import sys
    import random
    from config import BASE_COLORS, WEAPON_CONFIGS
    
    all_weapon = list(WEAPON_CONFIGS.keys())

    def _pick_weapon(flag, default="sword"):
        if flag in sys.argv:
            idx = sys.argv.index(flag)
            if idx + 1 < len(sys.argv):
                w = sys.argv[idx + 1]
                if w in WEAPON_CONFIGS:
                    return w
                print(f"[WARN] Unknown weapon '{w}', defaulting to {default}.")
        return default

    if "--weapons" in sys.argv and sys.argv[sys.argv.index("--weapons") + 1] == "random":
        f1_weapon, f2_weapon = random.sample(all_weapon, 2)
    else:
        f1_weapon = _pick_weapon("--f1-weapon")
        f2_weapon = _pick_weapon("--f2-weapon")

    # Randomly pick two distinct color names from the 12-slice wheel
    name_1, name_2 = random.sample(list(BASE_COLORS.keys()), 2)
    
    print("[MATCH STARTING]")
    print(f"Fighter 1: {name_1}")
    print(f"Fighter 2: {name_2}")
    
    game = Game(BASE_COLORS[name_1], BASE_COLORS[name_2], name_1, name_2,
                f1_weapon=f1_weapon, f2_weapon=f2_weapon)
    game.run()
