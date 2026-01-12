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
        
        # Locked state (during countdown)
        self.locked = False
        
        # Final Flash Draw fairness lock-in
        self.ffd_locked_in = False       # User is locked during charge
        self.ffd_lock_position = None    # Stored position during lock
        self.ffd_stunned = False         # Opponent is stunned during FFD
        
        # Spin Parry state
        self.spin_parry_active = False
        self.spin_parry_timer = 0
        self.spin_parry_window = 30  # ~0.5 seconds parry window
        self.spin_parry_recovery = 0  # Vulnerability after failed parry
        
        # Skill targeting - stores opponent position at skill activation
        self.skill_target_pos = None
        
        # 3-Hit Combo System
        # Combo: Left Slash -> Right Slash -> Pierce -> reset
        self.combo_step = 0       # 0=none, 1=left slash, 2=right slash, 3=pierce
        self.combo_timer = 0      # Active frames for current attack
        self.combo_recovery = 0   # Recovery frames after attack
        self.combo_timeout = 0    # Frames since last hit (reset combo if too long)
        
        # Combo constants (tunable for feel)
        self.COMBO_ACTIVE_FRAMES = 12    # How long attack hitbox is active
        self.COMBO_RECOVERY_FRAMES = 8   # Recovery after each attack
        self.COMBO_TIMEOUT_FRAMES = 25   # Reset combo if no hit within this time
        self.COMBO_PIERCE_RECOVERY = 18  # Pierce has longer recovery (risk/reward)
        
        # Combo damage multipliers
        self.COMBO_DAMAGE = {
            1: 1.0,  # Left Slash - base damage
            2: 1.2,  # Right Slash - slightly more
            3: 1.5,  # Pierce - high damage finisher
        }
        
        # Exact swing angles (in radians) - angles are relative to facing direction
        # Hit 1: Left -> Right Slash: 180° -> 45° (wide arc, 135° sweep)
        # Hit 2: Right -> Left Slash: 0° -> 135° (medium arc, 135° sweep)
        # Hit 3: Pierce: Straight 90° (narrow thrust)
        self.COMBO_SWING = {
            1: {
                'start': math.radians(180),  # Start from left/behind
                'end': math.radians(45),     # End at upper-right
                'arc': math.radians(135),    # Total sweep
            },
            2: {
                'start': math.radians(0),    # Start from front/right
                'end': math.radians(135),    # End at upper-left
                'arc': math.radians(135),    # Total sweep
            },
            3: {
                'start': math.radians(90),   # Straight thrust (down if facing right)
                'end': math.radians(90),     # No sweep for thrust
                'arc': math.radians(30),     # Narrow hitbox
            },
        }
        
        # Store current swing progress
        self.combo_swing_angle = 0  # Current sword angle during swing
    
    def activate_skill(self, skill_type, opponent, particles, shockwaves):
        """Activate a skill move. Skills always face and launch toward opponent."""
        self.active_skill = skill_type
        self.skill_timer = 0
        self.trail_positions = []
        
        # Reset combo when activating any skill
        self.combo_step = 0
        self.combo_timer = 0
        self.combo_recovery = 0
        self.combo_timeout = 0
        
        # Store opponent position for autotargeting (skills launch toward this)
        self.skill_target_pos = (opponent.x, opponent.y)
        
        # Face opponent at activation
        dx = opponent.x - self.x
        dy = opponent.y - self.y
        target_angle = math.atan2(dy, dx)
        self.sword_angle = target_angle
        
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
        
        elif skill_type == SkillType.SPIN_PARRY:
            # High-risk parry skill - enter spinning stance
            self.spin_parry_active = True
            self.spin_parry_timer = 0
            self.skill_data['duration'] = 40  # Total animation time
            self.skill_data['parry_window'] = 30  # Active parry frames
            self.skill_data['spin_speed'] = 0.6
            self.skill_data['parried'] = False
            # Slow down during parry stance
            self.vx *= 0.3
            self.vy *= 0.3
        
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
            # User lock-in: freeze position during charge
            self.ffd_locked_in = True
            self.ffd_lock_position = (self.x, self.y)
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
        
        elif self.active_skill == SkillType.SPIN_PARRY:
            # Spinning parry stance
            if self.skill_timer < self.skill_data['duration']:
                self.sword_angle += self.skill_data['spin_speed']
                self.spin_parry_timer += 1
                
                # Active parry window
                if self.spin_parry_timer <= self.skill_data['parry_window']:
                    self.spin_parry_active = True
                    # Emit subtle parry indicator particles
                    if self.skill_timer % 6 == 0:
                        particles.emit_ring(self.x, self.y, YELLOW, 35, count=6)
                else:
                    # Parry window expired - entering recovery
                    self.spin_parry_active = False
                    if not self.skill_data.get('parried'):
                        # Failed parry - enter vulnerability
                        self.spin_parry_recovery = 20  # Recovery frames
            else:
                # Skill complete
                self.active_skill = None
                self.spin_parry_active = False
                self.spin_parry_timer = 0
        
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
                # Autolock: continuously rotate toward opponent's current position
                target_angle = math.atan2(opponent.y - self.y, opponent.x - self.x)
                # Smooth rotation toward target with spin overlay
                angle_diff = ((target_angle - self.sword_angle + math.pi) % (2 * math.pi)) - math.pi
                self.sword_angle += angle_diff * 0.15 + self.skill_data['spin_speed']
                
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
            # Enforce user lock-in position throughout charge
            if self.ffd_locked_in and self.ffd_lock_position:
                self.x, self.y = self.ffd_lock_position
                self.vx = 0
                self.vy = 0
            
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
                    # Release user lock-in
                    self.ffd_locked_in = False
                    self.ffd_lock_position = None
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
        # Skip update if locked (during countdown)
        if self.locked:
            return
        
        # Skip update if stunned by Final Flash Draw
        if self.ffd_stunned:
            return
        
        self.update_skill(opponent, particles, shockwaves)
        self.update_pending_damage(particles)
        self.update_combo()  # Update combo timers and state
        
        # Decrease timers
        if self.flash_timer > 0:
            self.flash_timer -= 1
        if self.attack_cooldown > 0:
            self.attack_cooldown -= 1
        if self.invincible > 0:
            self.invincible -= 1
        if self.shield_parry_window > 0:
            self.shield_parry_window -= 1
        if self.spin_parry_recovery > 0:
            self.spin_parry_recovery -= 1
        
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
        
        if self.active_skill not in [SkillType.SPIN_PARRY, SkillType.BLADE_CYCLONE, 
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
        
        # Spin Parry indicator
        if self.spin_parry_active:
            parry_radius = 45 + math.sin(self.skill_timer * 0.4) * 5
            # Orange spinning ring
            from config import ORANGE
            pygame.draw.circle(surface, ORANGE,
                              (int(self.x + ox), int(self.y + oy)),
                              int(parry_radius), 3)
    
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
        self.vx = 0  # Will be set by main.py after countdown
        self.vy = 0
        self.radius = FIGHTER_RADIUS
        self.health = BASE_HEALTH
        self.sword_length = self.base_sword_length
        self.active_skill = None
        self.skill_timer = 0
        self.skill_data = {}
        self.skill_target_pos = None
        self.trail_positions = []
        self.flash_timer = 0
        self.victory_bounce = 0
        self.has_shield = False
        self.shield_parry_window = 0
        self.invincible = 0
        self.attack_cooldown = 0
        self.pending_damage = []
        self.trigger_screen_black = False
        self.locked = False
        self.ffd_locked_in = False
        self.ffd_lock_position = None
        self.ffd_stunned = False
        self.spin_parry_active = False
        self.spin_parry_timer = 0
        self.spin_parry_recovery = 0
        # Reset combo state
        self.combo_step = 0
        self.combo_timer = 0
        self.combo_recovery = 0
        self.combo_timeout = 0
    
    def check_spin_parry(self, attacker, particles):
        """Check if this fighter's Spin Parry successfully blocks an attack.
        Returns True if parry succeeded."""
        if not self.spin_parry_active:
            return False
        
        # Check if attacker's sword is within parry radius
        (_, _), (tip_x, tip_y) = attacker.get_sword_hitbox()
        dist = math.hypot(tip_x - self.x, tip_y - self.y)
        parry_radius = 55  # Slightly larger than visual indicator
        
        if dist < parry_radius:
            # Parry successful! Scale knockback based on attacker's combo step
            self.skill_data['parried'] = True
            self.spin_parry_active = False
            
            # Knockback scales with combo step (Pierce = massive punish)
            base_knockback = 15
            if attacker.combo_step == 3:  # Pierce
                knockback_mult = 2.0  # Massive punish
            elif attacker.combo_step == 2:  # Right slash
                knockback_mult = 1.3
            else:
                knockback_mult = 1.0
            
            # Visual effects
            particles.emit_sparks(self.x, self.y)
            particles.emit_ring(self.x, self.y, YELLOW, 40, count=12)
            self.flash_timer = 8
            
            # Knockback attacker
            angle_to_attacker = math.atan2(attacker.y - self.y, attacker.x - self.x)
            attacker.vx = math.cos(angle_to_attacker) * base_knockback * knockback_mult
            attacker.vy = math.sin(angle_to_attacker) * base_knockback * knockback_mult
            
            # Reset attacker's combo
            attacker.combo_step = 0
            attacker.combo_timer = 0
            attacker.combo_recovery = 15  # Brief stun
            
            return True
        
        return False
    
    # ===== 3-Hit Combo System =====
    
    def start_combo_attack(self, opponent):
        """Initiate or continue the combo chain. Returns True if attack started."""
        # Can't attack during skill, recovery, or cooldown
        if self.active_skill is not None:
            return False
        if self.combo_recovery > 0:
            return False
        if self.attack_cooldown > 0:
            return False
        if self.locked:
            return False
        
        # Advance combo step (1 -> 2 -> 3 -> 1)
        if self.combo_step == 0 or self.combo_timeout > self.COMBO_TIMEOUT_FRAMES:
            self.combo_step = 1  # Start fresh
        else:
            self.combo_step = (self.combo_step % 3) + 1
        
        self.combo_timer = self.COMBO_ACTIVE_FRAMES
        self.combo_timeout = 0
        
        # Get base facing direction toward opponent
        dx = opponent.x - self.x
        dy = opponent.y - self.y
        base_angle = math.atan2(dy, dx)
        
        # Apply starting angle from COMBO_SWING (relative to facing)
        swing_data = self.COMBO_SWING[self.combo_step]
        self.combo_swing_angle = base_angle + swing_data['start']
        self.sword_angle = self.combo_swing_angle
        
        return True
    
    def update_combo(self):
        """Update combo timers and state. Called each frame."""
        if self.combo_timer > 0:
            self.combo_timer -= 1
            
            swing_data = self.COMBO_SWING.get(self.combo_step, {})
            
            if self.combo_step in [1, 2]:
                # Animate sword swing from start to end angle
                total_sweep = swing_data.get('arc', math.radians(90))
                swing_per_frame = total_sweep / self.COMBO_ACTIVE_FRAMES
                
                if self.combo_step == 1:
                    # Hit 1: Left to right (decreasing angle: 180° -> 45°)
                    self.sword_angle -= swing_per_frame
                else:
                    # Hit 2: Right to left (increasing angle: 0° -> 135°)
                    self.sword_angle += swing_per_frame
            # Pierce (step 3) doesn't swing - stays fixed
            
            if self.combo_timer == 0:
                # Attack ended - enter recovery
                if self.combo_step == 3:
                    self.combo_recovery = self.COMBO_PIERCE_RECOVERY
                else:
                    self.combo_recovery = self.COMBO_RECOVERY_FRAMES
        
        if self.combo_recovery > 0:
            self.combo_recovery -= 1
        
        # Count frames since last hit for timeout
        if self.combo_step > 0 and self.combo_timer == 0 and self.combo_recovery == 0:
            self.combo_timeout += 1
            if self.combo_timeout > self.COMBO_TIMEOUT_FRAMES:
                self.combo_step = 0  # Reset combo
    
    def is_combo_active(self):
        """Check if currently in an active combo attack frame."""
        return self.combo_timer > 0
    
    def get_combo_damage_mult(self):
        """Get damage multiplier for current combo step."""
        return self.COMBO_DAMAGE.get(self.combo_step, 1.0)
    
    def get_combo_arc(self):
        """Get arc width for current combo step hitbox."""
        swing_data = self.COMBO_SWING.get(self.combo_step, {})
        return swing_data.get('arc', math.radians(60))
    
    def on_combo_hit(self):
        """Called when combo attack successfully hits. Resets timeout."""
        self.combo_timeout = 0
    
    def on_combo_blocked(self):
        """Called when combo is blocked by shield. Resets combo."""
        self.combo_step = 0
        self.combo_timer = 0
        self.combo_recovery = 12  # Brief stagger
    
    def on_take_damage_combo_reset(self):
        """Called when taking damage. Resets combo."""
        self.combo_step = 0
        self.combo_timer = 0
        self.combo_recovery = 0
        self.combo_timeout = 0
    
    def check_sword_clash(self, opponent, particles):
        """Check if this fighter's basic attack clashes with opponent's skill.
        Returns skill type if clash occurred, None otherwise.
        Only triggers when THIS fighter is mid-combo attack."""
        if not self.is_combo_active():
            return None
        
        # Only check when opponent has an active skill (not Final Flash Draw)
        if opponent.active_skill is None:
            return None
        if opponent.active_skill == SkillType.FINAL_FLASH_DRAW:
            return None  # Cannot be clashed
        
        # Check if sword arc intersects skill hitbox
        # Use sword tip position
        (_, _), (tip_x, tip_y) = self.get_sword_hitbox()
        
        # Calculate distance to opponent (skill center)
        dist = math.hypot(tip_x - opponent.x, tip_y - opponent.y)
        clash_radius = 60  # Tunable
        
        if dist < clash_radius:
            # CLASH! Return the skill type for specific handling
            clashed_skill = opponent.active_skill
            
            # Visual feedback
            clash_x = (tip_x + opponent.x) / 2
            clash_y = (tip_y + opponent.y) / 2
            particles.emit(clash_x, clash_y, WHITE, count=8, size=4, lifetime=8)
            
            return clashed_skill
        
        return None
    
    def check_sword_on_sword_parry(self, opponent):
        """Check if this fighter's sword collides with opponent's sword.
        Returns True if both swords intersect during active combo attacks.
        This triggers a mutual parry - no damage, combo reset for both."""
        # Both fighters must be mid-combo attack
        if not self.is_combo_active():
            return False
        if not opponent.is_combo_active():
            return False
        
        # Get both sword hitboxes
        (my_base_x, my_base_y), (my_tip_x, my_tip_y) = self.get_sword_hitbox()
        (opp_base_x, opp_base_y), (opp_tip_x, opp_tip_y) = opponent.get_sword_hitbox()
        
        # Line segment intersection check
        # Simplified: check if sword tips are close to each other's sword lines
        
        # Check if my tip is close to opponent's sword line
        my_tip_to_opp_line = self._point_to_line_distance(
            my_tip_x, my_tip_y,
            opp_base_x, opp_base_y, opp_tip_x, opp_tip_y
        )
        
        # Check if opponent's tip is close to my sword line
        opp_tip_to_my_line = self._point_to_line_distance(
            opp_tip_x, opp_tip_y,
            my_base_x, my_base_y, my_tip_x, my_tip_y
        )
        
        # Parry threshold
        parry_distance = 15  # Tunable
        
        if my_tip_to_opp_line < parry_distance or opp_tip_to_my_line < parry_distance:
            return True
        
        return False
    
    def _point_to_line_distance(self, px, py, x1, y1, x2, y2):
        """Calculate distance from point (px, py) to line segment (x1,y1)-(x2,y2)."""
        # Line segment vector
        dx = x2 - x1
        dy = y2 - y1
        
        # Handle zero-length line
        length_sq = dx * dx + dy * dy
        if length_sq < 0.001:
            return math.hypot(px - x1, py - y1)
        
        # Project point onto line, clamped to segment
        t = max(0, min(1, ((px - x1) * dx + (py - y1) * dy) / length_sq))
        
        # Closest point on segment
        closest_x = x1 + t * dx
        closest_y = y1 + t * dy
        
        return math.hypot(px - closest_x, py - closest_y)


