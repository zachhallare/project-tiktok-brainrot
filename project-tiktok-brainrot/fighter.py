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
    WALL_BOOST_STRENGTH, TRAIL_LENGTH, TRAIL_FADE_RATE,
    GLOW_ALPHA, GLOW_RADIUS_MULT, NEON_RED, NEON_BLUE
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
        
        # Attack timing constants (base values - modified by chaos)
        self.ATTACK_DURATION = 12      # Frames per swing
        self.ATTACK_COOLDOWN = 8       # Frames between attacks
        self.COMBO_TIMEOUT = 45        # Frames before combo resets
        
        # Motion trail (list of previous positions)
        self.trail = []
        
        # Dynamic sizing (modified by chaos events)
        # Separate body and sword size for Tiny Terror
        self.body_size_multiplier = 1.0   # Body/collision size
        self.sword_size_multiplier = 1.0  # Sword length/reach
        self.current_radius = self.radius  # Actual collision radius (body only)
        
        # Attack speed multiplier (lower = slower attacks)
        self.attack_speed_multiplier = 1.0
        
        # Wall damage cooldown (for Spike Walls)
        self.wall_damage_cooldown = 0
        
        # Render color (can be overridden by chaos events)
        self.render_color = color
        self.render_color_bright = color_bright
        
        # Health bar render color (for Blackout)
        self.health_bar_color = color
    

    
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
        
        # Update current radius based on BODY size multiplier (not sword)
        self.current_radius = self.radius * self.body_size_multiplier
        
        # Update trail (store previous positions for motion trail effect)
        self.trail.insert(0, (self.x, self.y))
        if len(self.trail) > TRAIL_LENGTH:
            self.trail.pop()
        
        self.update_rotation(opponent, 0)  # Sword faces opponent with combo offset
        
        # Decrease timers
        if self.flash_timer > 0:
            self.flash_timer -= 1
        if self.attack_cooldown > 0:
            # Apply attack speed multiplier (slower attacks = slower cooldown decay)
            self.attack_cooldown -= self.attack_speed_multiplier
        if self.invincible > 0:
            self.invincible -= 1
        if self.wall_damage_cooldown > 0:
            self.wall_damage_cooldown -= 1

        
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
        # Use current_radius for proper collision with size changes
        ax, ay, aw, ah = arena_bounds
        r = self.current_radius
        
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
        # Use current_radius (body) for sword base position
        r = self.current_radius
        # Scale sword length with SWORD size multiplier (separate from body)
        scaled_sword_length = self.sword_length * self.sword_size_multiplier
        
        base_x = self.x + math.cos(self.sword_angle) * (r + 3)
        base_y = self.y + math.sin(self.sword_angle) * (r + 3)
        tip_x = base_x + math.cos(self.sword_angle) * scaled_sword_length
        tip_y = base_y + math.sin(self.sword_angle) * scaled_sword_length
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
        """Draw fighter with glow, trail, and neon effects."""
        ox, oy = offset
        r = self.current_radius
        
        # Draw motion trail first (behind fighter)
        self._draw_trail(surface, offset)
        
        # Draw glow effect (bloom simulation)
        self._draw_glow(surface, offset)
        
        # Main body circle - use render_color for chaos events
        body_color = WHITE if self.flash_timer > 0 else self.render_color
        pygame.draw.circle(surface, body_color, 
                          (int(self.x + ox), int(self.y + oy)), int(r))
        
        # Inner highlight
        pygame.draw.circle(surface, self.render_color_bright,
                          (int(self.x - r * 0.2 + ox), 
                           int(self.y - r * 0.2 + oy)), 
                          int(r * 0.3))
        
        # Sword
        self._draw_sword(surface, offset)
        
        # Health bar (can be hidden during blackout via main.py)
        self._draw_health_bar(surface, offset)
    
    def _draw_glow(self, surface, offset):
        """Draw a glow/bloom effect behind the fighter."""
        ox, oy = offset
        glow_radius = int(self.current_radius * GLOW_RADIUS_MULT)
        
        # Create a surface for the glow with alpha
        glow_size = glow_radius * 2 + 4
        glow_surf = pygame.Surface((glow_size, glow_size), pygame.SRCALPHA)
        
        # Draw gradient circles for bloom effect
        for i in range(3):
            r = glow_radius - i * 4
            if r > 0:
                alpha = GLOW_ALPHA - i * 15
                color = (*self.render_color[:3], max(0, alpha))
                pygame.draw.circle(glow_surf, color, (glow_size // 2, glow_size // 2), r)
        
        # Blit the glow
        glow_x = int(self.x + ox) - glow_size // 2
        glow_y = int(self.y + oy) - glow_size // 2
        surface.blit(glow_surf, (glow_x, glow_y))
    
    def _draw_trail(self, surface, offset):
        """Draw motion trail as fading circles."""
        if len(self.trail) < 2:
            return
        
        ox, oy = offset
        
        for i, (tx, ty) in enumerate(self.trail):
            # Calculate fade based on position in trail
            fade = 1.0 - (i / len(self.trail))
            fade *= TRAIL_FADE_RATE
            
            if fade <= 0:
                continue
            
            # Trail circle gets smaller further back
            trail_r = int(self.current_radius * fade * 0.7)
            if trail_r < 2:
                continue
            
            # Create faded color
            alpha = int(100 * fade)
            trail_color = (*self.render_color[:3], alpha)
            
            # Draw on a temp surface for alpha
            trail_surf = pygame.Surface((trail_r * 2, trail_r * 2), pygame.SRCALPHA)
            pygame.draw.circle(trail_surf, trail_color, (trail_r, trail_r), trail_r)
            surface.blit(trail_surf, (int(tx + ox) - trail_r, int(ty + oy) - trail_r))
    
    def _draw_sword(self, surface, offset):
        """Draw sword with proper sizing."""
        ox, oy = offset
        r = self.current_radius
        # Use SWORD size multiplier (stays normal during Tiny Terror)
        scaled_sword_length = self.sword_length * self.sword_size_multiplier
        
        base_x = self.x + math.cos(self.sword_angle) * (r + 3)
        base_y = self.y + math.sin(self.sword_angle) * (r + 3)
        tip_x = base_x + math.cos(self.sword_angle) * scaled_sword_length
        tip_y = base_y + math.sin(self.sword_angle) * scaled_sword_length
        
        sword_color = WHITE if self.flash_timer > 0 else self.render_color_bright
        
        # Sword width stays normal (doesn't scale with body size)
        sword_w = max(2, int(SWORD_WIDTH * self.sword_size_multiplier))
        
        pygame.draw.line(surface, sword_color,
                        (int(base_x + ox), int(base_y + oy)),
                        (int(tip_x + ox), int(tip_y + oy)), sword_w)
    
    def _draw_health_bar(self, surface, offset):
        """Draw health bar above fighter."""
        ox, oy = offset
        bar_width = 40
        bar_height = 6
        bar_x = self.x - bar_width // 2
        bar_y = self.y - self.current_radius - 15  # Use current_radius for proper positioning
        
        # Background
        pygame.draw.rect(surface, (50, 50, 50),
                        (int(bar_x + ox), int(bar_y + oy), bar_width, bar_height))
        
        # Health fill - use health_bar_color (BLACK during Blackout, otherwise normal)
        health_pct = max(0, self.health / self.max_health)
        fill_width = int(bar_width * health_pct)
        if fill_width > 0:
            pygame.draw.rect(surface, self.health_bar_color,
                            (int(bar_x + ox), int(bar_y + oy), fill_width, bar_height))
        
        # Border - also use health bar color for consistency during Blackout
        border_color = self.health_bar_color if self.health_bar_color == BLACK else WHITE
        pygame.draw.rect(surface, border_color,
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
        
        # Reset chaos event properties
        self.trail.clear()
        self.body_size_multiplier = 1.0
        self.sword_size_multiplier = 1.0
        self.attack_speed_multiplier = 1.0
        self.current_radius = self.radius
        self.render_color = self.color
        self.render_color_bright = self.color_bright
        self.health_bar_color = self.color
        self.wall_damage_cooldown = 0
