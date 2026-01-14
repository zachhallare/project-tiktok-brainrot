"""
Simplified fighter with bounce-only movement and 5 skill-based power-ups.
Constant weapon rotation with ninja wall boost physics.
DVD logo style - fighters bounce around arena with spinning swords.
"""

import pygame
import math
import random

from config import (
    SCREEN_WIDTH, SCREEN_HEIGHT, WHITE, GREEN, YELLOW, BLACK,
    FIGHTER_RADIUS, SWORD_LENGTH, SWORD_WIDTH, BASE_HEALTH,
    DRAG, MAX_VELOCITY, MIN_VELOCITY, BOUNCE_ENERGY, ARENA_MARGIN,
    WEAPON_ROTATION_SPEED, ROTATION_PARRY_DISTANCE, ROTATION_BODY_HIT_BONUS,
    WALL_BOOST_STRENGTH
)
from skills import SkillType


class Fighter:
    """Simplified fighter with wall-bounce movement and constant rotation."""
    
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
        
        # Locked state (during countdown)
        self.locked = False
        
        # Spin Parry state
        self.spin_parry_active = False
        self.spin_parry_timer = 0
        self.spin_parry_window = 30  # ~0.5 seconds parry window
        self.spin_parry_recovery = 0  # Vulnerability after failed parry
        
        # Skill targeting - stores opponent position at skill activation
        self.skill_target_pos = None
        
        # Rotational Weapon System - CONSTANT rotation (DVD logo style)
        # Sword always rotates, only paused during skills
        self.rotation_clockwise = True      # Direction of rotation
        self.last_hit_frame = -100          # Frame of last hit
        self.rotation_paused = False        # Paused during skills
        self.attack_recovery = 0            # Brief recovery after shield block
    
    def activate_skill(self, skill_type, opponent, particles, shockwaves):
        """Activate a skill move. Skills always face and launch toward opponent."""
        self.active_skill = skill_type
        self.skill_timer = 0
        self.trail_positions = []
        
        # Pause rotation when activating any skill
        self.is_attacking = False
        self.rotation_paused = True
        
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
        
        elif skill_type == SkillType.BLADE_CYCLONE:
            self.skill_data['duration'] = 60
            self.skill_data['spin_speed'] = 0.8
            self.skill_data['hit_interval'] = 8  # Hit every 8 frames
            self.skill_data['hits_done'] = 0
            # Slow down during cyclone
            self.vx *= 0.3
            self.vy *= 0.3
    
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
                self.rotation_paused = False
        
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
                self.rotation_paused = False
        
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
                    self.rotation_paused = False
        
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
                self.rotation_paused = False
    
    def update_rotation(self, opponent=None):
        """Update sword angle - points toward opponent like a duel."""
        # Skills override sword direction
        if self.rotation_paused:
            return
        
        # Sword points toward opponent (like a real fight)
        if opponent:
            target_angle = math.atan2(opponent.y - self.y, opponent.x - self.x)
            
            # Smooth rotation toward opponent
            angle_diff = ((target_angle - self.sword_angle + math.pi) % (2 * math.pi)) - math.pi
            self.sword_angle += angle_diff * 0.25  # Smooth tracking
        
        # Keep angle in [-π, π]
        if self.sword_angle > math.pi:
            self.sword_angle -= 2 * math.pi
        elif self.sword_angle < -math.pi:
            self.sword_angle += 2 * math.pi
    
    def on_rotation_hit(self, hit_sword=False, frame_count=0):
        """Called when rotation attack hits something.
        Flips rotation direction for natural combat feel.
        """
        # Prevent multi-hits in same rotation
        if frame_count - self.last_hit_frame < 10:
            return False
        
        self.last_hit_frame = frame_count
        
        # Flip direction on hit (makes combat look responsive)
        self.rotation_clockwise = not self.rotation_clockwise
        
        return True
    
    def on_attack_blocked(self):
        """Called when attack is blocked by shield."""
        self.attack_recovery = 15  # Brief stagger
        self.rotation_clockwise = not self.rotation_clockwise
    
    def update(self, opponent, arena_bounds, particles, shockwaves):
        """Update fighter - bounce-only movement with ninja wall boosts."""
        # Skip update if locked (during countdown)
        if self.locked:
            return
        
        self.update_skill(opponent, particles, shockwaves)
        self.update_rotation(opponent)  # Sword faces opponent
        
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
        if self.attack_recovery > 0:
            self.attack_recovery -= 1
        
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
    
    def check_sword_on_sword_parry(self, other):
        """Check if two rotating swords collide (parry)."""
        if self.rotation_paused or other.rotation_paused:
            return False
        if self.attack_cooldown > 0 or other.attack_cooldown > 0:
            return False
        
        (_, _), (my_tip_x, my_tip_y) = self.get_sword_hitbox()
        (_, _), (other_tip_x, other_tip_y) = other.get_sword_hitbox()
        
        # Check tip-to-tip distance
        dist = math.hypot(my_tip_x - other_tip_x, my_tip_y - other_tip_y)
        return dist < ROTATION_PARRY_DISTANCE
    
    def check_sword_clash(self, other, particles):
        """Check if rotating sword clashes with opponent's skill."""
        if self.rotation_paused:
            return None
        if other.active_skill is None:
            return None
        
        (_, _), (tip_x, tip_y) = self.get_sword_hitbox()
        
        if other.active_skill == SkillType.BLADE_CYCLONE:
            dist = math.hypot(tip_x - other.x, tip_y - other.y)
            if dist < 60:
                return SkillType.BLADE_CYCLONE
        
        elif other.active_skill == SkillType.SPIN_PARRY:
            if other.spin_parry_active:
                dist = math.hypot(tip_x - other.x, tip_y - other.y)
                if dist < 50:
                    return SkillType.SPIN_PARRY
        
        return None
    
    def check_spin_parry(self, attacker, particles):
        """Check if Spin Parry skill successfully parries an attack."""
        if not self.spin_parry_active:
            return False
        
        (_, _), (tip_x, tip_y) = attacker.get_sword_hitbox()
        dist = math.hypot(tip_x - self.x, tip_y - self.y)
        parry_radius = 55
        
        if dist < parry_radius:
            self.skill_data['parried'] = True
            self.spin_parry_active = False
            
            base_knockback = 15
            particles.emit_sparks(self.x, self.y)
            particles.emit_ring(self.x, self.y, YELLOW, 40, count=12)
            self.flash_timer = 8
            
            angle_to_attacker = math.atan2(attacker.y - self.y, attacker.x - self.x)
            attacker.vx = math.cos(angle_to_attacker) * base_knockback
            attacker.vy = math.sin(angle_to_attacker) * base_knockback
            attacker.attack_cooldown = 30
            
            return True
        
        return False
    
    def draw(self, surface, offset=(0, 0)):
        """Draw fighter."""
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
        
        # Inner highlight
        pygame.draw.circle(surface, self.color_bright,
                          (int(self.x - self.radius * 0.2 + ox), 
                           int(self.y - self.radius * 0.2 + oy)), 
                          int(self.radius * 0.3))
        
        # Sword
        self._draw_sword(surface, offset)
        
        # Health bar
        self._draw_health_bar(surface, offset)
        
        # Shield indicator
        if self.has_shield:
            shield_color = WHITE if self.shield_parry_window > 0 else GREEN
            pygame.draw.circle(surface, shield_color, 
                              (int(self.x + ox), int(self.y + oy)), 
                              self.radius + 8, 3)
        
        # Blade Cyclone vortex
        if self.active_skill == SkillType.BLADE_CYCLONE:
            vortex_radius = 80 + math.sin(self.skill_timer * 0.3) * 10
            pygame.draw.circle(surface, YELLOW,
                              (int(self.x + ox), int(self.y + oy)),
                              int(vortex_radius), 2)
        
        # Spin Parry indicator
        if self.spin_parry_active:
            parry_radius = 45 + math.sin(self.skill_timer * 0.4) * 5
            from config import ORANGE
            pygame.draw.circle(surface, ORANGE,
                              (int(self.x + ox), int(self.y + oy)),
                              int(parry_radius), 3)
    
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
        
        if self.has_shield:
            self.has_shield = False
            if self.shield_parry_window > 0:
                particles.emit_sparks(self.x, self.y)
                self.flash_timer = 8
            else:
                particles.emit(self.x, self.y, GREEN, count=10, size=4)
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
        
        self.active_skill = None
        self.skill_timer = 0
        self.skill_data = {}
        self.skill_target_pos = None
        self.trail_positions = []
        
        self.flash_timer = 0
        self.victory_bounce = 0
        self.has_shield = False
        self.shield_parry_window = 0
        self.attack_cooldown = 0
        self.invincible = 0
        self.locked = False
        
        self.spin_parry_active = False
        self.spin_parry_timer = 0
        self.spin_parry_recovery = 0
        
        self.rotation_clockwise = True
        self.last_hit_frame = -100
        self.rotation_paused = False
        self.attack_recovery = 0
