"""
Fighter with bounce-only movement and Beyblade constant-spin combat.
Supports multiple weapon types via WEAPON_CONFIGS.
"""

import pygame
import math
import random

from config import (
    WHITE, BLACK,
    FIGHTER_RADIUS, SWORD_WIDTH, BASE_HEALTH,
    DRAG, MAX_VELOCITY, MIN_VELOCITY, BOUNCE_ENERGY,
    WALL_BOOST_STRENGTH, TRAIL_LENGTH, TRAIL_FADE_RATE,
    GLOW_ALPHA, GLOW_RADIUS_MULT,
    WEAPON_CONFIGS
)

from renderers.fighter_renderer import FighterRenderer

class Fighter:
    def __init__(self, x, y, color, color_bright, is_blue=True, weapon="sword"):
        self.x = x
        self.y = y
        self.start_x = x
        self.start_y = y
        self.vx = random.uniform(-8, 8)
        self.vy = random.uniform(-8, 8)
        self.radius = FIGHTER_RADIUS
        self.color = color
        self.color_bright = color_bright
        self.is_blue = is_blue
        self.health = BASE_HEALTH
        self.max_health = BASE_HEALTH
        self.speed_multiplier = 1.0

        # Weapon
        self.weapon = weapon
        self.weapon_config = WEAPON_CONFIGS[weapon]
        
        # Body rotation — the whole unit (body + sword) spins together.
        # sword_angle is kept in sync so combat_manager.py needs no changes.
        self.rotation_angle = 0.0
        self.sword_angle = 0.0          # always == rotation_angle
        self.sword_length = self.weapon_config["sword_length"]
        self.base_sword_length = self.sword_length
        self.last_sword_angle = 0.0
        self.sword_angular_velocity = 0.0
        
        # Beyblade spin state
        self.spin_direction = 1 if self.is_blue else -1
        self.base_spin_speed = 0.25 * self.weapon_config.get("spin_speed_mult", 1.0)
        self.spin_speed = self.base_spin_speed
        self.parry_cooldown = 0
        self.max_parry_energy = 100.0
        self.parry_energy = self.max_parry_energy
        self.energy_regen_rate = 0.5
        self.parry_cost = 35.0
        self.sword_trail = []
        
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
        self.last_hit_frame = -100
        
        self.trail = []
        
        self._renderer = FighterRenderer(weapon)


    def update_rotation(self, opponent=None, frame_count=0):
        """
        Spin the whole body. The sword is rigidly attached at angle 0 relative
        to the body, so rotation_angle drives everything.
        """
        self.rotation_angle += self.spin_speed * self.spin_direction
        # Clamp to [-pi, pi]
        if self.rotation_angle > math.pi:
            self.rotation_angle -= 2 * math.pi
        elif self.rotation_angle < -math.pi:
            self.rotation_angle += 2 * math.pi

        # Keep sword_angle in sync — combat_manager uses this for hitboxes
        self.sword_angle = self.rotation_angle

        if self.parry_cooldown > 0:
            self.parry_cooldown -= 1


    def update(self, opponent, arena_bounds, particles, shockwaves):
        """Update fighter — bounce-only movement with ninja wall boosts."""
        if self.locked:
            return
        
        self.parry_energy = min(self.max_parry_energy, self.parry_energy + self.energy_regen_rate)
        
        self.trail.insert(0, (self.x, self.y))
        if len(self.trail) > TRAIL_LENGTH:
            self.trail.pop()
        
        self.last_sword_angle = self.sword_angle
        self.update_rotation(opponent, 0)
        delta = (self.sword_angle - self.last_sword_angle + math.pi) % (2 * math.pi) - math.pi
        self.sword_angular_velocity = delta
        
        if self.flash_timer > 0: self.flash_timer -= 1
        if self.attack_cooldown > 0: self.attack_cooldown -= 1
        if self.invincible > 0: self.invincible -= 1

        self.vx *= DRAG
        self.vy *= DRAG
        
        speed = math.hypot(self.vx, self.vy)
        max_vel = MAX_VELOCITY * self.speed_multiplier
        if speed > max_vel:
            self.vx = (self.vx / speed) * max_vel
            self.vy = (self.vy / speed) * max_vel
        
        min_vel = MIN_VELOCITY * self.speed_multiplier
        if speed < min_vel and speed > 0:
            self.vx = (self.vx / speed) * min_vel
            self.vy = (self.vy / speed) * min_vel
        elif speed == 0:
            a = random.uniform(0, 2 * math.pi)
            self.vx = math.cos(a) * min_vel
            self.vy = math.sin(a) * min_vel
        
        self.x += self.vx
        self.y += self.vy
        
        ax, ay, aw, ah = arena_bounds
        r = self.radius
        cx = ax + aw / 2
        cy = ay + ah / 2
        
        if self.x - r < ax:
            self.x = ax + r
            self.vx = abs(self.vx) * BOUNCE_ENERGY
            if self.x < cx: self.vx += WALL_BOOST_STRENGTH
        if self.x + r > ax + aw:
            self.x = ax + aw - r
            self.vx = -abs(self.vx) * BOUNCE_ENERGY
            if self.x > cx: self.vx -= WALL_BOOST_STRENGTH
        if self.y - r < ay:
            self.y = ay + r
            self.vy = abs(self.vy) * BOUNCE_ENERGY
            if self.y < cy: self.vy += WALL_BOOST_STRENGTH
        if self.y + r > ay + ah:
            self.y = ay + ah - r
            self.vy = -abs(self.vy) * BOUNCE_ENERGY
            if self.y > cy: self.vy -= WALL_BOOST_STRENGTH
        
        if self.victory_bounce > 0:
            self.victory_bounce -= 1
            self.y += math.sin(self.victory_bounce * 0.4) * 5
    
    def get_sword_hitbox(self):
        """Get sword collision points — uses sword_angle (== rotation_angle)."""
        r = self.radius
        base_x = self.x + math.cos(self.sword_angle) * (r + 3)
        base_y = self.y + math.sin(self.sword_angle) * (r + 3)
        tip_x = base_x + math.cos(self.sword_angle) * self.sword_length
        tip_y = base_y + math.sin(self.sword_angle) * self.sword_length
        return (base_x, base_y), (tip_x, tip_y)
    
    def get_attack_damage_multiplier(self):
        return self.weapon_config.get("damage_mult", 1.0)

    def draw(self, surface, offset=(0, 0)):
        self._renderer.render(self, surface, offset)

    def take_damage(self, amount, knockback_angle, knockback_force, particles):
        if self.invincible > 0:
            return False
        self.health -= amount
        self.flash_timer = 6
        self.invincible = 20
        self.vx += math.cos(knockback_angle) * knockback_force
        self.vy += math.sin(knockback_angle) * knockback_force
        return True
    
    def reset(self):
        self.x = self.start_x
        self.y = self.start_y
        self.vx = random.uniform(-8, 8)
        self.vy = random.uniform(-8, 8)
        self.radius = FIGHTER_RADIUS
        self.health = BASE_HEALTH

        self.rotation_angle = 0.0 if self.is_blue else math.pi
        self.sword_angle = self.rotation_angle
        self.last_sword_angle = self.rotation_angle

        self.sword_angular_velocity = 0.0
        self.sword_length = self.base_sword_length
        
        self.spin_direction = 1 if self.is_blue else -1
        self.spin_speed = self.base_spin_speed
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
        self.health_bar_color = self.color
        
        self.last_hit_frame = -100
        self.trail.clear()