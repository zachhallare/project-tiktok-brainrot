import pygame
import math
import random

# Import constants and classes from other modules.
from config import (
    SCREEN_WIDTH, SCREEN_HEIGHT, FPS,
    BLUE, BLUE_BRIGHT, RED, RED_BRIGHT, WHITE, PURPLE, BLACK, DARK_GRAY, GRAY,
    YELLOW, ORANGE,
    ARENA_MARGIN, ARENA_WIDTH, ARENA_HEIGHT,
    ARENA_SHRINK_INTERVAL, ARENA_SHRINK_AMOUNT,
    POWERUP_SPAWN_MIN, POWERUP_SPAWN_MAX, MAX_POWERUPS,
    ROUND_MAX_TIME, BASE_KNOCKBACK, DAMAGE_PER_HIT, SLOW_MOTION_SPEED,
    HIT_STOP_FRAMES, SCREEN_SHAKE_INTENSITY, SCREEN_SHAKE_DECAY,
    PARRY_SLOWMO_FRAMES, PARRY_SLOWMO_TIMESCALE, PARRY_HITSTOP_FRAMES,
    HIT_SLOWMO_FRAMES, HIT_SLOWMO_TIMESCALE,
    INACTIVITY_PULSE_TIME, INACTIVITY_SHRINK_TIME, ARENA_PULSE_VELOCITY_BOOST,
    ARENA_PULSE_SHAKE, ESCALATION_SHRINK_SPEED, GAME_SETTINGS,
    ROTATION_BODY_HIT_BONUS
)
from effects import ParticleSystem, ShockwaveSystem, ArenaPulseSystem
from skills import SkillType, SkillOrb
from fighter import Fighter


