"""
Simplified fighter with bounce-only movement.
"""

import pygame
import math
import random

from config import (
    SCREEN_WIDTH, SCREEN_HEIGHT, WHITE, GREEN,
    FIGHTER_RADIUS, SWORD_LENGTH, SWORD_WIDTH, BASE_HEALTH,
    DRAG, MAX_VELOCITY, MIN_VELOCITY, BOUNCE_ENERGY, ARENA_MARGIN
)
from skills import SkillType


class Fighter:
    """Simplified fighter with wall-bounce movement."""
    
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
        
        # Skill states
        self.active_skill = None
        self.skill_timer = 0
        self.skill_data = {}
        
        # Visual
        self.flash_timer = 0
        self.victory_bounce = 0
        
        # Shield
        self.has_shield = False
        
        # Cooldowns
        self.attack_cooldown = 0
        self.invincible = 0
    
    def activate_skill(self, skill_type, opponent, particles, shockwaves):
        """Activate a skill move."""
        self.active_skill = skill_type
        self.skill_timer = 0
        
        if skill_type == SkillType.DASH_SLASH:
            dx = opponent.x - self.x
            dy = opponent.y - self.y
            dist = max(1, math.hypot(dx, dy))
            self.skill_data['dash_angle'] = math.atan2(dy, dx)
            self.skill_data['duration'] = 12
            # Boost velocity toward opponent
            self.vx = (dx / dist) * 25
            self.vy = (dy / dist) * 25
        
        elif skill_type == SkillType.SPIN_CUTTER:
            self.skill_data['duration'] = 45
            self.skill_data['spin_speed'] = 0.6
        
        elif skill_type == SkillType.GROUND_SLAM:
            self.skill_data['phase'] = 'rise'
            self.skill_data['duration'] = 30
        
        elif skill_type == SkillType.SHIELD:
            self.has_shield = True
            self.active_skill = None
        
        elif skill_type == SkillType.OVERDRIVE:
            self.skill_data['duration'] = 150
            self.sword_length = self.base_sword_length * 1.4
            # Speed boost
            speed = math.hypot(self.vx, self.vy)
            if speed > 0:
                self.vx = (self.vx / speed) * min(speed * 1.5, MAX_VELOCITY)
                self.vy = (self.vy / speed) * min(speed * 1.5, MAX_VELOCITY)
    
    def update_skill(self, opponent, particles, shockwaves):
        """Update active skill."""
        if self.active_skill is None:
            return
        
        self.skill_timer += 1
        
        if self.active_skill == SkillType.DASH_SLASH:
            if self.skill_timer >= self.skill_data['duration']:
                self.active_skill = None
        
        elif self.active_skill == SkillType.SPIN_CUTTER:
            if self.skill_timer < self.skill_data['duration']:
                self.sword_angle += self.skill_data['spin_speed']
            else:
                self.active_skill = None
        
        elif self.active_skill == SkillType.GROUND_SLAM:
            if self.skill_data['phase'] == 'rise':
                if self.skill_timer < 10:
                    self.vy = -6
                else:
                    self.skill_data['phase'] = 'fall'
            elif self.skill_data['phase'] == 'fall':
                if self.skill_timer < 18:
                    self.vy = 10
                else:
                    self.skill_data['phase'] = 'impact'
                    shockwaves.add(self.x, self.y, self.color, 120)
                    particles.emit_ring(self.x, self.y, self.color, 40, count=12)
            elif self.skill_data['phase'] == 'impact':
                if self.skill_timer > self.skill_data['duration']:
                    self.active_skill = None
        
        elif self.active_skill == SkillType.OVERDRIVE:
            if self.skill_timer >= self.skill_data['duration']:
                self.active_skill = None
                self.sword_length = self.base_sword_length
    
    def update(self, opponent, arena_bounds, particles, shockwaves):
        """Update fighter - bounce-only movement."""
        self.update_skill(opponent, particles, shockwaves)
        
        # Decrease timers
        if self.flash_timer > 0:
            self.flash_timer -= 1
        if self.attack_cooldown > 0:
            self.attack_cooldown -= 1
        if self.invincible > 0:
            self.invincible -= 1
        
        # Apply minimal drag
        self.vx *= DRAG
        self.vy *= DRAG
        
        # Clamp velocity
        speed = math.hypot(self.vx, self.vy)
        max_vel = MAX_VELOCITY * (1.3 if self.active_skill == SkillType.OVERDRIVE else 1.0)
        if speed > max_vel:
            self.vx = (self.vx / speed) * max_vel
            self.vy = (self.vy / speed) * max_vel
        
        # Update position
        self.x += self.vx
        self.y += self.vy
        
        # Wall bouncing (square arena)
        ax, ay, aw, ah = arena_bounds
        
        if self.x - self.radius < ax:
            self.x = ax + self.radius
            self.vx = abs(self.vx) * BOUNCE_ENERGY
        if self.x + self.radius > ax + aw:
            self.x = ax + aw - self.radius
            self.vx = -abs(self.vx) * BOUNCE_ENERGY
        if self.y - self.radius < ay:
            self.y = ay + self.radius
            self.vy = abs(self.vy) * BOUNCE_ENERGY
        if self.y + self.radius > ay + ah:
            self.y = ay + ah - self.radius
            self.vy = -abs(self.vy) * BOUNCE_ENERGY
        
        # Maintain minimum velocity (constant motion like DVD logo)
        speed = math.hypot(self.vx, self.vy)
        if speed < MIN_VELOCITY and speed > 0:
            self.vx = (self.vx / speed) * MIN_VELOCITY
            self.vy = (self.vy / speed) * MIN_VELOCITY
        elif speed == 0:
            # Give random direction if stopped
            angle = random.uniform(0, 2 * math.pi)
            self.vx = math.cos(angle) * MIN_VELOCITY
            self.vy = math.sin(angle) * MIN_VELOCITY
        
        # Sword angle - point toward opponent when close
        dx = opponent.x - self.x
        dy = opponent.y - self.y
        dist = math.hypot(dx, dy)
        
        if self.active_skill != SkillType.SPIN_CUTTER:
            if dist < 200:
                # Point at opponent
                target_angle = math.atan2(dy, dx)
            else:
                # Point in movement direction
                if speed > 1:
                    target_angle = math.atan2(self.vy, self.vx)
                else:
                    target_angle = self.sword_angle
            
            # Smooth rotation
            diff = ((target_angle - self.sword_angle + math.pi) % (2 * math.pi)) - math.pi
            self.sword_angle += diff * 0.15
        
        # Victory bounce
        if self.victory_bounce > 0:
            self.victory_bounce -= 1
            self.y += math.sin(self.victory_bounce * 0.4) * 5
    
    def get_sword_hitbox(self):
        """Get sword collision points."""
        base_x = self.x + math.cos(self.sword_angle) * (self.radius + 3)
        base_y = self.y + math.sin(self.sword_angle) * (self.radius + 3)
        tip_x = base_x + math.cos(self.sword_angle) * self.sword_length
        tip_y = base_y + math.sin(self.sword_angle) * self.sword_length
        return (base_x, base_y), (tip_x, tip_y)
    
    def draw(self, surface, offset=(0, 0)):
        """Draw simplified fighter."""
        ox, oy = offset
        
        # Main body circle
        body_color = WHITE if self.flash_timer > 0 else self.color
        pygame.draw.circle(surface, body_color, 
                          (int(self.x + ox), int(self.y + oy)), self.radius)
        
        # Small inner highlight (optional)
        pygame.draw.circle(surface, self.color_bright,
                          (int(self.x - self.radius * 0.2 + ox), 
                           int(self.y - self.radius * 0.2 + oy)), 
                          int(self.radius * 0.3))
        
        # Simple sword (just a line)
        self._draw_sword(surface, offset)
        
        # Health bar above fighter
        self._draw_health_bar(surface, offset)
        
        # Shield indicator
        if self.has_shield:
            pygame.draw.circle(surface, GREEN, 
                              (int(self.x + ox), int(self.y + oy)), 
                              self.radius + 8, 3)
    
    def _draw_sword(self, surface, offset):
        """Draw simple line sword."""
        ox, oy = offset
        
        base_x = self.x + math.cos(self.sword_angle) * (self.radius + 3)
        base_y = self.y + math.sin(self.sword_angle) * (self.radius + 3)
        tip_x = base_x + math.cos(self.sword_angle) * self.sword_length
        tip_y = base_y + math.sin(self.sword_angle) * self.sword_length
        
        # Simple line
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
        """Check if outside arena (for ring-out)."""
        ax, ay, aw, ah = arena_bounds
        margin = self.radius * 3
        return (self.x < ax - margin or self.x > ax + aw + margin or
                self.y < ay - margin or self.y > ay + ah + margin)
    
    def take_damage(self, amount, knockback_angle, knockback_force, particles):
        """Take damage and knockback."""
        if self.invincible > 0:
            return False
        
        if self.has_shield:
            self.has_shield = False
            particles.emit(self.x, self.y, GREEN, count=10, size=4)
            return False
        
        self.health -= amount
        self.flash_timer = 6
        self.invincible = 8
        
        self.vx += math.cos(knockback_angle) * knockback_force
        self.vy += math.sin(knockback_angle) * knockback_force
        
        return True
    
    def reset(self):
        """Reset fighter state."""
        self.x = self.start_x
        self.y = self.start_y
        self.vx = random.uniform(-6, 6)
        self.vy = random.uniform(-6, 6)
        self.radius = FIGHTER_RADIUS
        self.health = BASE_HEALTH
        self.sword_length = self.base_sword_length
        self.active_skill = None
        self.skill_timer = 0
        self.skill_data = {}
        self.flash_timer = 0
        self.victory_bounce = 0
        self.has_shield = False
        self.invincible = 0
        self.attack_cooldown = 0
