import pygame
import math
import random

# Import constants and classes from other modules.
from config import (
    SCREEN_WIDTH, SCREEN_HEIGHT, FPS,
    WHITE, PURPLE, BLACK, DARK_GRAY, GRAY, YELLOW,
    ARENA_MARGIN, ARENA_WIDTH, ARENA_HEIGHT,
    ARENA_SHRINK_INTERVAL, ARENA_SHRINK_AMOUNT,
    ROUND_MAX_TIME, BASE_KNOCKBACK, DAMAGE_PER_HIT, SLOW_MOTION_SPEED,
    HIT_STOP_FRAMES, SCREEN_SHAKE_INTENSITY, SCREEN_SHAKE_DECAY,
    HIT_SLOWMO_FRAMES, HIT_SLOWMO_TIMESCALE,
    INACTIVITY_PULSE_TIME, INACTIVITY_SHRINK_TIME, ARENA_PULSE_VELOCITY_BOOST,
    ARENA_PULSE_SHAKE, ESCALATION_SHRINK_SPEED,
    NEON_RED, NEON_BLUE, NEON_BG, NEON_GRID,
    CRIT_CHANCE, CRIT_MULTIPLIER, CRIT_IMPACT_FRAMES, CRIT_IMPACT_TIMESCALE
)
from effects import ParticleSystem, ShockwaveSystem, ArenaPulseSystem, DamageNumberSystem
from fighter import Fighter
from chaos_manager import ChaosManager, ChaosTextRenderer


