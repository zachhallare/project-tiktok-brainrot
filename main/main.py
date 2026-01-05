import pygame
import math
import random

from config import (
    SCREEN_WIDTH, SCREEN_HEIGHT, FPS,
    BLUE, BLUE_BRIGHT, RED, RED_BRIGHT, WHITE, PURPLE, BLACK, DARK_GRAY, GRAY,
    ARENA_MARGIN, ARENA_WIDTH, ARENA_HEIGHT,
    ARENA_SHRINK_INTERVAL, ARENA_SHRINK_AMOUNT,
    POWERUP_SPAWN_MIN, POWERUP_SPAWN_MAX, MAX_POWERUPS,
    ROUND_MAX_TIME, BASE_KNOCKBACK, DAMAGE_PER_HIT, SLOW_MOTION_SPEED,
    HIT_STOP_FRAMES, SCREEN_SHAKE_INTENSITY, SCREEN_SHAKE_DECAY
)
from effects import ParticleSystem, ShockwaveSystem
from skills import SkillType, SkillOrb
from fighter import Fighter


class Game:
    """Main game with square arena."""
    
    def __init__(self):
        pygame.init()
        pygame.mixer.init()
        pygame.font.init()
        
        self.screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
        pygame.display.set_caption("Red vs Blue Battle")
        self.clock = pygame.time.Clock()
        
        # Font for win text
        self.font_large = pygame.font.Font(None, 72)
        self.font_small = pygame.font.Font(None, 36)
        
        # Arena bounds (square)
        self.base_arena = (ARENA_MARGIN, ARENA_MARGIN, ARENA_WIDTH, ARENA_HEIGHT)
        self.arena_bounds = list(self.base_arena)
        self.arena_shrink_timer = ARENA_SHRINK_INTERVAL * FPS
        
        # Fighters spawn at opposite sides
        spawn_margin = 100
        center_y = SCREEN_HEIGHT // 2
        self.blue = Fighter(ARENA_MARGIN + spawn_margin, center_y, 
                           BLUE, BLUE_BRIGHT, is_blue=True)
        self.red = Fighter(SCREEN_WIDTH - ARENA_MARGIN - spawn_margin, center_y, 
                          RED, RED_BRIGHT, is_blue=False)
        
        # Effects
        self.particles = ParticleSystem()
        self.shockwaves = ShockwaveSystem()
        
        # Power-ups
        self.skill_orbs = []
        self.powerup_timer = random.uniform(POWERUP_SPAWN_MIN, POWERUP_SPAWN_MAX) * FPS
        
        # Screen effects
        self.screen_shake = 0
        self.hit_stop = 0
        
        # Round state
        self.round_timer = 0
        self.round_ending = False
        self.winner = None
        self.winner_text = ""
        self.reset_timer = 0
        
        # UI controls
        self.paused = False
        self.slow_motion = False
        self.slow_motion_accumulator = 0.0
        
        # Countdown before fight
        self.countdown_timer = 3 * FPS  # 3 seconds
        self.countdown_active = True
        
        # Sounds
        self._setup_sounds()
    
    def _setup_sounds(self):
        """Simple sound generation."""
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
            
            # Explosion
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
            
            self.sounds_enabled = True
        except:
            self.sounds_enabled = False
    
    def _spawn_skill_orb(self):
        """Spawn power-up inside arena."""
        if len(self.skill_orbs) >= MAX_POWERUPS:
            return
        
        ax, ay, aw, ah = self.arena_bounds
        margin = 60
        x = random.randint(int(ax + margin), int(ax + aw - margin))
        y = random.randint(int(ay + margin), int(ay + ah - margin))
        
        skill_type = random.randint(0, 4)
        self.skill_orbs.append(SkillOrb(x, y, skill_type))
    
    def _check_sword_hit(self, attacker, defender):
        """Check sword collision."""
        (base_x, base_y), (tip_x, tip_y) = attacker.get_sword_hitbox()
        
        for t in [0.4, 0.7, 1.0]:
            check_x = base_x + (tip_x - base_x) * t
            check_y = base_y + (tip_y - base_y) * t
            dist = math.hypot(check_x - defender.x, check_y - defender.y)
            if dist < defender.radius + 8:
                return (check_x, check_y)
        return None
    
    def _handle_combat(self):
        """Process combat."""
        # Blue attacks Red
        hit_blue = self._check_sword_hit(self.blue, self.red)
        if hit_blue and self.blue.attack_cooldown <= 0:
            angle = math.atan2(self.red.y - self.blue.y, self.red.x - self.blue.x)
            knockback = BASE_KNOCKBACK
            
            if self.blue.active_skill == SkillType.DASH_SLASH:
                knockback *= 2
            elif self.blue.active_skill == SkillType.OVERDRIVE:
                knockback *= 1.4
            
            if self.red.take_damage(DAMAGE_PER_HIT, angle, knockback, self.particles):
                self._trigger_hit(hit_blue[0], hit_blue[1], self.blue.color)
                self.blue.attack_cooldown = 18
        
        # Red attacks Blue
        hit_red = self._check_sword_hit(self.red, self.blue)
        if hit_red and self.red.attack_cooldown <= 0:
            angle = math.atan2(self.blue.y - self.red.y, self.blue.x - self.red.x)
            knockback = BASE_KNOCKBACK
            
            if self.red.active_skill == SkillType.DASH_SLASH:
                knockback *= 2
            elif self.red.active_skill == SkillType.OVERDRIVE:
                knockback *= 1.4
            
            if self.blue.take_damage(DAMAGE_PER_HIT, angle, knockback, self.particles):
                self._trigger_hit(hit_red[0], hit_red[1], self.red.color)
                self.red.attack_cooldown = 18
        
        # Ground slam damage
        for attacker, defender in [(self.blue, self.red), (self.red, self.blue)]:
            if (attacker.active_skill == SkillType.GROUND_SLAM and 
                attacker.skill_data.get('phase') == 'impact' and
                attacker.skill_timer == 18):
                dist = math.hypot(defender.x - attacker.x, defender.y - attacker.y)
                if dist < 120:
                    angle = math.atan2(defender.y - attacker.y, defender.x - attacker.x)
                    defender.take_damage(DAMAGE_PER_HIT * 1.5, angle, 15, self.particles)
                    self._trigger_hit(defender.x, defender.y, attacker.color)
    
    def _trigger_hit(self, x, y, color):
        """Hit effects."""
        self.particles.emit(x, y, WHITE, count=10, size=4)
        self.hit_stop = HIT_STOP_FRAMES
        self.screen_shake = SCREEN_SHAKE_INTENSITY
        
        if self.sounds_enabled:
            self.hit_sound.play()
    
    def _end_round(self, winner, loser):
        """End round with winner."""
        self.round_ending = True
        self.winner = winner
        self.winner_text = "Blue Wins!" if winner.is_blue else "Red Wins!"
        self.reset_timer = 120  # 2 seconds
        
        self.particles.emit_explosion(loser.x, loser.y, loser.color, count=40)
        self.shockwaves.add(loser.x, loser.y, loser.color, 100)
        winner.victory_bounce = 40
        
        # Enable slow-motion for dramatic effect
        self.slow_motion = True
        self.slow_motion_accumulator = 0.0
        
        if self.sounds_enabled:
            self.explosion_sound.play()
    
    def _reset_round(self):
        """Reset for new round."""
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
        
        # Disable slow-motion
        self.slow_motion = False
        self.slow_motion_accumulator = 0.0
        
        # Restart countdown
        self.countdown_timer = 3 * FPS
        self.countdown_active = True
    
    def update(self):
        """Update game state."""
        # Check if paused
        if self.paused:
            return
        
        # Handle countdown before fight
        if self.countdown_active:
            self.countdown_timer -= 1
            if self.countdown_timer <= 0:
                self.countdown_active = False
            return
        
        # Handle slow-motion during death sequence
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
            return
        
        self.round_timer += 1
        
        # Arena shrink
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
        
        # Power-ups
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
        
        # Update fighters
        self.blue.update(self.red, tuple(self.arena_bounds), self.particles, self.shockwaves)
        self.red.update(self.blue, tuple(self.arena_bounds), self.particles, self.shockwaves)
        
        # Combat
        self._handle_combat()
        
        # Effects
        self.particles.update()
        self.shockwaves.update()
        
        # Win conditions
        if self.blue.health <= 0:
            self._end_round(winner=self.red, loser=self.blue)
        elif self.red.health <= 0:
            self._end_round(winner=self.blue, loser=self.red)
        
        # Timeout - closest to center wins
        if self.round_timer > ROUND_MAX_TIME * FPS:
            cx = SCREEN_WIDTH // 2
            cy = SCREEN_HEIGHT // 2
            blue_dist = math.hypot(self.blue.x - cx, self.blue.y - cy)
            red_dist = math.hypot(self.red.x - cx, self.red.y - cy)
            if blue_dist < red_dist:
                self._end_round(winner=self.blue, loser=self.red)
            else:
                self._end_round(winner=self.red, loser=self.blue)
    
    def draw(self):
        """Render game."""
        offset = (0, 0)
        if self.screen_shake > 0:
            offset = (random.uniform(-self.screen_shake, self.screen_shake),
                     random.uniform(-self.screen_shake, self.screen_shake))
        
        # Dark background
        self.screen.fill(DARK_GRAY)
        
        # Draw arena (simple rectangle)
        ax, ay, aw, ah = self.arena_bounds
        arena_rect = pygame.Rect(int(ax + offset[0]), int(ay + offset[1]), int(aw), int(ah))
        pygame.draw.rect(self.screen, BLACK, arena_rect)
        pygame.draw.rect(self.screen, GRAY, arena_rect, 4)
        
        # Draw shockwaves
        self.shockwaves.draw(self.screen, offset)
        
        # Draw power-ups
        for orb in self.skill_orbs:
            orb.draw(self.screen, offset)
        
        # Draw fighters
        if not self.round_ending or self.winner == self.blue:
            self.blue.draw(self.screen, offset)
        if not self.round_ending or self.winner == self.red:
            self.red.draw(self.screen, offset)
        
        # Draw particles
        self.particles.draw(self.screen, offset)
        
        # Draw win text
        if self.round_ending and self.winner_text:
            text_color = BLUE if self.winner.is_blue else RED
            text_surface = self.font_large.render(self.winner_text, True, text_color)
            text_rect = text_surface.get_rect(center=(SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2))
            
            # Background box
            bg_rect = text_rect.inflate(40, 20)
            pygame.draw.rect(self.screen, BLACK, bg_rect)
            pygame.draw.rect(self.screen, text_color, bg_rect, 3)
            
            self.screen.blit(text_surface, text_rect)
        
        # Draw countdown text "Red vs Blue"
        if self.countdown_active:
            countdown_text = "Red vs Blue"
            text_surface = self.font_large.render(countdown_text, True, WHITE)
            text_rect = text_surface.get_rect(center=(SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2))
            
            # Background box
            bg_rect = text_rect.inflate(40, 20)
            pygame.draw.rect(self.screen, BLACK, bg_rect)
            pygame.draw.rect(self.screen, PURPLE, bg_rect, 3)
            
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
                        self.paused = not self.paused
                    elif event.key == pygame.K_r:
                        self._reset_round()
            
            self.update()
            self.draw()
            self.clock.tick(FPS)
        
        pygame.quit()


if __name__ == "__main__":
    game = Game()
    game.run()
