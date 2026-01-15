"""
Simplified fighter with bounce-only movement and basic attack combos.
DVD logo style - fighters bounce around arena with swinging swords.
"""

import pygame
import math
import random

from config import (
    SCREEN_WIDTH, SCREEN_HEIGHT, WHITE, GREEN, YELLOW, BLACK,
    FIGHTER_RADIUS, SWORD_LENGTH, SWORD_WIDTH, BASE_HEALTH,
    DRAG, MAX_VELOCITY, MIN_VELOCITY, BOUNCE_ENERGY, ARENA_MARGIN,
    WALL_BOOST_STRENGTH
)


class Fighter:
    """Simplified fighter with wall-bounce movement and combo attacks."""
    
    def __init__(self, x, y, color, color_bright, is_blue=True):
        self.x = x
        self.y = y
        self.start_x = x
        self.start_y = y
        self.vx = random.uniform(-8, 8)  # Start with random velocity
        self.vy = random.uniform(-8, 8)
        self.radius = FIGHTER_RADIUS
        self.color = color
        self.color_bright = color_bright
        self.is_blue = is_blue
        self.health = BASE_HEALTH
        self.max_health = BASE_HEALTH
        
        # Sword
        self.sword_angle = 0
        self.sword_length = SWORD_LENGTH
        self.base_sword_length = SWORD_LENGTH
        
        # Visual
        self.flash_timer = 0
        self.victory_bounce = 0
        
        # Cooldowns
        self.attack_cooldown = 0
        self.invincible = 0
        
        # Locked state (during countdown)
        self.locked = False
        
        # Combo Attack System (left-right-pierce)
        self.combo_stage = 0           # 0=left, 1=right, 2=pierce
        self.is_attacking = False      # Currently in attack animation
        self.attack_timer = 0          # Frames into current attack
        self.attack_target_angle = 0   # Direction to opponent
        self.swing_start_angle = 0     # Start angle of swing
        self.swing_end_angle = 0       # End angle of swing
        self.last_hit_frame = -100     # Frame of last successful hit
        self.combo_reset_timer = 0     # Timer to reset combo on miss/timeout
        
        # Attack timing constants
        self.ATTACK_DURATION = 12      # Frames per swing
        self.ATTACK_COOLDOWN = 8       # Frames between attacks
        self.COMBO_TIMEOUT = 45        # Frames before combo resets
    

    
    def update_rotation(self, opponent=None, frame_count=0):
        """Update sword angle - point toward opponent, swing during attacks."""
        if not opponent:
            return
        
        # Calculate angle to opponent
        self.attack_target_angle = math.atan2(opponent.y - self.y, opponent.x - self.x)
        
        # Combo timeout - reset if too long since last attack
        if self.combo_reset_timer > 0:
            self.combo_reset_timer -= 1
        elif self.combo_stage > 0 and not self.is_attacking:
            self.combo_stage = 0  # Reset combo after timeout
        
        if self.is_attacking:
            # Currently swinging
            self.attack_timer += 1
            progress = min(1.0, self.attack_timer / self.ATTACK_DURATION)
            
            # Ease-out for snappy feel
            eased = 1 - (1 - progress) ** 2
            
            # Interpolate from start to end angle
            angle_diff = self.swing_end_angle - self.swing_start_angle
            # Handle wraparound
            if angle_diff > math.pi:
                angle_diff -= 2 * math.pi
            elif angle_diff < -math.pi:
                angle_diff += 2 * math.pi
            
            self.sword_angle = self.swing_start_angle + angle_diff * eased
            
            # Attack finished
            if self.attack_timer >= self.ATTACK_DURATION:
                self.is_attacking = False
                self.attack_cooldown = self.ATTACK_COOLDOWN
                self.combo_reset_timer = self.COMBO_TIMEOUT
        else:
            # Not attacking - sword points toward opponent with offset based on combo
            if self.combo_stage == 0:
                # Ready for left slash - sword angled to the left
                offset = 0.6 if self.is_blue else -0.6
            elif self.combo_stage == 1:
                # Ready for right slash - sword angled to the right
                offset = -0.6 if self.is_blue else 0.6
            else:
                # Ready for pierce - sword straight
                offset = 0
            
            target = self.attack_target_angle + offset
            
            # Smooth rotation toward ready position
            angle_diff = ((target - self.sword_angle + math.pi) % (2 * math.pi)) - math.pi
            self.sword_angle += angle_diff * 0.2
        
        # Keep angle in [-π, π]
        if self.sword_angle > math.pi:
            self.sword_angle -= 2 * math.pi
        elif self.sword_angle < -math.pi:
            self.sword_angle += 2 * math.pi
    
    def start_attack(self, frame_count):
        """Initiate an attack based on current combo stage."""
        if self.is_attacking or self.attack_cooldown > 0:
            return False
        
        self.is_attacking = True
        self.attack_timer = 0
        
        if self.combo_stage == 0:
            # Left slash: wide arc (120°) from left to right
            arc = 2.1  # ~120 degrees
            self.swing_start_angle = self.attack_target_angle + arc / 2
            self.swing_end_angle = self.attack_target_angle - arc / 2
        elif self.combo_stage == 1:
            # Right slash: medium arc (90°) from right to left  
            arc = 1.57  # ~90 degrees
            self.swing_start_angle = self.attack_target_angle - arc / 2
            self.swing_end_angle = self.attack_target_angle + arc / 2
        else:
            # Pierce: narrow thrust (30°)
            arc = 0.52  # ~30 degrees
            self.swing_start_angle = self.attack_target_angle
            self.swing_end_angle = self.attack_target_angle
            # Extend sword briefly for pierce
            self.sword_length = self.base_sword_length * 1.3
        
        return True
    
    def on_attack_hit(self, frame_count):
        """Called when attack successfully hits opponent body."""
        # Prevent multi-hits in same swing
        if frame_count - self.last_hit_frame < 8:
            return False
        
        self.last_hit_frame = frame_count
        
        # Advance combo
        self.combo_stage = (self.combo_stage + 1) % 3
        self.combo_reset_timer = self.COMBO_TIMEOUT
        
        # Reset sword length if pierce ended
        self.sword_length = self.base_sword_length
        
        return True
    
    def on_attack_miss(self):
        """Called when attack misses or is blocked - reset combo."""
        self.combo_stage = 0
        self.combo_reset_timer = 0
        self.sword_length = self.base_sword_length
    
    def on_attack_blocked(self):
        """Called when attack is blocked by shield."""
        self.on_attack_miss()
        self.attack_cooldown = 20  # Longer recovery on block
    
    def update(self, opponent, arena_bounds, particles, shockwaves):
        """Update fighter - bounce-only movement with ninja wall boosts."""
        # Skip update if locked (during countdown)
        if self.locked:
            return
        
        self.update_rotation(opponent, 0)  # Sword faces opponent with combo offset
        
        # Decrease timers
        if self.flash_timer > 0:
            self.flash_timer -= 1
        if self.attack_cooldown > 0:
            self.attack_cooldown -= 1
        if self.invincible > 0:
            self.invincible -= 1

        
        # Apply minimal drag (DVD logo - constant velocity)
        self.vx *= DRAG
        self.vy *= DRAG
        
        # Clamp velocity
        speed = math.hypot(self.vx, self.vy)
        max_vel = MAX_VELOCITY
        if speed > max_vel:
            self.vx = (self.vx / speed) * max_vel
            self.vy = (self.vy / speed) * max_vel
        
        # Ensure minimum velocity (DVD logo always moving)
        if speed < MIN_VELOCITY and speed > 0:
            self.vx = (self.vx / speed) * MIN_VELOCITY
            self.vy = (self.vy / speed) * MIN_VELOCITY
        elif speed == 0:
            # Give random velocity if stopped
            angle = random.uniform(0, 2 * math.pi)
            self.vx = math.cos(angle) * MIN_VELOCITY
            self.vy = math.sin(angle) * MIN_VELOCITY
        
        # Update position
        self.x += self.vx
        self.y += self.vy
        
        # Wall collision with perfect bounce (DVD logo style)
        ax, ay, aw, ah = arena_bounds
        
        # Left wall
        if self.x - self.radius < ax:
            self.x = ax + self.radius
            self.vx = abs(self.vx) * BOUNCE_ENERGY
            # Ninja wall boost toward center
            center_x = ax + aw / 2
            if self.x < center_x:
                self.vx += WALL_BOOST_STRENGTH
        
        # Right wall
        if self.x + self.radius > ax + aw:
            self.x = ax + aw - self.radius
            self.vx = -abs(self.vx) * BOUNCE_ENERGY
            center_x = ax + aw / 2
            if self.x > center_x:
                self.vx -= WALL_BOOST_STRENGTH
        
        # Top wall
        if self.y - self.radius < ay:
            self.y = ay + self.radius
            self.vy = abs(self.vy) * BOUNCE_ENERGY
            center_y = ay + ah / 2
            if self.y < center_y:
                self.vy += WALL_BOOST_STRENGTH
        
        # Bottom wall
        if self.y + self.radius > ay + ah:
            self.y = ay + ah - self.radius
            self.vy = -abs(self.vy) * BOUNCE_ENERGY
            center_y = ay + ah / 2
            if self.y > center_y:
                self.vy -= WALL_BOOST_STRENGTH
        
        # Victory bounce
        if self.victory_bounce > 0:
            self.victory_bounce -= 1
            self.y += math.sin(self.victory_bounce * 0.4) * 5
    
    def get_sword_hitbox(self):
        """Get sword collision points for rotation attacks."""
        base_x = self.x + math.cos(self.sword_angle) * (self.radius + 3)
        base_y = self.y + math.sin(self.sword_angle) * (self.radius + 3)
        tip_x = base_x + math.cos(self.sword_angle) * self.sword_length
        tip_y = base_y + math.sin(self.sword_angle) * self.sword_length
        return (base_x, base_y), (tip_x, tip_y)
    
    def get_attack_damage_multiplier(self):
        """Get damage multiplier based on combo stage."""
        if self.combo_stage == 0:
            return 1.0   # Left slash - normal
        elif self.combo_stage == 1:
            return 1.2   # Right slash - bonus
        else:
            return 1.5   # Pierce - big bonus
    

    
    def draw(self, surface, offset=(0, 0)):
        """Draw fighter."""
        ox, oy = offset
        
        # Main body circle
        body_color = WHITE if self.flash_timer > 0 else self.color
        pygame.draw.circle(surface, body_color, 
                          (int(self.x + ox), int(self.y + oy)), self.radius)
        
        # Inner highlight
        pygame.draw.circle(surface, self.color_bright,
                          (int(self.x - self.radius * 0.2 + ox), 
                           int(self.y - self.radius * 0.2 + oy)), 
                          int(self.radius * 0.3))
        
        # Sword
        self._draw_sword(surface, offset)
        
        # Health bar
        self._draw_health_bar(surface, offset)
    
    def _draw_sword(self, surface, offset):
        """Draw sword."""
        ox, oy = offset
        
        base_x = self.x + math.cos(self.sword_angle) * (self.radius + 3)
        base_y = self.y + math.sin(self.sword_angle) * (self.radius + 3)
        tip_x = base_x + math.cos(self.sword_angle) * self.sword_length
        tip_y = base_y + math.sin(self.sword_angle) * self.sword_length
        
        sword_color = WHITE if self.flash_timer > 0 else self.color_bright
        
        pygame.draw.line(surface, sword_color,
                        (int(base_x + ox), int(base_y + oy)),
                        (int(tip_x + ox), int(tip_y + oy)), SWORD_WIDTH)
    
    def _draw_health_bar(self, surface, offset):
        """Draw health bar above fighter."""
        ox, oy = offset
        bar_width = 40
        bar_height = 6
        bar_x = self.x - bar_width // 2
        bar_y = self.y - self.radius - 15
        
        # Background
        pygame.draw.rect(surface, (50, 50, 50),
                        (int(bar_x + ox), int(bar_y + oy), bar_width, bar_height))
        
        # Health fill
        health_pct = max(0, self.health / self.max_health)
        fill_width = int(bar_width * health_pct)
        if fill_width > 0:
            pygame.draw.rect(surface, self.color,
                            (int(bar_x + ox), int(bar_y + oy), fill_width, bar_height))
        
        # Border
        pygame.draw.rect(surface, WHITE,
                        (int(bar_x + ox), int(bar_y + oy), bar_width, bar_height), 1)
    
    def is_outside_arena(self, arena_bounds):
        """Check if outside arena (ring-out)."""
        ax, ay, aw, ah = arena_bounds
        margin = self.radius * 3
        return (self.x < ax - margin or self.x > ax + aw + margin or
                self.y < ay - margin or self.y > ay + ah + margin)
    
    def take_damage(self, amount, knockback_angle, knockback_force, particles):
        """Take damage and knockback."""
        if self.invincible > 0:
            return False
        
        self.health -= amount
        self.flash_timer = 6
        self.invincible = 10
        
        self.vx += math.cos(knockback_angle) * knockback_force
        self.vy += math.sin(knockback_angle) * knockback_force
        
        return True
    
    def reset(self):
        """Reset fighter state."""
        self.x = self.start_x
        self.y = self.start_y
        self.vx = random.uniform(-8, 8)
        self.vy = random.uniform(-8, 8)
        self.radius = FIGHTER_RADIUS
        self.health = BASE_HEALTH
        self.sword_angle = 0
        self.sword_length = self.base_sword_length
        
        self.flash_timer = 0
        self.victory_bounce = 0
        self.attack_cooldown = 0
        self.invincible = 0
        self.locked = False
        
        self.combo_stage = 0
        self.is_attacking = False
        self.attack_timer = 0
        self.combo_reset_timer = 0
        self.last_hit_frame = -100