# Main game class - DVD logo style combat with rotating swords.
class Game:    
    def __init__(self):
        # Initialize pygame modules
        pygame.init()
        pygame.mixer.init()
        pygame.font.init()
        
        # Create the game window.
        self.screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
        pygame.display.set_caption("Red vs Blue Battle - TikTok Brainrot Edition")
        self.clock = pygame.time.Clock()
        
        # Fonts for UI text
        self.font_large = pygame.font.Font(None, 120)
        self.font_medium = pygame.font.Font(None, 72)
        self.font_small = pygame.font.Font(None, 36)
        
        # Define the base arena square.
        self.base_arena = (ARENA_MARGIN, ARENA_MARGIN, ARENA_WIDTH, ARENA_HEIGHT)
        self.arena_bounds = list(self.base_arena)
        self.arena_shrink_timer = ARENA_SHRINK_INTERVAL * FPS
        
        # Use neon colors for fighters
        spawn_margin = 100
        center_y = SCREEN_HEIGHT // 2
        self.blue = Fighter(ARENA_MARGIN + spawn_margin, center_y, 
                            NEON_BLUE, (100, 255, 255), is_blue=True)
        self.red = Fighter(SCREEN_WIDTH - ARENA_MARGIN - spawn_margin, center_y, 
                            NEON_RED, (255, 100, 120), is_blue=False)
        
        # Lock fighters for countdown
        self._lock_fighters_for_countdown()
        
        # Visual effect systems.
        self.particles = ParticleSystem()
        self.shockwaves = ShockwaveSystem()
        self.arena_pulses = ArenaPulseSystem()
        self.damage_numbers = DamageNumberSystem()
        
        # Chaos Manager for TikTok Brainrot events
        self.chaos = ChaosManager()
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
        
        # Attack range for triggering combos
        self.attack_trigger_range = 120  # Distance to trigger attack
        
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
        
        # Pre-fight countdown
        self.countdown_stage = 0
        self.countdown_timer = 0
        self.countdown_active = True
        self.countdown_texts = ["3", "2", "1", "FIGHT"]
        self.countdown_duration = 45
        self.fight_duration = 30
        
        # Arena Escalation System
        self.inactivity_timer = 0
        self.escalation_state = 'normal'
        self.escalation_shrink_paused = False
        
        # Game State
        self.game_state = 'TITLE'
        
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
        """Unlock fighters with random velocity."""
        self.blue.locked = False
        self.red.locked = False
        self.blue.vx = random.uniform(-6, 6)
        self.blue.vy = random.uniform(-6, 6)
        self.red.vx = random.uniform(-6, 6)
        self.red.vy = random.uniform(-6, 6)
    
    def _reset_inactivity(self):
        """Reset inactivity timer."""
        self.inactivity_timer = 0
        if self.escalation_state == 'shrinking':
            self.escalation_shrink_paused = True
    
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
            base_path = os.path.join(os.path.dirname(__file__), "assets", "audio")
            
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
        """Check if sword tip hits defender body during attack."""
        if not attacker.is_attacking:
            return None
        
        (base_x, base_y), (tip_x, tip_y) = attacker.get_sword_hitbox()
        
        # Check multiple points along sword
        for t in [0.5, 0.75, 1.0]:
            check_x = base_x + (tip_x - base_x) * t
            check_y = base_y + (tip_y - base_y) * t
            dist = math.hypot(check_x - defender.x, check_y - defender.y)
            # Use current_radius for proper chaos event sizing
            if dist < defender.current_radius + 8:
                return (check_x, check_y)
        return None

    def _handle_combat(self):
        """Detect and resolve combat interactions."""
        
        # AI Attack Triggering - fighters attack when in range
        for attacker, defender in [(self.blue, self.red), (self.red, self.blue)]:
            dist = math.hypot(attacker.x - defender.x, attacker.y - defender.y)
            
            # Trigger attack when in range and not on cooldown
            if dist < self.attack_trigger_range:
                attacker.start_attack(self.round_timer)
        
        # Check for sword hits during attacks
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
                knockback = BASE_KNOCKBACK * knockback_mult * (1.0 + (total_damage_mult - 1.0) * 0.5)
                damage = DAMAGE_PER_HIT * total_damage_mult
                
                # ULTRA KNOCKBACK: Massive screen shake + knockback whoosh
                if self.chaos.is_ultra_knockback():
                    self.screen_shake = max(self.screen_shake, SCREEN_SHAKE_INTENSITY * 3)
                    if self.sounds_enabled and self.knockback_whoosh_sound:
                        self.knockback_whoosh_sound.play()
                
                # Pierce (combo stage 2) has more hit-stop
                hit_stop_frames = HIT_STOP_FRAMES + (2 if attacker.combo_stage == 2 else 0)
                
                if defender.take_damage(damage, angle, knockback, self.particles):
                    self._trigger_hit(hit_pos[0], hit_pos[1], attacker.render_color, hit_stop_frames, damage, is_crit)
                    self.hit_slowmo_frames = HIT_SLOWMO_FRAMES
                    attacker.on_attack_hit(self.round_timer)
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
        self.reset_timer = 300
        
        if winner == self.blue:
            self.winner_text = "BLUE WINS"
        else:
            self.winner_text = "RED WINS"
        
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
        self.arena_shrink_timer = ARENA_SHRINK_INTERVAL * FPS
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
        self.escalation_state = 'normal'
        self.escalation_shrink_paused = False
        
        self._lock_fighters_for_countdown()
        self.countdown_stage = 0
        self.countdown_timer = 0
        self.countdown_active = True
        
        # Reset countdown and death sound state
        self.countdown_beep_played = [False, False, False]
        self.fight_sound_played = False
        self.death_sound_phase = 0

    def update(self):
        """Main update loop."""
        if self.paused:
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
            if self.death_sound_phase == 1 and self.reset_timer < 260:
                self.death_sound_phase = 2
                if self.sounds_enabled and self.sword_to_ground_sound:
                    self.sword_to_ground_sound.play()
            
            if self.reset_timer <= 0:
                self._reset_round()
            self.particles.update()
            self.shockwaves.update()
            self.arena_pulses.update()
            return
        
        self.round_timer += 1
        
        # Arena Escalation
        self.inactivity_timer += 1
        
        if self.escalation_state == 'normal':
            if self.inactivity_timer >= INACTIVITY_PULSE_TIME * FPS:
                self._trigger_arena_pulse()
                self.escalation_state = 'pulse_triggered'
                self.inactivity_timer = 0
        
        elif self.escalation_state == 'pulse_triggered':
            if self.inactivity_timer >= INACTIVITY_SHRINK_TIME * FPS:
                self.escalation_state = 'shrinking'
                self.escalation_shrink_paused = False
                self._start_escalation_sound()  # Start shrink warning loop
        
        elif self.escalation_state == 'shrinking':
            if not self.escalation_shrink_paused:
                ax, ay, aw, ah = self.arena_bounds
                if aw > 250 and ah > 250:
                    self.arena_bounds = [
                        ax + ESCALATION_SHRINK_SPEED,
                        ay + ESCALATION_SHRINK_SPEED,
                        aw - ESCALATION_SHRINK_SPEED * 2,
                        ah - ESCALATION_SHRINK_SPEED * 2
                    ]
                else:
                    self._stop_escalation_sound()  # Stop when minimum size reached
            else:
                if self.inactivity_timer >= FPS * 2:
                    self.escalation_shrink_paused = False
        
        self.arena_shrink_timer -= 1
        if self.arena_shrink_timer <= 0:
            self.arena_shrink_timer = ARENA_SHRINK_INTERVAL * FPS
            ax, ay, aw, ah = self.arena_bounds
            if aw > 300 and ah > 300:
                self.arena_bounds = [
                    ax + ARENA_SHRINK_AMOUNT,
                    ay + ARENA_SHRINK_AMOUNT,
                    aw - ARENA_SHRINK_AMOUNT * 2,
                    ah - ARENA_SHRINK_AMOUNT * 2
                ]
        
        # ===== CHAOS SYSTEM UPDATE =====
        dt = 1.0 / FPS
        prev_event = self.chaos.active_event  # Track for sound trigger
        self.chaos.update(dt, self.particles, [self.blue, self.red])
        
        # Trigger chaos event sound when new event starts
        current_event = self.chaos.active_event
        if current_event and current_event != prev_event:
            self._play_chaos_event_sound(current_event)
        elif prev_event and not current_event:
            # Event ended, stop any loops
            self._stop_chaos_loops()
        
        # Get chaos modifiers
        speed_mult = self.chaos.get_speed_mult()
        body_size_mult = self.chaos.get_body_size_mult()
        sword_size_mult = self.chaos.get_sword_size_mult()
        attack_speed_mult = self.chaos.get_attack_speed_mult()
        center_x = SCREEN_WIDTH // 2
        center_y = SCREEN_HEIGHT // 2
        
        # Apply chaos modifiers to fighters
        for fighter in [self.blue, self.red]:
            # Apply separate body and sword size multipliers
            fighter.body_size_multiplier = body_size_mult
            fighter.sword_size_multiplier = sword_size_mult
            
            # Apply attack speed multiplier
            fighter.attack_speed_multiplier = attack_speed_mult
            
            # Apply speed multiplier
            fighter.speed_multiplier = speed_mult
            
            # Apply chaos color overrides
            fighter.render_color = self.chaos.get_fighter_color(fighter.color, fighter.is_blue)
            fighter.render_color_bright = self.chaos.get_fighter_color(fighter.color_bright, fighter.is_blue)
            
            # Apply health bar color (BLACK during Blackout)
            fighter.health_bar_color = self.chaos.get_health_bar_color(fighter.color)
            
            # Apply speed multiplier to velocity (acceleration boost when entering HYPER SPEED)
            if speed_mult != 1.0:
                fighter.vx *= (1.0 + (speed_mult - 1.0) * 0.15)
                fighter.vy *= (1.0 + (speed_mult - 1.0) * 0.15)
        
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
        
        if self.round_timer > ROUND_MAX_TIME * FPS:
            cx = SCREEN_WIDTH // 2
            cy = SCREEN_HEIGHT // 2
            blue_dist = math.hypot(self.blue.x - cx, self.blue.y - cy)
            red_dist = math.hypot(self.red.x - cx, self.red.y - cy)
            if blue_dist < red_dist:
                self._end_round(winner=self.blue, loser=self.red)
            else:
                self._end_round(winner=self.red, loser=self.blue)
    
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
        
        # Arena border
        if self.chaos.active_event in ["THE CRUSHER", "BREATHING ROOM"]:
            border_color = NEON_RED if not self.chaos.is_blackout() else BLACK
            border_width = 6
        elif self.escalation_state == 'shrinking':
            border_color = NEON_RED
            border_width = 6
        elif self.escalation_state == 'pulse_triggered':
            border_color = YELLOW
            border_width = 5
        elif self.chaos.is_tron_mode():
            border_color = NEON_BLUE
            border_width = 6
        else:
            border_color = NEON_BLUE if not self.chaos.is_blackout() else GRAY
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
                border_color = NEON_BLUE
            else:
                text_surface = self.font_large.render(countdown_text, True, WHITE)
                border_color = NEON_RED
            
            text_rect = text_surface.get_rect(center=(SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2))
            
            bg_rect = text_rect.inflate(50, 30)
            pygame.draw.rect(self.screen, NEON_BG, bg_rect)
            pygame.draw.rect(self.screen, border_color, bg_rect, 4)
            
            self.screen.blit(text_surface, text_rect)
        
        # Winner UI Announcement
        # Wait until after death animation (when reset_timer < 240, i.e., after 1 second)
        if self.round_ending and self.winner_text and self.reset_timer < 240:
            winner_surface = self.font_large.render(self.winner_text, True, WHITE)
            winner_rect = winner_surface.get_rect(center=(SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2))
            
            border_color = NEON_BLUE if "BLUE" in self.winner_text else NEON_RED
            
            # Pulsing box effect
            pulse = abs(math.sin(self.reset_timer * 0.05))
            bg_rect = winner_rect.inflate(60 + 30 * pulse, 40 + 30 * pulse)
            
            # Give UI text a dark backing
            pygame.draw.rect(self.screen, NEON_BG, bg_rect)
            pygame.draw.rect(self.screen, border_color, bg_rect, max(4, int(6 + 4 * pulse)))
            
            self.screen.blit(winner_surface, winner_rect)
        
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
                pygame.draw.line(self.screen, NEON_BLUE,
                               (int(x1 + ox), int(y1 + oy)),
                               (int(x2 + ox), int(y2 + oy)), 4)
        
        # Draw red fighter's trail in neon red
        red_trail = trails.get('red', [])
        if len(red_trail) >= 2:
            for i in range(1, len(red_trail)):
                x1, y1 = red_trail[i-1]
                x2, y2 = red_trail[i]
                pygame.draw.line(self.screen, NEON_RED,
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
        pygame.draw.rect(glow_surf, (*NEON_BLUE, 60), glow_surf.get_rect())
        self.screen.blit(glow_surf, glow_rect)
        
        # Main wall
        pygame.draw.rect(self.screen, NEON_BLUE, wall_rect)

    def run(self):
        """Main loop."""
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
                        else:
                            self.paused = not self.paused
                    elif event.key == pygame.K_r:
                        self._reset_round()
                elif event.type == pygame.MOUSEBUTTONDOWN:
                    if self.game_state == 'TITLE':
                        self.game_state = 'PLAYING'
            
            if self.game_state == 'TITLE':
                self._draw_title_screen()
            else:
                self.update()
                self.draw()
            self.clock.tick(FPS)
        
        pygame.quit()


if __name__ == "__main__":
    game = Game()
    game.run()
