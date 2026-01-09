"""
Simplified fighter with bounce-only movement and 7 skill-based power-ups.
"""

import pygame
import math
import random

from config import (
    SCREEN_WIDTH, SCREEN_HEIGHT, WHITE, GREEN, YELLOW, PINK, GOLD, BLACK,
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
        
        # Trail positions for dash effects
        self.trail_positions = []
        
        # Visual
        self.flash_timer = 0
        self.victory_bounce = 0
        
        # Shield
        self.has_shield = False
        self.shield_parry_window = 0  # Active parry frames
        
        # Cooldowns
        self.attack_cooldown = 0
        self.invincible = 0
        
        # Phantom Cross delayed damage
        self.pending_damage = []  # [(target, damage, angle, knockback, delay_frames), ...]
        
        # Final Flash Draw screen black
        self.trigger_screen_black = False
    
    def activate_skill(self, skill_type, opponent, particles, shockwaves):
        """Activate a skill move."""
        self.active_skill = skill_type
        self.skill_timer = 0
        self.trail_positions = []
        
        if skill_type == SkillType.DASH_SLASH:
            dx = opponent.x - self.x
            dy = opponent.y - self.y
            dist = max(1, math.hypot(dx, dy))
            self.skill_data['dash_angle'] = math.atan2(dy, dx)
            self.skill_data['duration'] = 15
            # Boost velocity toward opponent
            self.vx = (dx / dist) * 28
            self.vy = (dy / dist) * 28
            # Store initial position for trail
            self.trail_positions = [(self.x, self.y)]
        
        elif skill_type == SkillType.SPIN_CUTTER:
            self.skill_data['duration'] = 50
            self.skill_data['spin_speed'] = 0.7
            self.skill_data['pull_phase'] = True  # Pull enemies first
            self.skill_data['ring_timer'] = 0
        
        elif skill_type == SkillType.GROUND_SLAM:
            self.skill_data['phase'] = 'rise'
            self.skill_data['duration'] = 35
            self.skill_data['start_y'] = self.y
        
        elif skill_type == SkillType.SHIELD:
            self.has_shield = True
            self.shield_parry_window = 20  # Active parry for ~0.33 seconds
            self.active_skill = None
        
        elif skill_type == SkillType.PHANTOM_CROSS:
            # Calculate position behind opponent
            dx = opponent.x - self.x
            dy = opponent.y - self.y
            dist = max(1, math.hypot(dx, dy))
            # Teleport behind
            behind_dist = 50
            self.skill_data['original_pos'] = (self.x, self.y)
            self.x = opponent.x + (dx / dist) * behind_dist
            self.y = opponent.y + (dy / dist) * behind_dist
            self.skill_data['target_pos'] = (opponent.x, opponent.y)
            self.skill_data['duration'] = 25
            self.skill_data['slash_frame'] = 8
            self.skill_data['damage_frame'] = 12  # Delayed damage
            self.vx = 0
            self.vy = 0
            # Emit teleport particles at original position
            ox, oy = self.skill_data['original_pos']
            particles.emit(ox, oy, PINK, count=15, size=5)
        
        elif skill_type == SkillType.BLADE_CYCLONE:
            self.skill_data['duration'] = 60
            self.skill_data['spin_speed'] = 0.8
            self.skill_data['hit_interval'] = 8  # Hit every 8 frames
            self.skill_data['hits_done'] = 0
            # Slow down during cyclone
            self.vx *= 0.3
            self.vy *= 0.3
        
        elif skill_type == SkillType.FINAL_FLASH_DRAW:
            self.skill_data['phase'] = 'sheath'  # sheath -> pause -> slash
            self.skill_data['duration'] = 45
            self.skill_data['sheath_frames'] = 20
            self.skill_data['pause_frames'] = 8
            self.skill_data['slash_frame'] = 30
            # Stop movement during iaido
            self.vx = 0
            self.vy = 0
            self.skill_data['target_angle'] = math.atan2(
                opponent.y - self.y, opponent.x - self.x
            )
    
    def update_skill(self, opponent, particles, shockwaves):
        """Update active skill."""
        if self.active_skill is None:
            return
        
        self.skill_timer += 1
        
        if self.active_skill == SkillType.DASH_SLASH:
            # Add trail positions
            if len(self.trail_positions) < 8:
                self.trail_positions.append((self.x, self.y))
            else:
                self.trail_positions.pop(0)
                self.trail_positions.append((self.x, self.y))
            
            # Emit trail particles
            if self.skill_timer % 2 == 0:
                particles.emit(self.x, self.y, self.color, count=3, size=3, lifetime=10)
            
            if self.skill_timer >= self.skill_data['duration']:
                self.active_skill = None
                self.trail_positions = []
        
        elif self.active_skill == SkillType.SPIN_CUTTER:
            if self.skill_timer < self.skill_data['duration']:
                self.sword_angle += self.skill_data['spin_speed']
                
                # Emit expanding slash rings every 10 frames
                self.skill_data['ring_timer'] += 1
                if self.skill_data['ring_timer'] >= 10:
                    self.skill_data['ring_timer'] = 0
                    ring_radius = 30 + (self.skill_timer / self.skill_data['duration']) * 50
                    particles.emit_ring(self.x, self.y, self.color, ring_radius, count=8)
                
                # Pull phase (first half) then knockback phase
                dist_to_opponent = math.hypot(opponent.x - self.x, opponent.y - self.y)
                if dist_to_opponent < 150:
                    angle_to_self = math.atan2(self.y - opponent.y, self.x - opponent.x)
                    if self.skill_timer < self.skill_data['duration'] // 2:
                        # Pull inward
                        pull_force = 2
                        opponent.vx -= math.cos(angle_to_self) * pull_force
                        opponent.vy -= math.sin(angle_to_self) * pull_force
                    elif self.skill_timer == self.skill_data['duration'] // 2:
                        # Launch outward
                        knockback_force = 15
                        opponent.vx += math.cos(angle_to_self) * knockback_force
                        opponent.vy += math.sin(angle_to_self) * knockback_force
            else:
                self.active_skill = None
        
        elif self.active_skill == SkillType.GROUND_SLAM:
            if self.skill_data['phase'] == 'rise':
                if self.skill_timer < 12:
                    self.vy = -8
                else:
                    self.skill_data['phase'] = 'fall'
            elif self.skill_data['phase'] == 'fall':
                if self.skill_timer < 22:
                    self.vy = 12
                else:
                    self.skill_data['phase'] = 'impact'
                    shockwaves.add(self.x, self.y, self.color, 130)
                    particles.emit_ring(self.x, self.y, self.color, 50, count=16)
                    # Emit debris particles
                    particles.emit_debris(self.x, self.y, count=12)
            elif self.skill_data['phase'] == 'impact':
                if self.skill_timer > self.skill_data['duration']:
                    self.active_skill = None
        
        elif self.active_skill == SkillType.PHANTOM_CROSS:
            # Draw X-slash at target on slash frame
            if self.skill_timer == self.skill_data['slash_frame']:
                tx, ty = self.skill_data['target_pos']
                particles.emit_cross_slash(tx, ty, PINK)
            
            if self.skill_timer >= self.skill_data['duration']:
                self.active_skill = None
        
        elif self.active_skill == SkillType.BLADE_CYCLONE:
            if self.skill_timer < self.skill_data['duration']:
                self.sword_angle += self.skill_data['spin_speed']
                
                # Emit vortex particles
                if self.skill_timer % 4 == 0:
                    angle = self.skill_timer * 0.3
                    px = self.x + math.cos(angle) * 40
                    py = self.y + math.sin(angle) * 40
                    particles.emit(px, py, YELLOW, count=2, size=3, lifetime=15)
                
                # Pull and lift enemies in range
                dist_to_opponent = math.hypot(opponent.x - self.x, opponent.y - self.y)
                if dist_to_opponent < 100:
                    # Slight lift
                    opponent.vy -= 0.5
                    # Pull toward center
                    angle_to_self = math.atan2(self.y - opponent.y, self.x - opponent.x)
                    opponent.vx += math.cos(angle_to_self) * 1.5
                    opponent.vy += math.sin(angle_to_self) * 1.5
            else:
                # Release with outward knockback
                dist_to_opponent = math.hypot(opponent.x - self.x, opponent.y - self.y)
                if dist_to_opponent < 120:
                    angle_away = math.atan2(opponent.y - self.y, opponent.x - self.x)
                    opponent.vx += math.cos(angle_away) * 12
                    opponent.vy += math.sin(angle_away) * 12
                self.active_skill = None
        
        elif self.active_skill == SkillType.FINAL_FLASH_DRAW:
            if self.skill_data['phase'] == 'sheath':
                # Point sword backward (sheathing)
                self.sword_angle = self.skill_data['target_angle'] + math.pi
                if self.skill_timer >= self.skill_data['sheath_frames']:
                    self.skill_data['phase'] = 'pause'
            
            elif self.skill_data['phase'] == 'pause':
                if self.skill_timer >= self.skill_data['sheath_frames'] + self.skill_data['pause_frames']:
                    self.skill_data['phase'] = 'slash'
                    self.trigger_screen_black = True  # Signal to main.py
            
            elif self.skill_data['phase'] == 'slash':
                # Instant slash toward opponent
                self.sword_angle = self.skill_data['target_angle']
                # Emit dramatic slash particles
                if self.skill_timer == self.skill_data['slash_frame']:
                    particles.emit(self.x, self.y, GOLD, count=20, size=5, lifetime=30)
                    shockwaves.add(self.x, self.y, GOLD, 100)
                
                if self.skill_timer >= self.skill_data['duration']:
                    self.active_skill = None
    
    def update_pending_damage(self, particles):
        """Process delayed damage effects."""
        new_pending = []
        for target, damage, angle, knockback, delay in self.pending_damage:
            if delay <= 0:
                target.take_damage(damage, angle, knockback, particles)
            else:
                new_pending.append((target, damage, angle, knockback, delay - 1))
        self.pending_damage = new_pending
    
    def update(self, opponent, arena_bounds, particles, shockwaves):
        """Update fighter - bounce-only movement."""
        self.update_skill(opponent, particles, shockwaves)
        self.update_pending_damage(particles)
        
        # Decrease timers
        if self.flash_timer > 0:
            self.flash_timer -= 1
        if self.attack_cooldown > 0:
            self.attack_cooldown -= 1
        if self.invincible > 0:
            self.invincible -= 1
        if self.shield_parry_window > 0:
            self.shield_parry_window -= 1
        
        # Apply minimal drag
        self.vx *= DRAG
        self.vy *= DRAG
        
        # Clamp velocity
        speed = math.hypot(self.vx, self.vy)
        max_vel = MAX_VELOCITY
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
        # Don't force movement during certain skills
        if self.active_skill not in [SkillType.PHANTOM_CROSS, SkillType.FINAL_FLASH_DRAW]:
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
        
        if self.active_skill not in [SkillType.SPIN_CUTTER, SkillType.BLADE_CYCLONE, 
                                      SkillType.FINAL_FLASH_DRAW]:
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
        
        # Draw dash trail
        if self.trail_positions:
            for i, (tx, ty) in enumerate(self.trail_positions):
                alpha = (i + 1) / len(self.trail_positions)
                trail_radius = int(self.radius * alpha * 0.7)
                if trail_radius > 0:
                    trail_color = tuple(int(c * alpha) for c in self.color)
                    pygame.draw.circle(surface, trail_color,
                                      (int(tx + ox), int(ty + oy)), trail_radius)
        
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
        
        # Shield indicator (with parry glow)
        if self.has_shield:
            shield_color = WHITE if self.shield_parry_window > 0 else GREEN
            pygame.draw.circle(surface, shield_color, 
                              (int(self.x + ox), int(self.y + oy)), 
                              self.radius + 8, 3)
        
        # Blade Cyclone vortex indicator
        if self.active_skill == SkillType.BLADE_CYCLONE:
            vortex_radius = 80 + math.sin(self.skill_timer * 0.3) * 10
            pygame.draw.circle(surface, YELLOW,
                              (int(self.x + ox), int(self.y + oy)),
                              int(vortex_radius), 2)
    
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
            # Spark/counter-flash effect on parry
            if self.shield_parry_window > 0:
                # Perfect parry - emit sparks
                particles.emit_sparks(self.x, self.y)
                self.flash_timer = 8  # Bright counter-flash
            else:
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
        self.trail_positions = []
        self.flash_timer = 0
        self.victory_bounce = 0
        self.has_shield = False
        self.shield_parry_window = 0
        self.invincible = 0
        self.attack_cooldown = 0
        self.pending_damage = []
        self.trigger_screen_black = False
