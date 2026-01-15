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
    ROUND_MAX_TIME, BASE_KNOCKBACK, DAMAGE_PER_HIT, SLOW_MOTION_SPEED,
    HIT_STOP_FRAMES, SCREEN_SHAKE_INTENSITY, SCREEN_SHAKE_DECAY,
    HIT_SLOWMO_FRAMES, HIT_SLOWMO_TIMESCALE,
    INACTIVITY_PULSE_TIME, INACTIVITY_SHRINK_TIME, ARENA_PULSE_VELOCITY_BOOST,
    ARENA_PULSE_SHAKE, ESCALATION_SHRINK_SPEED, GAME_SETTINGS,
    FIGHTER_RADIUS,
    NEON_RED, NEON_BLUE, NEON_BG, NEON_GRID
)
from effects import ParticleSystem, ShockwaveSystem, ArenaPulseSystem, DamageNumberSystem
from fighter import Fighter
from chaos_manager import ChaosManager


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
        
        # Bold/Impact font for chaos banner
        try:
            self.font_chaos = pygame.font.SysFont("Impact", 48, bold=True)
        except:
            self.font_chaos = pygame.font.Font(None, 56)
        
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
        
        # Screen effects.
        self.screen_shake = 0
        self.hit_stop = 0
        self.hit_slowmo_frames = 0
        self.hit_slowmo_accumulator = 0.0
        
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
                
                # Apply combo damage multiplier + chaos damage multiplier
                damage_mult = attacker.get_attack_damage_multiplier()
                chaos_damage_mult = self.chaos.get_damage_mult()
                total_damage_mult = damage_mult * chaos_damage_mult
                
                angle = math.atan2(defender.y - attacker.y, defender.x - attacker.x)
                knockback = BASE_KNOCKBACK * (1.0 + (total_damage_mult - 1.0) * 0.5)
                damage = DAMAGE_PER_HIT * total_damage_mult
                
                # Pierce (combo stage 2) has more hit-stop
                hit_stop_frames = HIT_STOP_FRAMES + (2 if attacker.combo_stage == 2 else 0)
                
                if defender.take_damage(damage, angle, knockback, self.particles):
                    self._trigger_hit(hit_pos[0], hit_pos[1], attacker.render_color, hit_stop_frames, damage)
                    self.hit_slowmo_frames = HIT_SLOWMO_FRAMES
                    attacker.on_attack_hit(self.round_timer)
                    self._reset_inactivity()

    def _trigger_hit(self, x, y, color, hit_stop_frames=None, damage=0):
        """Apply hit effects including damage numbers."""
        self.particles.emit(x, y, WHITE, count=10, size=4)
        self.hit_stop = hit_stop_frames if hit_stop_frames else HIT_STOP_FRAMES
        self.screen_shake = SCREEN_SHAKE_INTENSITY
        
        # Spawn floating damage number
        if damage > 0:
            self.damage_numbers.spawn(x, y - 20, damage, color)
        
        if self.sounds_enabled:
            self.hit_sound.play()

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
        
        # Reset chaos system
        self.chaos.reset_chaos()
        
        self.hit_slowmo_frames = 0
        self.hit_slowmo_accumulator = 0.0
        
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
        
        # ===== CHAOS SYSTEM UPDATE =====
        dt = 1.0 / FPS
        self.chaos.update(dt, self.particles, [self.blue, self.red])
        
        # Apply chaos modifiers to fighters
        speed_mult = self.chaos.get_speed_mult()
        size_mult = self.chaos.get_size_mult()
        center_x = SCREEN_WIDTH // 2
        center_y = SCREEN_HEIGHT // 2
        
        for fighter in [self.blue, self.red]:
            # Apply size multiplier
            fighter.size_multiplier = size_mult
            
            # Apply chaos color overrides
            fighter.render_color = self.chaos.get_fighter_color(fighter.color, fighter.is_blue)
            fighter.render_color_bright = self.chaos.get_fighter_color(fighter.color_bright, fighter.is_blue)
            
            # Apply Tumble Dryer rotational gravity
            fx, fy = self.chaos.get_gravity_force(fighter.x, fighter.y, center_x, center_y)
            fighter.vx += fx
            fighter.vy += fy
            
            # Apply speed multiplier to velocity
            if speed_mult != 1.0:
                fighter.vx *= (1.0 + (speed_mult - 1.0) * 0.1)  # Gradual speed change
                fighter.vy *= (1.0 + (speed_mult - 1.0) * 0.1)
        
        # Calculate arena bounds with Crusher modifier
        arena_mult = self.chaos.get_arena_mult()
        if arena_mult < 1.0:
            # Apply Crusher shrinking
            base_ax, base_ay, base_aw, base_ah = self.base_arena
            shrink = (1.0 - arena_mult) * min(base_aw, base_ah) / 2
            effective_arena = (
                self.arena_bounds[0] + shrink,
                self.arena_bounds[1] + shrink,
                max(200, self.arena_bounds[2] - shrink * 2),
                max(200, self.arena_bounds[3] - shrink * 2)
            )
        else:
            effective_arena = tuple(self.arena_bounds)
        
        # Update fighters with effective arena
        self.blue.update(self.red, effective_arena, self.particles, self.shockwaves)
        self.red.update(self.blue, effective_arena, self.particles, self.shockwaves)
        
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
        
        # Calculate effective arena for Crusher
        arena_mult = self.chaos.get_arena_mult()
        if arena_mult < 1.0:
            shrink = (1.0 - arena_mult) * min(self.arena_bounds[2], self.arena_bounds[3]) / 2
            draw_arena = (
                self.arena_bounds[0] + shrink,
                self.arena_bounds[1] + shrink,
                max(200, self.arena_bounds[2] - shrink * 2),
                max(200, self.arena_bounds[3] - shrink * 2)
            )
        else:
            draw_arena = self.arena_bounds
        
        ax, ay, aw, ah = draw_arena
        arena_rect = pygame.Rect(int(ax + offset[0]), int(ay + offset[1]), int(aw), int(ah))
        
        # Arena fill color (dark or Blackout inverted)
        arena_fill = WHITE if self.chaos.is_blackout() else BLACK
        pygame.draw.rect(self.screen, arena_fill, arena_rect)
        
        # Arena border
        if self.escalation_state == 'shrinking' or self.chaos.active_event == "THE CRUSHER":
            border_color = NEON_RED if not self.chaos.is_blackout() else BLACK
            border_width = 6
        elif self.escalation_state == 'pulse_triggered':
            border_color = YELLOW
            border_width = 5
        else:
            border_color = NEON_BLUE if not self.chaos.is_blackout() else GRAY
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
        
        # Draw chaos event banner (unless Blackout which hides UI)
        if self.chaos.active_event and not self.chaos.is_blackout():
            self._draw_chaos_banner()
        
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
    
    def _draw_chaos_banner(self):
        """Draw pulsing chaos event banner."""
        if not self.chaos.active_event:
            return
        
        # Pulsing animation
        pulse = 1.0 + 0.15 * math.sin(pygame.time.get_ticks() * 0.008)
        
        event_text = self.chaos.active_event
        
        # Render text
        text_surface = self.font_chaos.render(event_text, True, WHITE)
        
        # Scale for pulse effect
        if pulse != 1.0:
            new_w = int(text_surface.get_width() * pulse)
            new_h = int(text_surface.get_height() * pulse)
            if new_w > 0 and new_h > 0:
                text_surface = pygame.transform.scale(text_surface, (new_w, new_h))
        
        # Position at top of screen
        text_rect = text_surface.get_rect(center=(SCREEN_WIDTH // 2, 60))
        
        # Draw shadow
        shadow_surface = self.font_chaos.render(event_text, True, (30, 30, 30))
        if pulse != 1.0:
            new_w = int(shadow_surface.get_width() * pulse)
            new_h = int(shadow_surface.get_height() * pulse)
            if new_w > 0 and new_h > 0:
                shadow_surface = pygame.transform.scale(shadow_surface, (new_w, new_h))
        shadow_rect = shadow_surface.get_rect(center=(SCREEN_WIDTH // 2 + 2, 62))
        
        # Background bar
        bar_rect = pygame.Rect(0, 30, SCREEN_WIDTH, 60)
        bar_surface = pygame.Surface((bar_rect.width, bar_rect.height), pygame.SRCALPHA)
        pygame.draw.rect(bar_surface, (0, 0, 0, 180), bar_surface.get_rect())
        self.screen.blit(bar_surface, bar_rect)
        
        # Draw text
        self.screen.blit(shadow_surface, shadow_rect)
        self.screen.blit(text_surface, text_rect)
        
        # Progress bar for event duration
        progress = self.chaos.get_event_progress()
        bar_width = int(SCREEN_WIDTH * 0.6)
        bar_x = (SCREEN_WIDTH - bar_width) // 2
        bar_y = 85
        
        # Background bar
        pygame.draw.rect(self.screen, (50, 50, 50), (bar_x, bar_y, bar_width, 6))
        # Progress fill
        fill_width = int(bar_width * (1.0 - progress))
        if fill_width > 0:
            pygame.draw.rect(self.screen, NEON_BLUE, (bar_x, bar_y, fill_width, 6))

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