# Main game class - DVD logo style combat with rotating swords.
class Game:    
    def __init__(self):
        # Initialize pygame modules
        pygame.init()
        pygame.mixer.init()
        pygame.font.init()
        
        # Create the game window.
        self.screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
        pygame.display.set_caption("Red vs Blue Battle")
        self.clock = pygame.time.Clock()
        
        # Fonts for UI text
        self.font_large = pygame.font.Font(None, 120)
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
        
        # Lock fighters for countdown
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
        self.parry_slowmo_frames = 0
        self.parry_slowmo_accumulator = 0.0
        self.hit_slowmo_frames = 0
        self.hit_slowmo_accumulator = 0.0
        
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
        """Generate procedural sounds."""
        try:
            sample_rate = 44100
            duration = 0.1
            
            # Hit sound
            t = [i / sample_rate for i in range(int(sample_rate * duration))]
            samples = []
            for i in t:
                freq = 200
                amp = 20000 * math.exp(-i * 25) * math.sin(2 * math.pi * freq * i)
                samples.append(int(max(-32768, min(32767, amp))))
            
            arr = bytes()
            for s in samples:
                arr += s.to_bytes(2, 'little', signed=True)
            
            self.hit_sound = pygame.mixer.Sound(buffer=arr)
            self.hit_sound.set_volume(0.4)
            
            # Explosion sound
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
            
            # Clang sound for parries
            clang_dur = 0.08
            t_clang = [i / sample_rate for i in range(int(sample_rate * clang_dur))]
            clang_samples = []
            for i in t_clang:
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

    def _spawn_skill_orb(self):
        """Spawn a random skill orb."""
        if len(self.skill_orbs) >= MAX_POWERUPS:
            return
        
        ax, ay, aw, ah = self.arena_bounds
        margin = 60
        x = random.randint(int(ax + margin), int(ax + aw - margin))
        y = random.randint(int(ay + margin), int(ay + ah - margin))
        
        # Only 5 skills
        SELECTED_SKILLS = [0, 1, 2, 3, 4]
        skill_type = random.choice(SELECTED_SKILLS)
        self.skill_orbs.append(SkillOrb(x, y, skill_type))

    def _check_sword_hit(self, attacker, defender):
        """Check if sword tip hits defender body."""
        (base_x, base_y), (tip_x, tip_y) = attacker.get_sword_hitbox()
        
        for t in [0.4, 0.7, 1.0]:
            check_x = base_x + (tip_x - base_x) * t
            check_y = base_y + (tip_y - base_y) * t
            dist = math.hypot(check_x - defender.x, check_y - defender.y)
            if dist < defender.radius + ROTATION_BODY_HIT_BONUS:
                return (check_x, check_y)
        return None

    def _handle_combat(self):
        """Detect and resolve combat interactions."""
        
        # Check for Sword-on-Sword Parry (both rotating)
        if self.blue.check_sword_on_sword_parry(self.red):
            self._handle_sword_parry(self.blue, self.red)
            return
        
        # Check for Sword Clash (rotation vs skill)
        for defender, attacker in [(self.blue, self.red), (self.red, self.blue)]:
            clashed_skill = defender.check_sword_clash(attacker, self.particles)
            if clashed_skill is not None:
                self._handle_clash_outcome(defender, attacker, clashed_skill)
                self._reset_inactivity()
                self.hit_stop = 3
                return
        
        # Check for Spin Parry
        for defender, attacker in [(self.blue, self.red), (self.red, self.blue)]:
            if defender.check_spin_parry(attacker, self.particles):
                self.hit_stop = PARRY_HITSTOP_FRAMES
                self.parry_slowmo_frames = PARRY_SLOWMO_FRAMES
                self.screen_shake = 5
                self._reset_inactivity()
                if self.sounds_enabled:
                    self.clang_sound.play()
                return
        
        # Rotation Sword vs Body Hits
        for attacker, defender in [(self.blue, self.red), (self.red, self.blue)]:
            if attacker.active_skill is not None:
                continue
            if attacker.attack_cooldown > 0:
                continue
            if attacker.attack_recovery > 0:
                continue
            
            hit_pos = self._check_sword_hit(attacker, defender)
            if hit_pos:
                if defender.has_shield:
                    defender.has_shield = False
                    if defender.shield_parry_window > 0:
                        self.particles.emit_sparks(defender.x, defender.y)
                        defender.flash_timer = 8
                    else:
                        self.particles.emit(defender.x, defender.y, (100, 255, 150), count=10, size=4)
                    attacker.on_attack_blocked()
                    self._reset_inactivity()
                    continue
                
                extra_damage = 1.3 if defender.spin_parry_recovery > 0 else 1.0
                
                angle = math.atan2(defender.y - attacker.y, defender.x - attacker.x)
                knockback = BASE_KNOCKBACK
                damage = DAMAGE_PER_HIT * extra_damage
                hit_stop_frames = HIT_STOP_FRAMES
                
                if attacker.active_skill == SkillType.DASH_SLASH:
                    knockback *= 1.8
                    hit_stop_frames = 4
                    attacker.flash_timer = 4
                elif attacker.active_skill == SkillType.SPIN_PARRY:
                    knockback *= 1.3
                elif attacker.active_skill == SkillType.BLADE_CYCLONE:
                    knockback *= 0.5
                    damage *= 0.6
                    hit_stop_frames = 2
                
                if defender.take_damage(damage, angle, knockback, self.particles):
                    self._trigger_hit(hit_pos[0], hit_pos[1], attacker.color, hit_stop_frames)
                    self.hit_slowmo_frames = HIT_SLOWMO_FRAMES
                    attacker.on_rotation_hit(hit_sword=False, frame_count=self.round_timer)
                    attacker.attack_cooldown = 18
                    self._reset_inactivity()
        
        # Ground slam area damage
        for attacker, defender in [(self.blue, self.red), (self.red, self.blue)]:
            if (attacker.active_skill == SkillType.GROUND_SLAM and 
                attacker.skill_data.get('phase') == 'impact' and
                attacker.skill_timer == 23):
                dist = math.hypot(defender.x - attacker.x, defender.y - attacker.y)
                if dist < 130:
                    angle = math.atan2(defender.y - attacker.y, defender.x - attacker.x)
                    if defender.take_damage(DAMAGE_PER_HIT * 1.5, angle, 18, self.particles):
                        self._trigger_hit(defender.x, defender.y, attacker.color, 5)
                        self.hit_slowmo_frames = HIT_SLOWMO_FRAMES
                        self._reset_inactivity()

    def _trigger_hit(self, x, y, color, hit_stop_frames=None):
        """Apply hit effects."""
        self.particles.emit(x, y, WHITE, count=10, size=4)
        self.hit_stop = hit_stop_frames if hit_stop_frames else HIT_STOP_FRAMES
        self.screen_shake = SCREEN_SHAKE_INTENSITY
        
        if self.sounds_enabled:
            self.hit_sound.play()
    
    def _handle_sword_parry(self, fighter1, fighter2):
        """Handle sword-on-sword parry."""
        mid_x = (fighter1.x + fighter2.x) / 2
        mid_y = (fighter1.y + fighter2.y) / 2
        
        self.particles.emit(mid_x, mid_y, WHITE, count=12, size=5, lifetime=10)
        self.particles.emit_sparks(mid_x, mid_y)
        
        fighter1.on_rotation_hit(hit_sword=True, frame_count=self.round_timer)
        fighter2.on_rotation_hit(hit_sword=True, frame_count=self.round_timer)
        
        fighter1.attack_cooldown = 15
        fighter2.attack_cooldown = 15
        
        dx = fighter2.x - fighter1.x
        dy = fighter2.y - fighter1.y
        dist = max(1, math.hypot(dx, dy))
        push_force = 8
        
        fighter1.vx -= (dx / dist) * push_force
        fighter1.vy -= (dy / dist) * push_force
        fighter2.vx += (dx / dist) * push_force
        fighter2.vy += (dy / dist) * push_force
        
        self.hit_stop = PARRY_HITSTOP_FRAMES
        self.parry_slowmo_frames = PARRY_SLOWMO_FRAMES
        self.screen_shake = 6
        
        self._reset_inactivity()
        
        if self.sounds_enabled:
            self.clang_sound.play()
    
    def _handle_clash_outcome(self, defender, attacker, skill_type):
        """Handle skill vs rotation clash."""
        if skill_type == SkillType.BLADE_CYCLONE:
            self.particles.emit_sparks(defender.x, defender.y)
            attacker.on_rotation_hit(hit_sword=True, frame_count=self.round_timer)
            attacker.attack_cooldown = 20
        elif skill_type == SkillType.SPIN_PARRY:
            defender.skill_data['parried'] = True

    def _end_round(self, winner, loser):
        """Handle round end."""
        self.round_ending = True
        self.winner = winner
        self.reset_timer = 120
        
        self.particles.emit_explosion(loser.x, loser.y, loser.color, count=40)
        self.shockwaves.add(loser.x, loser.y, loser.color, 100)
        winner.victory_bounce = 40
        
        self.slow_motion = True
        self.slow_motion_accumulator = 0.0
        
        if self.sounds_enabled:
            self.explosion_sound.play()

    def _reset_round(self):
        """Reset round."""
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
        
        self.slow_motion = False
        self.slow_motion_accumulator = 0.0
        self.hit_slowmo_frames = 0
        self.hit_slowmo_accumulator = 0.0
        self.parry_slowmo_frames = 0
        self.parry_slowmo_accumulator = 0.0
        
        self.inactivity_timer = 0
        self.escalation_state = 'normal'
        self.escalation_shrink_paused = False
        
        self._lock_fighters_for_countdown()
        self.countdown_stage = 0
        self.countdown_timer = 0
        self.countdown_active = True

    def update(self):
        """Main update loop."""
        if self.paused:
            return
        
        if self.countdown_active:
            self.countdown_timer += 1
            duration = self.fight_duration if self.countdown_stage == 3 else self.countdown_duration
            
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
        
        if self.parry_slowmo_frames > 0:
            self.parry_slowmo_accumulator += PARRY_SLOWMO_TIMESCALE
            self.parry_slowmo_frames -= 1
            if self.parry_slowmo_accumulator < 1.0:
                return
            self.parry_slowmo_accumulator -= 1.0
        
        if self.hit_slowmo_frames > 0:
            self.hit_slowmo_accumulator += HIT_SLOWMO_TIMESCALE
            self.hit_slowmo_frames -= 1
            if self.hit_slowmo_accumulator < 1.0:
                return
            self.hit_slowmo_accumulator -= 1.0
        
        if self.screen_shake > 0:
            self.screen_shake *= SCREEN_SHAKE_DECAY
            if self.screen_shake < 0.5:
                self.screen_shake = 0
        
        if self.round_ending:
            self.reset_timer -= 1
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
        
        self.powerup_timer -= 1
        if self.powerup_timer <= 0:
            self._spawn_skill_orb()
            self.powerup_timer = random.uniform(POWERUP_SPAWN_MIN, POWERUP_SPAWN_MAX) * FPS
        
        for orb in self.skill_orbs[:]:
            orb.update()
            if orb.check_collision(self.blue):
                self.blue.activate_skill(orb.skill_type, self.red, self.particles, self.shockwaves)
                self.skill_orbs.remove(orb)
                self.particles.emit(orb.x, orb.y, orb.color, count=12, size=4)
            elif orb.check_collision(self.red):
                self.red.activate_skill(orb.skill_type, self.blue, self.particles, self.shockwaves)
                self.skill_orbs.remove(orb)
                self.particles.emit(orb.x, orb.y, orb.color, count=12, size=4)
        
        self.blue.update(self.red, tuple(self.arena_bounds), self.particles, self.shockwaves)
        self.red.update(self.blue, tuple(self.arena_bounds), self.particles, self.shockwaves)
        
        self._handle_combat()
        
        self.particles.update()
        self.shockwaves.update()
        self.arena_pulses.update()
        
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
        """Draw game."""
        offset = (0, 0)
        if self.screen_shake > 0:
            offset = (random.uniform(-self.screen_shake, self.screen_shake),
                     random.uniform(-self.screen_shake, self.screen_shake))
        
        self.screen.fill(DARK_GRAY)
        
        ax, ay, aw, ah = self.arena_bounds
        arena_rect = pygame.Rect(int(ax + offset[0]), int(ay + offset[1]), int(aw), int(ah))
        pygame.draw.rect(self.screen, BLACK, arena_rect)
        
        if self.escalation_state == 'shrinking':
            border_color = ORANGE
            border_width = 6
        elif self.escalation_state == 'pulse_triggered':
            border_color = YELLOW
            border_width = 5
        else:
            border_color = GRAY
            border_width = 4
        pygame.draw.rect(self.screen, border_color, arena_rect, border_width)
        
        self.arena_pulses.draw(self.screen, offset)
        self.shockwaves.draw(self.screen, offset)
        
        for orb in self.skill_orbs:
            orb.draw(self.screen, offset)
        
        if not self.round_ending or self.winner == self.blue:
            self.blue.draw(self.screen, offset)
        if not self.round_ending or self.winner == self.red:
            self.red.draw(self.screen, offset)
        
        self.particles.draw(self.screen, offset)
        
        if self.countdown_active:
            countdown_text = self.countdown_texts[self.countdown_stage]
            
            if countdown_text == "FIGHT":
                text_surface = self.font_medium.render(countdown_text, True, WHITE)
                border_color = YELLOW
            else:
                text_surface = self.font_large.render(countdown_text, True, WHITE)
                border_color = PURPLE
            
            text_rect = text_surface.get_rect(center=(SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2))
            
            bg_rect = text_rect.inflate(50, 30)
            pygame.draw.rect(self.screen, BLACK, bg_rect)
            pygame.draw.rect(self.screen, border_color, bg_rect, 4)
            
            self.screen.blit(text_surface, text_rect)
        
        pygame.display.flip()

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
