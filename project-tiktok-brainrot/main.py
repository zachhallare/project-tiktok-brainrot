import pygame
import math
import random

# Import constants and classes from other modules.
from config import (
    SCREEN_WIDTH, SCREEN_HEIGHT, FPS,
    BLUE, BLUE_BRIGHT, RED, RED_BRIGHT, WHITE, PURPLE, BLACK, DARK_GRAY, GRAY,
    YELLOW, GOLD, ORANGE,
    ARENA_MARGIN, ARENA_WIDTH, ARENA_HEIGHT,
    ARENA_SHRINK_INTERVAL, ARENA_SHRINK_AMOUNT,
    POWERUP_SPAWN_MIN, POWERUP_SPAWN_MAX, MAX_POWERUPS,
    ROUND_MAX_TIME, BASE_KNOCKBACK, DAMAGE_PER_HIT, SLOW_MOTION_SPEED,
    HIT_STOP_FRAMES, SCREEN_SHAKE_INTENSITY, SCREEN_SHAKE_DECAY,
    PARRY_SLOWMO_FRAMES, PARRY_SLOWMO_TIMESCALE, PARRY_HITSTOP_FRAMES,
    INACTIVITY_PULSE_TIME, INACTIVITY_SHRINK_TIME, ARENA_PULSE_VELOCITY_BOOST,
    ARENA_PULSE_SHAKE, ESCALATION_SHRINK_SPEED, GAME_SETTINGS
)
from effects import ParticleSystem, ShockwaveSystem, ArenaPulseSystem
from skills import SkillType, SkillOrb
from fighter import Fighter


