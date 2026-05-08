"""
Fighter module for the AlgoRot battle simulation.

This module defines the Fighter class, which implements a "Beyblade-style" 
combatant. Movement is purely momentum-based with wall bounces, and 
combat is driven by constant weapon rotation rather than manual inputs.
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
    WEAPON_CONFIGS, MOMENTUM_MAX_STACKS,
    BASE_PARRY_ENERGY, PARRY_DRAIN_BASE, PARRY_REGEN_RATE,
    PARRY_COOLDOWN_FRAMES, GUARD_BREAK_STUN_FRAMES
)

from renderers.fighter_renderer import FighterRenderer

class Fighter:
    """Represents a combatant in the arena.

    The Fighter handles its own physics, state management (health, energy, 
    momentum), and weapon rotation logic.

    Attributes:
        weapon (str): The key for the weapon configuration in WEAPON_CONFIGS.
        parry_energy (float): The current resource pool used to block attacks.
        guard_break_stun (int): Frames remaining in a paralyzed state.
        momentum (int): Cumulative stacks rewarding aggressive successful hits.
        rotation_since_last_hit (float): Tracks angular distance to scale damage.
    """

    def __init__(self, x: float, y: float, color: tuple, color_bright: tuple, is_blue: bool = True, weapon: str = "sword"):
        """Initializes the fighter with starting position and weapon archetype."""
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

        # Weapon Configuration
        self.weapon = weapon
        self.weapon_config = WEAPON_CONFIGS[weapon]

        # Health scaling based on weapon weight/archetype
        weapon_health = self.weapon_config.get('base_health', BASE_HEALTH)
        self.health = weapon_health
        self.max_health = weapon_health

        # Speed_Multiplier is used by chaos (HYPER SPEED sets it to 2.5, resets to 1.0)
        # weapon_speed_mult is the weapon's intrinsic movement modifier — kept separate
        # so chaos reset doesn't erase the weapon's base speed
        self.speed_multiplier = 1.0
        self.weapon_speed_mult = self.weapon_config.get('move_speed_mult', 1.0)

        # Per-Weapon Trail Length for visual identity
        self.trail_length = self.weapon_config.get('trail_length', TRAIL_LENGTH)

        # Body & Sword Rotation
        self.rotation_angle = 0.0
        self.sword_angle = 0.0
        self.sword_length = self.weapon_config["sword_length"]
        self.base_sword_length = self.sword_length
        self.last_sword_angle = 0.0
        self.sword_angular_velocity = 0.0

        # Beyblade spin state
        self.spin_direction = 1 if self.is_blue else -1
        self.base_spin_speed = 0.25 * self.weapon_config.get("spin_speed_mult", 1.0)
        self.spin_speed = self.base_spin_speed
        self.parry_cooldown = 0
        self.max_parry_energy = float(BASE_PARRY_ENERGY)
        self.parry_energy = self.max_parry_energy
        self.energy_regen_rate = PARRY_REGEN_RATE
        self.parry_cost = float(PARRY_DRAIN_BASE)
        self.sword_trail = []

        # Guard break stun (weapon stops spinning, heavy drag applied)
        self.guard_break_stun = 0
        self.regen_suppress_timer = 0

        # Momentum: rewards consecutive hits
        self.momentum = 0

        # Rotation tracking for damage scaling (full spins deal more damage)
        self.rotation_since_last_hit = 0.0

        # Visual states
        self.flash_timer = 0
        self.victory_bounce = 0
        self.render_color = self.color
        self.render_color_bright = self.color_bright
        self.health_bar_color = self.color

        # System cooldowns
        self.attack_cooldown = 0
        self.invincible = 0

        # Operational state
        self.locked = False
        self.last_hit_frame = -100
        self.trail = []

        self._renderer = FighterRenderer(weapon)


    def update_rotation(self, opponent=None, frame_count: int = 0):
        """Updates the angular position of the fighter's weapon.

        Weapon rotation is disabled during guard break stun to visually signal 
        vulnerability. Rotation since last hit is tracked to reward 'full' 
        swings with higher damage.

        Args:
            opponent: The enemy fighter (optional, used for future AI/tracking).
            frame_count: Current simulation frame.
        """
        # During guard break stun, weapon hangs limp — no rotation
        if self.guard_break_stun > 0:
            if self.parry_cooldown > 0:
                self.parry_cooldown -= 1
            return

        delta_rot = self.spin_speed * self.spin_direction
        self.rotation_angle += delta_rot
        
        # Normalize angle to [-π, π] range
        if self.rotation_angle > math.pi:
            self.rotation_angle -= 2 * math.pi
        elif self.rotation_angle < -math.pi:
            self.rotation_angle += 2 * math.pi

        # Accumulate rotation distance since last contact (capped at 2π)
        self.rotation_since_last_hit = min(
            2 * math.pi, self.rotation_since_last_hit + abs(delta_rot)
        )

        self.sword_angle = self.rotation_angle

        if self.parry_cooldown > 0:
            self.parry_cooldown -= 1


    def update(self, opponent, arena_bounds: tuple, particles, shockwaves):
        """Updates physics, energy regeneration, and state timers.

        Movement follows a 'billiard' style with constant friction (DRAG) and 
        wall boosts. Energy regeneration is dynamically scaled based on 
        current HP ratio to make guard breaks more frequent as health declines.

        Args:
            opponent: The opposing fighter.
            arena_bounds: (x, y, w, h) of the playable area.
            particles: Global particle manager.
            shockwaves: Global shockwave manager.
        """
        if self.locked:
            return

        # Energy Management Logic
        if self.regen_suppress_timer > 0:
            self.regen_suppress_timer -= 1
        elif self.guard_break_stun <= 0:
            hp_ratio = max(0.0, self.health / self.max_health)
            # Energy regen scales from 100% (Full HP) down to 35% (Low HP).
            # This ensures that "lategame" clashes are more likely to result in breaks.
            effective_regen = self.energy_regen_rate * (0.35 + 0.65 * hp_ratio)
            self.parry_energy = min(self.max_parry_energy, self.parry_energy + effective_regen)

        # Movement History (Visual Trail)
        self.trail.insert(0, (self.x, self.y))
        if len(self.trail) > self.trail_length:
            self.trail.pop()

        self.last_sword_angle = self.sword_angle
        self.update_rotation(opponent, 0)
        
        # Calculate angular velocity for collision impact calculations
        delta = (self.sword_angle - self.last_sword_angle + math.pi) % (2 * math.pi) - math.pi
        self.sword_angular_velocity = delta

        # Timers
        if self.flash_timer > 0:     self.flash_timer -= 1
        if self.attack_cooldown > 0: self.attack_cooldown -= 1
        if self.invincible > 0:      self.invincible -= 1

        # Guard break stun: applies heavy drag and slides the fighter to a halt
        if self.guard_break_stun > 0:
            self.guard_break_stun -= 1
            if self.guard_break_stun == 0:
                self.regen_suppress_timer = 45  # 0.75s suppression window after stun ends
            self.vx *= 0.88
            self.vy *= 0.88
            self.x += self.vx
            self.y += self.vy
            
            # Simple clamping without wall boosts during stun
            ax, ay, aw, ah = arena_bounds
            r = self.radius
            if self.x - r < ax: self.x = ax + r; self.vx = 0
            if self.x + r > ax + aw: self.x = ax + aw - r; self.vx = 0
            if self.y - r < ay: self.y = ay + r; self.vy = 0
            if self.y + r > ay + ah: self.y = ay + ah - r; self.vy = 0
            return

        # Normal Physics Update
        self.vx *= DRAG
        self.vy *= DRAG

        combined_mult = self.speed_multiplier * self.weapon_speed_mult

        speed = math.hypot(self.vx, self.vy)
        max_vel = MAX_VELOCITY * combined_mult
        if speed > max_vel:
            self.vx = (self.vx / speed) * max_vel
            self.vy = (self.vy / speed) * max_vel

        min_vel = MIN_VELOCITY * combined_mult
        if speed < min_vel and speed > 0:
            self.vx = (self.vx / speed) * min_vel
            self.vy = (self.vy / speed) * min_vel
        elif speed == 0:
            a = random.uniform(0, 2 * math.pi)
            self.vx = math.cos(a) * min_vel
            self.vy = math.sin(a) * min_vel

        self.x += self.vx
        self.y += self.vy

        # Wall Bounce & Ninja Boost Logic
        ax, ay, aw, ah = arena_bounds
        r = self.radius
        cx = ax + aw / 2
        cy = ay + ah / 2

        # Bounces apply a fixed BOUNCE_ENERGY multiplier and a WALL_BOOST_STRENGTH push
        # toward the center to keep fighters engaged in the middle of the arena.
        if self.x - r < ax:
            self.x = ax + r
            self.vx = abs(self.vx) * BOUNCE_ENERGY
            if self.x < cx: self.vx += WALL_BOOST_STRENGTH
            if abs(self.vy) < 0.5:
                self.vy += random.uniform(-0.5, 0.5) or 0.3
        if self.x + r > ax + aw:
            self.x = ax + aw - r
            self.vx = -abs(self.vx) * BOUNCE_ENERGY
            if self.x > cx: self.vx -= WALL_BOOST_STRENGTH
            if abs(self.vy) < 0.5:
                self.vy += random.uniform(-0.5, 0.5) or 0.3
        if self.y - r < ay:
            self.y = ay + r
            self.vy = abs(self.vy) * BOUNCE_ENERGY
            if self.y < cy: self.vy += WALL_BOOST_STRENGTH
            if abs(self.vx) < 0.5:
                self.vx += random.uniform(-0.5, 0.5) or 0.3
        if self.y + r > ay + ah:
            self.y = ay + ah - r
            self.vy = -abs(self.vy) * BOUNCE_ENERGY
            if self.y > cy: self.vy -= WALL_BOOST_STRENGTH
            if abs(self.vx) < 0.5:
                self.vx += random.uniform(-0.5, 0.5) or 0.3

        if self.victory_bounce > 0:
            self.victory_bounce -= 1
            self.y += math.sin(self.victory_bounce * 0.4) * 5


    def get_sword_hitbox(self) -> tuple:
        """Calculates the line segment representing the weapon's reach.

        Returns:
            A tuple of ((base_x, base_y), (tip_x, tip_y)).
        """
        r = self.radius
        base_x = self.x + math.cos(self.sword_angle) * (r + 3)
        base_y = self.y + math.sin(self.sword_angle) * (r + 3)
        tip_x = base_x + math.cos(self.sword_angle) * self.sword_length
        tip_y = base_y + math.sin(self.sword_angle) * self.sword_length
        return (base_x, base_y), (tip_x, tip_y)


    def get_attack_damage_multiplier(self) -> float:
        """Retrieves the damage multiplier from the weapon configuration."""
        return self.weapon_config.get("damage_mult", 1.0)


    def draw(self, surface: pygame.Surface, offset=(0, 0)):
        """Renders the complete fighter entity."""
        self._renderer.render(self, surface, offset)


    def draw_body_only(self, surface: pygame.Surface, offset=(0, 0)):
        """Renders only the fighter's body, omitting the weapon."""
        self._renderer.render_body_only(self, surface, offset)


    def take_damage(self, amount: float, knockback_angle: float, knockback_force: float, particles) -> bool:
        """Applies damage and knockback to the fighter.

        Resets momentum and triggers an invincibility window.

        Args:
            amount: HP to subtract.
            knockback_angle: Direction of push in radians.
            knockback_force: Intensity of the push.
            particles: Global particle manager for impact effects.

        Returns:
            True if damage was successfully applied, False if invincible.
        """
        if self.invincible > 0:
            return False
        self.health -= amount
        self.flash_timer = 6
        self.invincible = 45
        self.vx += math.cos(knockback_angle) * knockback_force
        self.vy += math.sin(knockback_angle) * knockback_force
        self.momentum = 0
        return True


    def reset(self):
        """Restores the fighter to its initial spawning state."""
        self.x = self.start_x
        self.y = self.start_y
        self.vx = random.uniform(-8, 8)
        self.vy = random.uniform(-8, 8)
        self.radius = FIGHTER_RADIUS
        self.health = self.max_health

        self.rotation_angle = 0.0 if self.is_blue else math.pi
        self.sword_angle = self.rotation_angle
        self.last_sword_angle = self.rotation_angle

        self.sword_angular_velocity = 0.0
        self.sword_length = self.base_sword_length

        self.spin_direction = 1 if self.is_blue else -1
        self.spin_speed = self.base_spin_speed
        self.speed_multiplier = 1.0     # reset chaos override
        self.parry_cooldown = 0
        self.parry_energy = self.max_parry_energy
        self.sword_trail = []

        self.guard_break_stun = 0
        self.regen_suppress_timer = 0

        self.momentum = 0
        self.rotation_since_last_hit = 0.0

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

        