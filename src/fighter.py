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
        self.sword_trail = []  # Tip positions for clean visual trail
        
        # Visual
        self.flash_timer = 0
        self.victory_bounce = 0
        
        # Cooldowns
        self.attack_cooldown = 0
        self.invincible = 0
        
        # Locked state (during countdown)
        self.locked = False
        
        # Legacy hit tracking
        self.last_hit_frame = -100     # Frame of last successful hit
        
        # Motion trail (list of previous positions)
        self.trail = []
        
        # Dynamic sizing (modified by chaos events)
        # Separate body and sword size for Tiny Terror
        self.body_size_multiplier = 1.0   # Body/collision size
        self.sword_size_multiplier = 1.0  # Sword length/reach
        self.current_radius = self.radius  # Actual collision radius (body only)
        
        # Attack speed multiplier (lower = slower attacks)
        self.attack_speed_multiplier = 1.0
        
        # Physics movement speed multiplier
        self.speed_multiplier = 1.0
        
        # Render color (can be overridden by chaos events)
        self.render_color = color
        self.render_color_bright = color_bright
        
        # Health bar render color (for Blackout)
        self.health_bar_color = color
    

    
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
        
        # Update current radius based on BODY size multiplier (not sword)
        self.current_radius = self.radius * self.body_size_multiplier
        
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
            # Apply attack speed multiplier (slower attacks = slower cooldown decay)
            self.attack_cooldown -= self.attack_speed_multiplier
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
        """Get damage multiplier (constant for Beyblade mode)."""
        return 1.0
    

    
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
        """Draw sword with dark blade and clean tip trail."""
        ox, oy = offset
        r = self.current_radius
        
        # Scale sword length with sword size multiplier
        visual_sword_length = self.sword_length * self.sword_size_multiplier
        
        base_x = self.x + math.cos(self.sword_angle) * (r + 3)
        base_y = self.y + math.sin(self.sword_angle) * (r + 3)
        tip_x = base_x + math.cos(self.sword_angle) * visual_sword_length
        tip_y = base_y + math.sin(self.sword_angle) * visual_sword_length
        
        # Darker sword color for visual distinction from neon body
        dark_sword_color = (int(self.render_color[0] * 0.4), int(self.render_color[1] * 0.4), int(self.render_color[2] * 0.4))
        
        # --- Clean Tip Trail ---
        self.sword_trail.append((tip_x, tip_y))
        if len(self.sword_trail) > 5:
            self.sword_trail = self.sword_trail[-5:]
        
        # Draw thin fading trail lines connecting recent tip positions
        if len(self.sword_trail) >= 2:
            for i in range(1, len(self.sword_trail)):
                # Fade: older segments are more transparent
                alpha = int(255 * (i / len(self.sword_trail)) * 0.5)
                trail_color = (*self.render_color[:3], alpha)
                # Draw on a temp surface for alpha support
                x1, y1 = self.sword_trail[i - 1]
                x2, y2 = self.sword_trail[i]
                # Calculate bounding box for the line segment
                min_x = int(min(x1, x2) + ox) - 2
                min_y = int(min(y1, y2) + oy) - 2
                max_x = int(max(x1, x2) + ox) + 2
                max_y = int(max(y1, y2) + oy) + 2
                seg_w = max(max_x - min_x, 1)
                seg_h = max(max_y - min_y, 1)
                trail_surf = pygame.Surface((seg_w, seg_h), pygame.SRCALPHA)
                pygame.draw.line(trail_surf, trail_color,
                                (int(x1 + ox) - min_x, int(y1 + oy) - min_y),
                                (int(x2 + ox) - min_x, int(y2 + oy) - min_y), 2)
                surface.blit(trail_surf, (min_x, min_y))
        
        # Draw chunky outlined sword on top of trail
        sword_w = max(6, int(SWORD_WIDTH * self.sword_size_multiplier * 2.5))
        # Black outline (slightly thicker)
        pygame.draw.line(surface, BLACK,
                        (int(base_x + ox), int(base_y + oy)),
                        (int(tip_x + ox), int(tip_y + oy)), sword_w + 4)
        # Colored blade on top
        pygame.draw.line(surface, dark_sword_color,
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
        self.sword_trail = []
        
        self.flash_timer = 0
        self.victory_bounce = 0
        self.attack_cooldown = 0
        self.invincible = 0
        self.locked = False
        
        self.last_hit_frame = -100
        
        # Reset chaos event properties
        self.trail.clear()
        self.body_size_multiplier = 1.0
        self.sword_size_multiplier = 1.0
        self.attack_speed_multiplier = 1.0
        self.speed_multiplier = 1.0
        self.current_radius = self.radius
        self.render_color = self.color
        self.render_color_bright = self.color_bright
        self.health_bar_color = self.color