# Main game class managing a 1v1 fighter battle in a shrinking square arena.
class Game:    
    def __init__(self):
        # Initialize pygame modules
        pygame.init()
        pygame.mixer.init()     # For sound.
        pygame.font.init()      # For text rendering.
        
        # Create the game window.
        self.screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
        pygame.display.set_caption("Red vs Blue Battle")
        self.clock = pygame.time.Clock()    # Controls frame rate.
        
        # Fonts for UI text (win message, countdown, etc.)
        self.font_large = pygame.font.Font(None, 120)  # Bigger for countdown
        self.font_medium = pygame.font.Font(None, 72)
        self.font_small = pygame.font.Font(None, 36)
        
        # Define the base arena square.
        self.base_arena = (ARENA_MARGIN, ARENA_MARGIN, ARENA_WIDTH, ARENA_HEIGHT)
        self.arena_bounds = list(self.base_arena)
        self.arena_shrink_timer = ARENA_SHRINK_INTERVAL * FPS
        
        # Spawn fighters on opposite sides of the arena
        spawn_margin = 100
        center_y = SCREEN_HEIGHT // 2
        self.blue = Fighter(ARENA_MARGIN + spawn_margin, center_y, 
                            BLUE, BLUE_BRIGHT, is_blue=True)
        self.red = Fighter(SCREEN_WIDTH - ARENA_MARGIN - spawn_margin, center_y, 
                            RED, RED_BRIGHT, is_blue=False)
        
        # Lock fighters for countdown (facing each other)
        self._lock_fighters_for_countdown()
        
        # Visual effect systems.
        self.particles = ParticleSystem()
        self.shockwaves = ShockwaveSystem()
        self.arena_pulses = ArenaPulseSystem()
        
        # Fighter power-up (skill orb) management.
        self.skill_orbs = []
        self.powerup_timer = random.uniform(POWERUP_SPAWN_MIN, POWERUP_SPAWN_MAX) * FPS
        
        # Screen effects.
        self.screen_shake = 0
        self.hit_stop = 0
        self.screen_black_frames = 0  # For Final Flash Draw
        self.parry_slowmo_frames = 0  # Parry slow-motion effect
        self.parry_slowmo_accumulator = 0.0
        
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
        
        # Pre-fight countdown: "3" -> "2" -> "1" -> "FIGHT"
        self.countdown_stage = 0  # 0=3, 1=2, 2=1, 3=FIGHT
        self.countdown_timer = 0
        self.countdown_active = True
        self.countdown_texts = ["3", "2", "1", "FIGHT"]
        self.countdown_duration = 45  # Frames per number (~0.75 seconds)
        self.fight_duration = 30  # FIGHT shows a bit shorter
        
        # Arena Escalation System (Inactivity Handling)
        self.inactivity_timer = 0  # Frames since last interaction
        self.escalation_state = 'normal'  # 'normal', 'pulse_triggered', 'shrinking'
        self.escalation_shrink_paused = False  # Paused when interaction occurs
        
        # Game State (TITLE, PLAYING, ROUND_END)
        self.game_state = 'TITLE'  # Start at title screen
        
        # Load/generated sounds.
        self._setup_sounds()
    
    def _lock_fighters_for_countdown(self):
        """Lock fighters in place and face each other for countdown."""
        self.blue.locked = True
        self.red.locked = True
        self.blue.vx = 0
        self.blue.vy = 0
        self.red.vx = 0
        self.red.vy = 0
        # Point swords at each other
        self.blue.sword_angle = 0  # Points right (toward red)
        self.red.sword_angle = math.pi  # Points left (toward blue)
    
    def _unlock_fighters(self):
        """Unlock fighters and give them initial velocity after countdown."""
        self.blue.locked = False
        self.red.locked = False
        # Give random starting velocities
        self.blue.vx = random.uniform(-6, 6)
        self.blue.vy = random.uniform(-6, 6)
        self.red.vx = random.uniform(-6, 6)
        self.red.vy = random.uniform(-6, 6)
    
    def _reset_inactivity(self):
        """Reset inactivity timer (called on combat interactions)."""
        self.inactivity_timer = 0
        if self.escalation_state == 'shrinking':
            self.escalation_shrink_paused = True
            # Don't reset state - just pause shrinking
    
    def _trigger_arena_pulse(self):
        """Trigger Tier 1 Arena Pulse - visual wave and fighter nudge."""
        # Visual effect
        self.arena_pulses.add(tuple(self.arena_bounds), PURPLE)
        self.screen_shake = ARENA_PULSE_SHAKE
        
        # Nudge both fighters toward center
        center_x = SCREEN_WIDTH // 2
        center_y = SCREEN_HEIGHT // 2
        
        for fighter in [self.blue, self.red]:
            dx = center_x - fighter.x
            dy = center_y - fighter.y
            dist = max(1, math.hypot(dx, dy))
            # Normalize and apply velocity boost toward center
            fighter.vx += (dx / dist) * ARENA_PULSE_VELOCITY_BOOST
            fighter.vy += (dy / dist) * ARENA_PULSE_VELOCITY_BOOST
            # Also increase overall speed slightly
            speed = math.hypot(fighter.vx, fighter.vy)
            if speed > 0:
                boost = 1.2
                fighter.vx *= boost
                fighter.vy *= boost
    

    # Generate simple procedural hit and explosion sounds.
    def _setup_sounds(self):
        try:
            sample_rate = 44100
            duration = 0.1      # Seconds for hit sound.
            
            # Generate a short decaying sine wave for punch/hit impact.
            t = [i / sample_rate for i in range(int(sample_rate * duration))]
            samples = []
            for i in t:
                freq = 200
                amp = 20000 * math.exp(-i * 25) * math.sin(2 * math.pi * freq * i)
                samples.append(int(max(-32768, min(32767, amp))))
            
            # Convert samples to byte buffer for pygame Sound.
            arr = bytes()
            for s in samples:
                arr += s.to_bytes(2, 'little', signed=True)
            
            self.hit_sound = pygame.mixer.Sound(buffer=arr)
            self.hit_sound.set_volume(0.4)
            
            # Generate explosion sound using noise with exponential decay.
            exp_dur = 0.25
            t_exp = [i / sample_rate for i in range(int(sample_rate * exp_dur))]
            exp_samples = []
            for i in t_exp:
                noise = random.uniform(-1, 1)
                amp = 25000 * math.exp(-i * 6) * noise
                exp_samples.append(int(max(-32768, min(32767, amp))))
            
            exp_arr = bytes()
            for s in exp_samples:
                exp_arr += s.to_bytes(2, 'little', signed=True)
            
            self.explosion_sound = pygame.mixer.Sound(buffer=exp_arr)
            self.explosion_sound.set_volume(0.5)
            
            # Generate metallic clang sound for parries (higher frequency, sharper decay)
            clang_dur = 0.08
            t_clang = [i / sample_rate for i in range(int(sample_rate * clang_dur))]
            clang_samples = []
            for i in t_clang:
                # Multiple frequencies for metallic ring
                freq1 = 800
                freq2 = 1200
                amp = 18000 * math.exp(-i * 40) * (
                    math.sin(2 * math.pi * freq1 * i) +
                    0.5 * math.sin(2 * math.pi * freq2 * i)
                )
                clang_samples.append(int(max(-32768, min(32767, amp))))
            
            clang_arr = bytes()
            for s in clang_samples:
                clang_arr += s.to_bytes(2, 'little', signed=True)
            
            self.clang_sound = pygame.mixer.Sound(buffer=clang_arr)
            self.clang_sound.set_volume(0.5)
            
            self.sounds_enabled = True
        except Exception:
            self.sounds_enabled = False
    

    # Spawn a random skill orb (power-up) inside the current arena bounds.
    def _spawn_skill_orb(self):
        if len(self.skill_orbs) >= MAX_POWERUPS:
            return      # Don't exceed max power-ups on screen.
        
        ax, ay, aw, ah = self.arena_bounds
        margin = 60     # To avoid spawning too close to edges.
        x = random.randint(int(ax + margin), int(ax + aw - margin))
        y = random.randint(int(ay + margin), int(ay + ah - margin))
        
        # 7 skill types now (0-6), with Final Flash Draw being rare
        if random.random() < 0.1:  # 10% chance for Final Flash Draw
            skill_type = SkillType.FINAL_FLASH_DRAW
        else:
            skill_type = random.randint(0, 5)  # Other 6 skills
        self.skill_orbs.append(SkillOrb(x, y, skill_type))
    

    # Check if attacker's sword tip intersects defender's body.
    def _check_sword_hit(self, attacker, defender):
        (base_x, base_y), (tip_x, tip_y) = attacker.get_sword_hitbox()
        
        # Sample 3 points along the sword line for more accurate collision
        for t in [0.4, 0.7, 1.0]:
            check_x = base_x + (tip_x - base_x) * t
            check_y = base_y + (tip_y - base_y) * t
            dist = math.hypot(check_x - defender.x, check_y - defender.y)
            if dist < defender.radius + 8:
                return (check_x, check_y)
        return None
    

    # Detect and resolve sword attacks and skill-specific damage.
    def _handle_combat(self):
        # ===== Check for Sword-on-Sword Parry (new universal rule) =====
        if self.blue.check_sword_on_sword_parry(self.red):
            # Both swords collided during attacks!
            # No damage - both combos reset
            self._handle_sword_parry(self.blue, self.red)
            return  # Skip other combat this frame
        
        # ===== Check for Sword Clash (basic attack vs skill) =====
        for defender, attacker in [(self.blue, self.red), (self.red, self.blue)]:
            clashed_skill = defender.check_sword_clash(attacker, self.particles)
            if clashed_skill is not None:
                # Clash occurred! Apply skill-specific outcome
                self._handle_clash_outcome(defender, attacker, clashed_skill)
                self._reset_inactivity()
                self.hit_stop = 3  # Brief hit-stop for clash
                return  # Skip other combat this frame
        
        # ===== Check for Spin Parry (only when active) =====
        for defender, attacker in [(self.blue, self.red), (self.red, self.blue)]:
            if defender.check_spin_parry(attacker, self.particles):
                # Parry successful - trigger samurai slow-mo and effects
                self.hit_stop = PARRY_HITSTOP_FRAMES
                self.parry_slowmo_frames = PARRY_SLOWMO_FRAMES
                self.screen_shake = 5
                self._reset_inactivity()
                attacker.attack_cooldown = 30  # Punish attacker
                # Metallic clang
                if self.sounds_enabled and hasattr(self, 'clang_sound'):
                    self.clang_sound.play()
                return  # Skip other combat this frame after parry
        
        # Blue attacking Red.
        hit_blue = self._check_sword_hit(self.blue, self.red)
        if hit_blue and self.blue.attack_cooldown <= 0:
            # Check if Red's Spin Parry is in recovery (extra vulnerable)
            extra_damage = 1.3 if self.red.spin_parry_recovery > 0 else 1.0
            
            angle = math.atan2(self.red.y - self.blue.y, self.red.x - self.blue.x)
            knockback = BASE_KNOCKBACK
            damage = DAMAGE_PER_HIT * extra_damage
            hit_stop_frames = HIT_STOP_FRAMES
            
            # Skill-specific effects
            if self.blue.active_skill == SkillType.DASH_SLASH:
                knockback *= 1.8
                hit_stop_frames = 4  # Extra hit-stop
                # Flash both fighters
                self.blue.flash_timer = 4
            elif self.blue.active_skill == SkillType.SPIN_PARRY:
                knockback *= 1.3
            elif self.blue.active_skill == SkillType.BLADE_CYCLONE:
                knockback *= 0.5  # Less knockback, more hits
                damage *= 0.6
                hit_stop_frames = 2
            elif self.blue.active_skill == SkillType.FINAL_FLASH_DRAW:
                knockback *= 2.5
                damage *= 2.5
                hit_stop_frames = 8  # Big freeze
            
            if self.red.take_damage(damage, angle, knockback, self.particles):
                self._trigger_hit(hit_blue[0], hit_blue[1], self.blue.color, hit_stop_frames)
                self.blue.attack_cooldown = 18      # Prevent spam.
                self._reset_inactivity()  # Reset inactivity on hit
        
        # Red attacking Blue.
        hit_red = self._check_sword_hit(self.red, self.blue)
        if hit_red and self.red.attack_cooldown <= 0:
            # Check if Blue's Spin Parry is in recovery (extra vulnerable)
            extra_damage = 1.3 if self.blue.spin_parry_recovery > 0 else 1.0
            
            angle = math.atan2(self.blue.y - self.red.y, self.blue.x - self.red.x)
            knockback = BASE_KNOCKBACK
            damage = DAMAGE_PER_HIT * extra_damage
            hit_stop_frames = HIT_STOP_FRAMES
            
            if self.red.active_skill == SkillType.DASH_SLASH:
                knockback *= 1.8
                hit_stop_frames = 4
                self.red.flash_timer = 4
            elif self.red.active_skill == SkillType.SPIN_PARRY:
                knockback *= 1.3
            elif self.red.active_skill == SkillType.BLADE_CYCLONE:
                knockback *= 0.5
                damage *= 0.6
                hit_stop_frames = 2
            elif self.red.active_skill == SkillType.FINAL_FLASH_DRAW:
                knockback *= 2.5
                damage *= 2.5
                hit_stop_frames = 8
            
            if self.blue.take_damage(damage, angle, knockback, self.particles):
                self._trigger_hit(hit_red[0], hit_red[1], self.red.color, hit_stop_frames)
                self.red.attack_cooldown = 18
                self._reset_inactivity()  # Reset inactivity on hit
        
        # Ground slam area damage when skill impacts.
        for attacker, defender in [(self.blue, self.red), (self.red, self.blue)]:
            if (attacker.active_skill == SkillType.GROUND_SLAM and 
                attacker.skill_data.get('phase') == 'impact' and
                attacker.skill_timer == 23):    # Specific frame for impact.
                dist = math.hypot(defender.x - attacker.x, defender.y - attacker.y)
                if dist < 130:      # Slam radius.
                    angle = math.atan2(defender.y - attacker.y, defender.x - attacker.x)
                    if defender.take_damage(DAMAGE_PER_HIT * 1.5, angle, 18, self.particles):
                        self._trigger_hit(defender.x, defender.y, attacker.color, 5)
                        self._reset_inactivity()
            
            # Phantom Cross delayed damage
            if (attacker.active_skill == SkillType.PHANTOM_CROSS and
                attacker.skill_timer == attacker.skill_data.get('damage_frame', 12)):
                dist = math.hypot(defender.x - attacker.skill_data.get('target_pos', (0, 0))[0],
                                 defender.y - attacker.skill_data.get('target_pos', (0, 0))[1])
                if dist < 80:
                    angle = math.atan2(defender.y - attacker.y, defender.x - attacker.x)
                    if defender.take_damage(DAMAGE_PER_HIT * 1.8, angle, 15, self.particles):
                        self._trigger_hit(defender.x, defender.y, attacker.color, 5)
                        self._reset_inactivity()
        
        # Check for Final Flash Draw screen black trigger
        for fighter in [self.blue, self.red]:
            if fighter.trigger_screen_black:
                fighter.trigger_screen_black = False
                self.screen_black_frames = 3  # 3 frames of black
    

    # Apply visual and audio feedback when a successful hit lands.
    def _trigger_hit(self, x, y, color, hit_stop_frames=None):
        self.particles.emit(x, y, WHITE, count=10, size=4)
        self.hit_stop = hit_stop_frames if hit_stop_frames else HIT_STOP_FRAMES
        self.screen_shake = SCREEN_SHAKE_INTENSITY
        
        if self.sounds_enabled:
            self.hit_sound.play()
    
    def _handle_sword_parry(self, fighter1, fighter2):
        """Handle sword-on-sword parry - both fighters reset combo, no damage."""
        # Reset both combos
        fighter1.combo_step = 0
        fighter1.combo_timer = 0
        fighter1.combo_recovery = 8  # Brief stagger
        
        fighter2.combo_step = 0
        fighter2.combo_timer = 0
        fighter2.combo_recovery = 8
        
        # Visual feedback - white flash at midpoint between fighters (sword contact)
        mid_x = (fighter1.x + fighter2.x) / 2
        mid_y = (fighter1.y + fighter2.y) / 2
        self.particles.emit(mid_x, mid_y, WHITE, count=8, size=5, lifetime=10)
        
        # Both fighters flash
        fighter1.flash_timer = 4
        fighter2.flash_timer = 4
        
        # Parry slow-motion effect (samurai-style)
        self.hit_stop = PARRY_HITSTOP_FRAMES  # Small hit-stop stacked on slow-mo
        self.parry_slowmo_frames = PARRY_SLOWMO_FRAMES  # Then slow-mo
        self.screen_shake = 4
        
        # Audio feedback - metallic clang
        if self.sounds_enabled and hasattr(self, 'clang_sound'):
            self.clang_sound.play()
        elif self.sounds_enabled:
            self.hit_sound.play()  # Fallback
        
        self._reset_inactivity()
    
    def _handle_clash_outcome(self, defender, attacker, clashed_skill):
        """Handle skill-specific outcomes when basic attack clashes with skill."""
        # White flash for clash
        defender.flash_timer = 3
        self.screen_shake = 4
        
        if clashed_skill == SkillType.DASH_SLASH:
            # Deflected off-angle - change attacker's velocity direction
            angle = math.atan2(attacker.vy, attacker.vx)
            deflect_angle = angle + random.uniform(-0.8, 0.8)  # Random deflection
            speed = math.hypot(attacker.vx, attacker.vy)
            attacker.vx = math.cos(deflect_angle) * speed
            attacker.vy = math.sin(deflect_angle) * speed
            attacker.active_skill = None  # Cancel skill
        
        elif clashed_skill == SkillType.SPIN_PARRY:
            # Spin Parry dissipates when active (clash only works on active)
            if attacker.spin_parry_active:
                attacker.active_skill = None
                attacker.spin_parry_active = False
                attacker.spin_parry_recovery = 15  # Brief vulnerability
        
        elif clashed_skill == SkillType.GROUND_SLAM:
            # Shockwave reduced - reduce future impact damage
            attacker.skill_data['shockwave_reduced'] = True
        
        elif clashed_skill == SkillType.PHANTOM_CROSS:
            # Delayed damage canceled
            attacker.pending_damage = []
            attacker.active_skill = None
        
        elif clashed_skill == SkillType.BLADE_CYCLONE:
            # Pushback only - push defender away
            angle = math.atan2(defender.y - attacker.y, defender.x - attacker.x)
            defender.vx += math.cos(angle) * 8
            defender.vy += math.sin(angle) * 8
        
        # Final Flash Draw cannot be clashed (handled in check_sword_clash)

    # Handle round end: play effects, start slow-motion.
    def _end_round(self, winner, loser):
        self.round_ending = True
        self.winner = winner
        # No victory text - slow-motion death is the sole indicator
        self.reset_timer = 120  # 2 seconds
        
        # Dramatic death effects on loser.
        self.particles.emit_explosion(loser.x, loser.y, loser.color, count=40)
        self.shockwaves.add(loser.x, loser.y, loser.color, 100)
        winner.victory_bounce = 40      # Winner does a little bounce animation.
        
        # Slow-motion for dramatic finish.
        self.slow_motion = True
        self.slow_motion_accumulator = 0.0
        
        if self.sounds_enabled:
            self.explosion_sound.play()
    

    # Reset everything for a new round.
    def _reset_round(self):
        self.blue.reset()
        self.red.reset()
        self.skill_orbs.clear()
        self.arena_bounds = list(self.base_arena)
        self.arena_shrink_timer = ARENA_SHRINK_INTERVAL * FPS
        self.powerup_timer = random.uniform(POWERUP_SPAWN_MIN, POWERUP_SPAWN_MAX) * FPS
        self.round_ending = False
        self.winner = None
        self.winner_text = ""
        self.round_timer = 0
        self.particles.clear()
        self.shockwaves.clear()
        self.arena_pulses.clear()
        self.screen_black_frames = 0
        
        # End slow-motion.
        self.slow_motion = False
        self.slow_motion_accumulator = 0.0
        
        # Reset arena escalation.
        self.inactivity_timer = 0
        self.escalation_state = 'normal'
        self.escalation_shrink_paused = False
        
        # Lock fighters and restart countdown.
        self._lock_fighters_for_countdown()
        self.countdown_stage = 0
        self.countdown_timer = 0
        self.countdown_active = True
    

    # Main game logic update (called every frame).
    def update(self):
        if self.paused:
            return  # Skips updates when paused.
        
        # Countdown before fight starts: "3" -> "2" -> "1" -> "FIGHT"
        if self.countdown_active:
            self.countdown_timer += 1
            
            # Determine duration for current stage
            duration = self.fight_duration if self.countdown_stage == 3 else self.countdown_duration
            
            if self.countdown_timer >= duration:
                self.countdown_timer = 0
                self.countdown_stage += 1
                if self.countdown_stage > 3:
                    self.countdown_active = False
                    self._unlock_fighters()  # Unlock fighters after "FIGHT"
            return
        
        # Slow-motion handling (only during death sequence).
        if self.slow_motion and not self.round_ending:
            self.slow_motion = False
        
        if self.slow_motion:
            self.slow_motion_accumulator += SLOW_MOTION_SPEED
            if self.slow_motion_accumulator < 1.0:
                return
            self.slow_motion_accumulator -= 1.0
        
        # Screen black frames for Final Flash Draw
        if self.screen_black_frames > 0:
            self.screen_black_frames -= 1
        
        # Hit-stop freeze.
        if self.hit_stop > 0:
            self.hit_stop -= 1
            return
        
        # Parry slow-motion effect (samurai-style)
        # Physics continues at reduced timescale, not paused
        if self.parry_slowmo_frames > 0:
            self.parry_slowmo_accumulator += PARRY_SLOWMO_TIMESCALE
            self.parry_slowmo_frames -= 1
            if self.parry_slowmo_accumulator < 1.0:
                return  # Skip this frame
            self.parry_slowmo_accumulator -= 1.0
        
        # Decay screen shake.
        if self.screen_shake > 0:
            self.screen_shake *= SCREEN_SHAKE_DECAY
            if self.screen_shake < 0.5:
                self.screen_shake = 0
        
        # Round ending sequence.
        if self.round_ending:
            self.reset_timer -= 1
            if self.reset_timer <= 0:
                self._reset_round()
            self.particles.update()
            self.shockwaves.update()
            self.arena_pulses.update()
            return
        
        # Normal round progression.
        self.round_timer += 1
        
        # ===== Arena Escalation System =====
        self.inactivity_timer += 1
        
        # Tier 1: Arena Pulse (after 5 seconds of inactivity)
        if self.escalation_state == 'normal':
            if self.inactivity_timer >= INACTIVITY_PULSE_TIME * FPS:
                self._trigger_arena_pulse()
                self.escalation_state = 'pulse_triggered'
                self.inactivity_timer = 0
        
        # Tier 2: Shrinking Walls (continued inactivity after pulse)
        elif self.escalation_state == 'pulse_triggered':
            if self.inactivity_timer >= INACTIVITY_SHRINK_TIME * FPS:
                self.escalation_state = 'shrinking'
                self.escalation_shrink_paused = False
        
        # Active shrinking (paused on interaction)
        elif self.escalation_state == 'shrinking':
            if not self.escalation_shrink_paused:
                ax, ay, aw, ah = self.arena_bounds
                if aw > 250 and ah > 250:  # Don't shrink too small
                    self.arena_bounds = [
                        ax + ESCALATION_SHRINK_SPEED,
                        ay + ESCALATION_SHRINK_SPEED,
                        aw - ESCALATION_SHRINK_SPEED * 2,
                        ah - ESCALATION_SHRINK_SPEED * 2
                    ]
            else:
                # Resume shrinking after interaction pause
                if self.inactivity_timer >= FPS * 2:  # 2 second grace period
                    self.escalation_shrink_paused = False
        
        # Shrink arena periodically.
        self.arena_shrink_timer -= 1
        if self.arena_shrink_timer <= 0:
            self.arena_shrink_timer = ARENA_SHRINK_INTERVAL * FPS
            ax, ay, aw, ah = self.arena_bounds
            if aw > 300 and ah > 300:   # Don't strink too small.
                self.arena_bounds = [
                    ax + ARENA_SHRINK_AMOUNT,
                    ay + ARENA_SHRINK_AMOUNT,
                    aw - ARENA_SHRINK_AMOUNT * 2,
                    ah - ARENA_SHRINK_AMOUNT * 2
                ]
        
        # Spawn power-ups on timer.
        self.powerup_timer -= 1
        if self.powerup_timer <= 0:
            self._spawn_skill_orb()
            self.powerup_timer = random.uniform(POWERUP_SPAWN_MIN, POWERUP_SPAWN_MAX) * FPS
        
        # Update and check collisions for skill orbs.
        for orb in self.skill_orbs[:]:
            orb.update()
            if orb.check_collision(self.blue):
                self.blue.activate_skill(orb.skill_type, self.red, self.particles, self.shockwaves)
                # FFD: Stun opponent on activation
                if orb.skill_type == SkillType.FINAL_FLASH_DRAW:
                    self.red.ffd_stunned = True
                self.skill_orbs.remove(orb)
                self.particles.emit(orb.x, orb.y, orb.color, count=12, size=4)
            elif orb.check_collision(self.red):
                self.red.activate_skill(orb.skill_type, self.blue, self.particles, self.shockwaves)
                # FFD: Stun opponent on activation
                if orb.skill_type == SkillType.FINAL_FLASH_DRAW:
                    self.blue.ffd_stunned = True
                self.skill_orbs.remove(orb)
                self.particles.emit(orb.x, orb.y, orb.color, count=12, size=4)
        
        # Update both fighters (movement, skills, etc.)
        self.blue.update(self.red, tuple(self.arena_bounds), self.particles, self.shockwaves)
        self.red.update(self.blue, tuple(self.arena_bounds), self.particles, self.shockwaves)
        
        # FFD stun release: when user's lock-in ends, release opponent's stun
        if not self.blue.ffd_locked_in and self.red.ffd_stunned:
            self.red.ffd_stunned = False
        if not self.red.ffd_locked_in and self.blue.ffd_stunned:
            self.blue.ffd_stunned = False
        
        # Handle attacks and damage.
        self._handle_combat()
        
        # Update visual effects.
        self.particles.update()
        self.shockwaves.update()
        self.arena_pulses.update()
        
        # Check win by KO.
        if self.blue.health <= 0:
            self._end_round(winner=self.red, loser=self.blue)
        elif self.red.health <= 0:
            self._end_round(winner=self.blue, loser=self.red)
        
        # Timeout win condition: closest to center wins.
        if self.round_timer > ROUND_MAX_TIME * FPS:
            cx = SCREEN_WIDTH // 2
            cy = SCREEN_HEIGHT // 2
            blue_dist = math.hypot(self.blue.x - cx, self.blue.y - cy)
            red_dist = math.hypot(self.red.x - cx, self.red.y - cy)
            if blue_dist < red_dist:
                self._end_round(winner=self.blue, loser=self.red)
            else:
                self._end_round(winner=self.red, loser=self.blue)
    


    def _draw_title_screen(self):
        """Draw Pygame-only title screen."""
        self.screen.fill(DARK_GRAY)
        
        # Draw arena preview
        ax, ay, aw, ah = self.base_arena
        arena_rect = pygame.Rect(int(ax), int(ay), int(aw), int(ah))
        pygame.draw.rect(self.screen, BLACK, arena_rect)
        pygame.draw.rect(self.screen, GRAY, arena_rect, 4)
        
        # Title
        title_text = "RED vs BLUE"
        title_surface = self.font_large.render(title_text, True, WHITE)
        title_rect = title_surface.get_rect(center=(SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2 - 80))
        
        # Title shadow
        shadow_surface = self.font_large.render(title_text, True, (50, 50, 50))
        shadow_rect = shadow_surface.get_rect(center=(SCREEN_WIDTH // 2 + 3, SCREEN_HEIGHT // 2 - 77))
        self.screen.blit(shadow_surface, shadow_rect)
        self.screen.blit(title_surface, title_rect)
        
        # Subtitle
        subtitle = "BATTLE"
        subtitle_surface = self.font_medium.render(subtitle, True, YELLOW)
        subtitle_rect = subtitle_surface.get_rect(center=(SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2 - 10))
        self.screen.blit(subtitle_surface, subtitle_rect)
        
        # Start prompt (blinking effect)
        if (pygame.time.get_ticks() // 500) % 2 == 0:
            prompt = "Press SPACE or CLICK to Start"
            prompt_surface = self.font_small.render(prompt, True, WHITE)
            prompt_rect = prompt_surface.get_rect(center=(SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2 + 80))
            self.screen.blit(prompt_surface, prompt_rect)
        
        # Controls hint
        controls = "SPACE: Pause  |  R: Reset  |  ESC: Exit"
        controls_surface = self.font_small.render(controls, True, GRAY)
        controls_rect = controls_surface.get_rect(center=(SCREEN_WIDTH // 2, SCREEN_HEIGHT - 40))
        self.screen.blit(controls_surface, controls_rect)
        
        pygame.display.flip()

    # Render everything to the screen.
    def draw(self):
        # Screen black for Final Flash Draw
        if self.screen_black_frames > 0:
            self.screen.fill(BLACK)
            pygame.display.flip()
            return
        
        # Screen shake offset.
        offset = (0, 0)
        if self.screen_shake > 0:
            offset = (random.uniform(-self.screen_shake, self.screen_shake),
                     random.uniform(-self.screen_shake, self.screen_shake))
        
        # Dark background.
        self.screen.fill(DARK_GRAY)
        
        # Draw shrinking arena border with escalation indicator.
        ax, ay, aw, ah = self.arena_bounds
        arena_rect = pygame.Rect(int(ax + offset[0]), int(ay + offset[1]), int(aw), int(ah))
        pygame.draw.rect(self.screen, BLACK, arena_rect)
        
        # Border color changes based on escalation state
        if self.escalation_state == 'shrinking':
            border_color = ORANGE  # Warning: arena is shrinking!
            border_width = 6
        elif self.escalation_state == 'pulse_triggered':
            border_color = YELLOW  # Caution: shrinking soon
            border_width = 5
        else:
            border_color = GRAY
            border_width = 4
        pygame.draw.rect(self.screen, border_color, arena_rect, border_width)
        
        # Draw arena pulse effects.
        self.arena_pulses.draw(self.screen, offset)
        
        # Draw effects in correct order.
        self.shockwaves.draw(self.screen, offset)
        
        # Draw power-ups.
        for orb in self.skill_orbs:
            orb.draw(self.screen, offset)
        
        # Draw fighters (hide loser during death animation for drama).
        if not self.round_ending or self.winner == self.blue:
            self.blue.draw(self.screen, offset)
        if not self.round_ending or self.winner == self.red:
            self.red.draw(self.screen, offset)
        
        # Particles on top.
        self.particles.draw(self.screen, offset)
        
        # Victory is now indicated solely by slow-motion death sequence
        # No text overlay
        
        # Draw countdown "3" -> "2" -> "1" -> "FIGHT"
        if self.countdown_active:
            countdown_text = self.countdown_texts[self.countdown_stage]
            
            # Use larger font for numbers, medium for FIGHT
            if countdown_text == "FIGHT":
                text_surface = self.font_medium.render(countdown_text, True, WHITE)
                border_color = YELLOW
            else:
                text_surface = self.font_large.render(countdown_text, True, WHITE)
                border_color = PURPLE
            
            text_rect = text_surface.get_rect(center=(SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2))
            
            # Background box
            bg_rect = text_rect.inflate(50, 30)
            pygame.draw.rect(self.screen, BLACK, bg_rect)
            pygame.draw.rect(self.screen, border_color, bg_rect, 4)
            
            self.screen.blit(text_surface, text_rect)
        
        pygame.display.flip()
    

    # Main game loop.
    def run(self):
        running = True
        while running:
            # Event handling
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    running = False
                elif event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_ESCAPE:
                        running = False
                    elif event.key == pygame.K_SPACE:
                        if self.game_state == 'TITLE':
                            # Start game from title screen
                            self.game_state = 'PLAYING'
                        else:
                            self.paused = not self.paused
                    elif event.key == pygame.K_r:
                        self._reset_round()
                elif event.type == pygame.MOUSEBUTTONDOWN:
                    # Also allow mouse click to start from title
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
