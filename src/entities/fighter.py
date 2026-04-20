"""
Simplified fighter with bounce-only movement and Beyblade constant-spin combat.
DVD logo style - fighters bounce around arena with always-spinning swords.
"""

import pygame
import math
import random

from config import (
    WHITE, BLACK,
    FIGHTER_RADIUS, SWORD_LENGTH, SWORD_WIDTH, BASE_HEALTH,
    DRAG, MAX_VELOCITY, MIN_VELOCITY, BOUNCE_ENERGY,
    WALL_BOOST_STRENGTH, TRAIL_LENGTH, TRAIL_FADE_RATE,
    GLOW_ALPHA, GLOW_RADIUS_MULT
)

from renderers.fighter_renderer import FighterRenderer

class Fighter:
    """Simplified fighter with wall-bounce movement and Beyblade spin combat."""
    
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
        self.speed_multiplier = 1.0
        
        # Sword
        self.sword_angle = 0
        self.sword_length = SWORD_LENGTH
        self.base_sword_length = SWORD_LENGTH
        self.last_sword_angle = 0
        self.sword_angular_velocity = 0.0
        
        # Beyblade spin state
        self.spin_direction = 1 if self.is_blue else -1
        self.spin_speed = 0.25
        self.parry_cooldown = 0
        self.max_parry_energy = 100.0
        self.parry_energy = self.max_parry_energy
        self.energy_regen_rate = 0.5  # Recharges slowly over time
        self.parry_cost = 35.0  # ~3 rapid parries before a Guard Break
        self.sword_trail = []  # Tip positions for clean visual trail
        
        # Visual
        self.flash_timer = 0
        self.victory_bounce = 0
        self.render_color = self.color
        self.render_color_bright = self.color_bright
        self.health_bar_color = self.color
        
        # Cooldowns
        self.attack_cooldown = 0
        self.invincible = 0
        
        # Locked state (during countdown)
        self.locked = False
        
        # Legacy hit tracking
        self.last_hit_frame = -100     # Frame of last successful hit
        
        self.trail = []
        
        self._renderer = FighterRenderer()

    def update_rotation(self, opponent=None, frame_count=0):
        """Update sword angle - constant Beyblade spin with parry reversal."""
        self.sword_angle += self.spin_speed * self.spin_direction
        if self.sword_angle > math.pi:
            self.sword_angle -= 2 * math.pi
        elif self.sword_angle < -math.pi:
            self.sword_angle += 2 * math.pi
        
        if self.parry_cooldown > 0:
            self.parry_cooldown -= 1
    

    
    def update(self, opponent, arena_bounds, particles, shockwaves):
        """Update fighter - bounce-only movement with ninja wall boosts."""
        # Skip update if locked (during countdown)
        if self.locked:
            return
        
        self.parry_energy = min(self.max_parry_energy, self.parry_energy + self.energy_regen_rate)
        
        # Update trail (store previous positions for motion trail effect)
        self.trail.insert(0, (self.x, self.y))
        if len(self.trail) > TRAIL_LENGTH:
            self.trail.pop()
        
        self.last_sword_angle = self.sword_angle
        self.update_rotation(opponent, 0)  # Sword faces opponent with combo offset
        
        # Calculate angular velocity (handles pi wraparound perfectly)
        delta_angle = (self.sword_angle - self.last_sword_angle + math.pi) % (2 * math.pi) - math.pi
        self.sword_angular_velocity = delta_angle
        
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
        
        # Clamp velocity (scaling limits with speed_multiplier)
        speed = math.hypot(self.vx, self.vy)
        max_vel = MAX_VELOCITY * self.speed_multiplier
        if speed > max_vel:
            self.vx = (self.vx / speed) * max_vel
            self.vy = (self.vy / speed) * max_vel
        
        # Ensure minimum velocity (DVD logo always moving)
        min_vel = MIN_VELOCITY * self.speed_multiplier
        if speed < min_vel and speed > 0:
            self.vx = (self.vx / speed) * min_vel
            self.vy = (self.vy / speed) * min_vel
        elif speed == 0:
            # Give random velocity if stopped
            angle = random.uniform(0, 2 * math.pi)
            self.vx = math.cos(angle) * min_vel
            self.vy = math.sin(angle) * min_vel
        
        # Update position
        self.x += self.vx
        self.y += self.vy
        
        # Wall collision with perfect bounce (DVD logo style)
        ax, ay, aw, ah = arena_bounds
        r = self.radius
        
        # Left wall
        if self.x - r < ax:
            self.x = ax + r
            self.vx = abs(self.vx) * BOUNCE_ENERGY
            # Ninja wall boost toward center
            center_x = ax + aw / 2
            if self.x < center_x:
                self.vx += WALL_BOOST_STRENGTH
        
        # Right wall
        if self.x + r > ax + aw:
            self.x = ax + aw - r
            self.vx = -abs(self.vx) * BOUNCE_ENERGY
            center_x = ax + aw / 2
            if self.x > center_x:
                self.vx -= WALL_BOOST_STRENGTH
        
        # Top wall
        if self.y - r < ay:
            self.y = ay + r
            self.vy = abs(self.vy) * BOUNCE_ENERGY
            center_y = ay + ah / 2
            if self.y < center_y:
                self.vy += WALL_BOOST_STRENGTH
        
        # Bottom wall
        if self.y + r > ay + ah:
            self.y = ay + ah - r
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
        r = self.radius
        scaled_sword_length = self.sword_length
        
        base_x = self.x + math.cos(self.sword_angle) * (r + 3)
        base_y = self.y + math.sin(self.sword_angle) * (r + 3)
        tip_x = base_x + math.cos(self.sword_angle) * scaled_sword_length
        tip_y = base_y + math.sin(self.sword_angle) * scaled_sword_length
        return (base_x, base_y), (tip_x, tip_y)
    
    def get_attack_damage_multiplier(self):
        """Get damage multiplier (constant for Beyblade mode)."""
        return 1.0
    

    def draw(self, surface, offset=(0, 0)):
        """Draw fighter with glow, trail, and neon effects using the dedicated renderer."""
        self._renderer.render(self, surface, offset)
    

    
    def take_damage(self, amount, knockback_angle, knockback_force, particles):
        """Take damage and knockback."""
        if self.invincible > 0:
            return False
        
        self.health -= amount
        self.flash_timer = 6
        self.invincible = 45
        
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
        self.last_sword_angle = 0
        self.sword_angular_velocity = 0.0
        self.sword_length = self.base_sword_length
        
        # Reset Beyblade spin state
        self.spin_direction = 1 if self.is_blue else -1
        self.spin_speed = 0.25
        self.parry_cooldown = 0
        self.parry_energy = self.max_parry_energy
        self.sword_trail = []
        
        self.flash_timer = 0
        self.victory_bounce = 0
        self.attack_cooldown = 0
        self.invincible = 0
        self.locked = False

        self.render_color = self.color
        self.render_color_bright = self.color_bright
        self.health_bar_color
        
        self.last_hit_frame = -100
        
        self.trail.clear()
