import pygame
import math
import random
import os
import json

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
    NEON_BG, NEON_GRID,
    CRIT_CHANCE, CRIT_MULTIPLIER, CRIT_IMPACT_FRAMES, CRIT_IMPACT_TIMESCALE
)
from effects import ParticleSystem, ShockwaveSystem, ArenaPulseSystem, DamageNumberSystem
from fighter import Fighter
from obs_manager import OBSManager
from combat_manager import CombatManager
from ui_renderer import UIRenderer


# Main game class - DVD logo style combat with rotating swords.
class Game:    
    def __init__(self, f1_color, f2_color, f1_name="Blue", f2_name="Red"):
        self.f1_name = f1_name
        self.f2_name = f2_name
        self.f1_color = f1_color
        self.f1_bright = tuple(min(255, c + 100) for c in f1_color)
        self.f2_color = f2_color
        self.f2_bright = tuple(min(255, c + 100) for c in f2_color)
        
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
        

        
        # Arena Escalation System
        self.inactivity_timer = 0
        
        # Parry Escalation System
        self.total_parries = 0
        
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
        
        # Main Component Managers
        self.obs_manager = OBSManager(self.f1_name, self.f2_name)
        self.obs_manager.connect()
        self.combat_manager = CombatManager()
        self.ui_renderer = UIRenderer(self.screen, self.font_medium, self.font_small)
        
        # Load sounds.
        self._setup_sounds()
        
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
        """Unlock fighters and trigger a magnetic pulse toward the center."""
        self.blue.locked = False
        self.red.locked = False
        
        # Trigger the visual and audio pulse effect
        self._trigger_arena_pulse()
        
        # Launch them directly at the center for a massive opening clash
        from config import SCREEN_WIDTH, SCREEN_HEIGHT
        import math
        
        center_x = SCREEN_WIDTH // 2
        center_y = SCREEN_HEIGHT // 2
        
        # Calculate launch vectors
        dx_b = center_x - self.blue.x
        dy_b = center_y - self.blue.y
        dist_b = max(1, math.hypot(dx_b, dy_b))
        self.blue.vx = (dx_b / dist_b) * 18  # High-speed initial launch
        self.blue.vy = (dy_b / dist_b) * 18
        
        dx_r = center_x - self.red.x
        dy_r = center_y - self.red.y
        dist_r = max(1, math.hypot(dx_r, dy_r))
        self.red.vx = (dx_r / dist_r) * 18
        self.red.vy = (dy_r / dist_r) * 18
    

    
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
        loser.flash_timer = 0
        death_color = loser.color
            
        self.particles.emit_explosion(loser.x, loser.y, death_color, count=40)
        self.shockwaves.add(loser.x, loser.y, death_color, 100)
        winner.victory_bounce = 40
        
        self.slow_motion = True
        self.slow_motion_accumulator = 0.0
        
        # Death sound sequence: death_final_hit first, sword_to_ground after freeze
        self.death_sound_phase = 1
        if self.sounds_enabled and self.death_final_hit_sound:
            self.death_final_hit_sound.play()
        
        self._stop_escalation_sound()
        
        # Calculate winner's remaining health percentage
        hp_percent = (winner.health / winner.max_health) * 100
        winner_color_name = self.f1_name if winner == self.blue else self.f2_name
        loser_color_name = self.f2_name if winner == self.blue else self.f1_name

        # Expanded 15-Title Pools (SPOILER-FREE)
        if hp_percent <= 10:
            category = "clutch"
            titles = [
                f"The greatest 1 HP comeback in AlgoRot history?!",
                f"Someone actually survived on 1 HP! ({self.f1_name} vs {self.f2_name})",
                f"Never count them out... INSANE Ending!",
                f"They thought it was over... (Wait for it)",
                f"The Ultimate Underdog Story: {self.f1_name} vs {self.f2_name}!",
                f"A literal miracle in the final seconds!",
                f"Greatest Plot Twist: Someone refuses to die!",
                f"99% of people thought this was over... Then they woke up!",
                f"How did they survive that?! (1 HP Comeback)",
                f"A massive lead just got CHOKED in {self.f1_name} vs {self.f2_name}!",
                f"The exact moment the tables turned!",
                f"The craziest buzzer-beater win yet!",
                f"From the brink of defeat: A legendary clutch!",
                f"Do not swipe away... this comeback is pure cinema!",
                f"{self.f1_name} vs {self.f2_name} goes down to the wire!"
            ]
        elif hp_percent >= 75:
            category = "blowout"
            titles = [
                f"ABSOLUTE DOMINATION! ({self.f1_name} vs {self.f2_name})",
                f"Is one of these colors broken in AlgoRot?!",
                f"FLAWLESS VICTORY! Someone gets destroyed!",
                f"Nobody can stop them... Just watch.",
                f"They didn't stand a chance...",
                f"The most one-sided battle in AlgoRot history!",
                f"Pure Destruction: {self.f1_name} vs {self.f2_name}!",
                f"Someone just proved they are the final boss!",
                f"A masterclass in physics!",
                f"Someone got absolutely vaporized...",
                f"Speedrun? Finished with NO MERCY!",
                f"Are they cheating?! (Flawless Win)",
                f"Casually wiping the floor with their opponent.",
                f"Total annihilation: Zero damage taken!",
                f"They need to be deleted after what just happened."
            ]
        else:
            category = "standard"
            titles = [
                f"{self.f1_name} vs {self.f2_name} ends in SHOCKING Sudden Death!",
                f"The physics in this {self.f1_name} vs {self.f2_name} match went CRAZY!",
                f"10 Parries Later... {self.f1_name} vs {self.f2_name} goes Nuclear!",
                f"This {self.f1_name} vs {self.f2_name} Sudden Death will give you chills!",
                f"NO WAY! The {self.f1_name} vs {self.f2_name} Match Was Too Close!",
                f"Wait until the end of this {self.f1_name} vs {self.f2_name} fight!",
                f"You won't believe how {self.f1_name} vs {self.f2_name} ends!",
                f"Are we dreaming?! {self.f1_name} vs {self.f2_name} goes off the rails!",
                f"This collision between {self.f1_name} and {self.f2_name} broke the engine!",
                f"The most intense rivalry yet! ({self.f1_name} vs {self.f2_name})",
                f"Pure satisfying chaos: {self.f1_name} vs {self.f2_name} Sudden Death!",
                f"My brain melted watching {self.f1_name} vs {self.f2_name}...",
                f"Who are you rooting for? ({self.f1_name} vs {self.f2_name} Epic Ending)",
                f"Gravity stopped working in this {self.f1_name} vs {self.f2_name} clash!",
                f"The exact moment {self.f1_name} vs {self.f2_name} turned into a movie!"
            ]

        # Persistent JSON Tracker Logic (INDEX-BASED)
        tracker_file = "used_titles.json"
        
        # Load existing tracker data
        if os.path.exists(tracker_file):
            with open(tracker_file, 'r') as f:
                tracker_data = json.load(f)
        else:
            tracker_data = {"clutch": [], "blowout": [], "standard": []}
            
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
        
        # Save the picked index to the tracker (not the string)
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
        self.round_timer = 0
        self.particles.clear()
        self.shockwaves.clear()
        self.arena_pulses.clear()
        self.damage_numbers.clear()
        
        self._stop_escalation_sound()
        
        self.hit_slowmo_frames = 0
        self.hit_slowmo_accumulator = 0.0
        
        # Reset critical hit impact state
        self.crit_impact_frames = 0
        self.crit_impact_accumulator = 0.0
        self.crit_flash_phase = 0
        
        self.inactivity_timer = 0
        self.total_parries = 0
        
        self._lock_fighters_for_countdown()
        self.countdown_stage = 0
        self.countdown_timer = 0
        self.countdown_active = True
        
        # Reset countdown and death sound state
        self.countdown_beep_played = [False, False, False]
        self.fight_sound_played = False
        self.death_sound_phase = 0

        
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
        

        
        # Arena Escalation (Repeating Pulse)
        self.inactivity_timer += 1
        if self.inactivity_timer >= INACTIVITY_PULSE_TIME * FPS:
            self._trigger_arena_pulse()
            self.inactivity_timer = 0  # Reset so it pulses again in 2 seconds if still inactive
        
        effective_arena = tuple(self.arena_bounds)
        
        # Update fighters with effective arena
        self.blue.update(self.red, effective_arena, self.particles, self.shockwaves)
        self.red.update(self.blue, effective_arena, self.particles, self.shockwaves)
        
        # Body-to-body collision separation (prevent overlap that causes phantom sword hits)
        dx = self.red.x - self.blue.x
        dy = self.red.y - self.blue.y
        body_dist = math.hypot(dx, dy)
        min_sep = self.blue.radius + self.red.radius
        if body_dist < min_sep and body_dist > 0:
            overlap = (min_sep - body_dist) / 2.0
            nx = dx / body_dist
            ny = dy / body_dist
            self.blue.x -= nx * overlap
            self.blue.y -= ny * overlap
            self.red.x += nx * overlap
            self.red.y += ny * overlap
        

        
        self.combat_manager.handle_collisions(self.blue, self.red, self)
        
        self.particles.update()
        self.shockwaves.update()
        self.arena_pulses.update()
        self.damage_numbers.update()
        
        if self.blue.health <= 0:
            self._end_round(winner=self.red, loser=self.blue)
        elif self.red.health <= 0:
            self._end_round(winner=self.blue, loser=self.red)


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
        """Draw game with neon visuals."""
        offset = (0, 0)
        if self.screen_shake > 0:
            offset = (random.uniform(-self.screen_shake, self.screen_shake),
                     random.uniform(-self.screen_shake, self.screen_shake))
        
        self.screen.fill(NEON_BG)
        
        self._draw_grid(offset)
        
        draw_arena = self.arena_bounds
        
        ax, ay, aw, ah = draw_arena
        arena_rect = pygame.Rect(int(ax + offset[0]), int(ay + offset[1]), int(aw), int(ah))
        
        arena_fill = BLACK
        pygame.draw.rect(self.screen, arena_fill, arena_rect)
        
        # Draw background logo watermark
        if hasattr(self, 'bg_logo') and self.bg_logo:
            # Center logo in current drawn arena
            logo_rect = self.bg_logo.get_rect(center=(int(ax + aw/2 + offset[0]), int(ay + ah/2 + offset[1])))
            self.screen.blit(self.bg_logo, logo_rect)
        
        # Base swap logic for border color (180 frames = 3 seconds at 60fps)
        base_border_color = self.f1_color if (self.round_timer // 180) % 2 == 0 else self.f2_color
        
        # Arena border — flash RED/WHITE during Sudden Death
        if self.total_parries >= 15:
            border_color = (255, 0, 0) if (self.round_timer // 4) % 2 == 0 else WHITE
            border_width = 6
        else:
            border_color = base_border_color
            border_width = 4
        pygame.draw.rect(self.screen, border_color, arena_rect, border_width)
        
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
        
        # UI Overlays
        self.ui_renderer.draw(self)
        
        # Draw game surface to high-res canvas
        self.canvas.fill((15, 15, 15))  # Dark background for dead space
        y_offset = (CANVAS_HEIGHT - SCREEN_HEIGHT) // 2
        self.canvas.blit(self.screen, (0, y_offset))
        
        # Scale down and present to the laptop display window
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
            self.obs_manager.start_recording()
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
                        self.obs_startup_timer = 60  # Delay on start
            
            if self.game_state == 'TITLE':
                self._draw_title_screen()
            else:
                self.update()
                self.draw()
            self.clock.tick(FPS)
        
        # Stop OBS before shutting down entirely
        self.obs_manager.stop_recording(getattr(self, 'viral_title_idea', None))
        pygame.quit()


if __name__ == "__main__":
    import sys
    import random
    from config import BASE_COLORS
    
    # Randomly pick two distinct color names from the 12-slice wheel
    name_1, name_2 = random.sample(list(BASE_COLORS.keys()), 2)
    
    print("[MATCH STARTING]")
    print(f"Fighter 1: {name_1}")
    print(f"Fighter 2: {name_2}")
    
    game = Game(BASE_COLORS[name_1], BASE_COLORS[name_2], name_1, name_2)
    game.run()
