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
        
        self.trail = []

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
        max_vel = MAX_VELOCITY
        if speed > max_vel:
            self.vx = (self.vx / speed) * max_vel
            self.vy = (self.vy / speed) * max_vel
        
        # Ensure minimum velocity (DVD logo always moving)
        min_vel = MIN_VELOCITY
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
        """Draw fighter with glow, trail, and neon effects."""
        ox, oy = offset
        r = self.radius
        
        # Draw motion trail first (behind fighter)
        self._draw_trail(surface, offset)
        
        # Draw glow effect (bloom simulation)
        self._draw_glow(surface, offset)
        
        # Calculate dark border color for cel-shaded outline
        dark_border_color = (int(self.color[0] * 0.4), int(self.color[1] * 0.4), int(self.color[2] * 0.4))
        
        # Dark border circle (drawn slightly larger behind the body)
        pygame.draw.circle(surface, dark_border_color,
                          (int(self.x + ox), int(self.y + oy)), int(r + 3))
        
        # Main body circle
        body_color = WHITE if self.flash_timer > 0 else self.color
        pygame.draw.circle(surface, body_color, 
                          (int(self.x + ox), int(self.y + oy)), int(r))
        
        # Inner highlight
        pygame.draw.circle(surface, self.color_bright,
                          (int(self.x - r * 0.2 + ox), 
                           int(self.y - r * 0.2 + oy)), 
                          int(r * 0.3))
        
        # Sword
        self._draw_sword(surface, offset, dark_border_color)
    
    def _draw_glow(self, surface, offset):
        """Draw a glow/bloom effect behind the fighter."""
        ox, oy = offset
        glow_radius = int(self.radius * GLOW_RADIUS_MULT)
        
        # Create a surface for the glow with alpha
        glow_size = glow_radius * 2 + 4
        glow_surf = pygame.Surface((glow_size, glow_size), pygame.SRCALPHA)
        
        # Draw gradient circles for bloom effect
        for i in range(3):
            r = glow_radius - i * 4
            if r > 0:
                alpha = GLOW_ALPHA - i * 15
                color = (*self.color[:3], max(0, alpha))
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
            trail_r = int(self.radius * fade * 0.7)
            if trail_r < 2:
                continue
            
            # Create faded color
            alpha = int(100 * fade)
            trail_color = (*self.color[:3], alpha)
            
            # Draw on a temp surface for alpha
            trail_surf = pygame.Surface((trail_r * 2, trail_r * 2), pygame.SRCALPHA)
            pygame.draw.circle(trail_surf, trail_color, (trail_r, trail_r), trail_r)
            surface.blit(trail_surf, (int(tx + ox) - trail_r, int(ty + oy) - trail_r))
    
    def _draw_sword(self, surface, offset, dark_border_color):
        """Draw sword with cel-shaded blade, dark directional smear, and clean tip trail."""
        ox, oy = offset
        r = self.radius
        
        visual_sword_length = self.sword_length
        
        # --- Main sword geometry ---
        base_x = self.x + math.cos(self.sword_angle) * (r + 3)
        base_y = self.y + math.sin(self.sword_angle) * (r + 3)
        tip_x = base_x + math.cos(self.sword_angle) * visual_sword_length
        tip_y = base_y + math.sin(self.sword_angle) * visual_sword_length
        
        # --- Clean Tip Trail ---
        self.sword_trail.append((tip_x, tip_y))
        if len(self.sword_trail) > 5:
            self.sword_trail = self.sword_trail[-5:]
        
        # Draw thin fading trail lines connecting recent tip positions
        if len(self.sword_trail) >= 2:
            for i in range(1, len(self.sword_trail)):
                # Fade: older segments are more transparent
                alpha = int(255 * (i / len(self.sword_trail)) * 0.5)
                trail_color = (*self.color[:3], alpha)
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
        
        # --- Dark Directional Smear (drawn BEFORE the crisp sword) ---
        # Calculate trailing tail angle (physically trails behind the spin)
        tail_angle = self.sword_angle - (self.spin_speed * self.spin_direction * 3.5)
        
        # Tail base and tip coordinates
        tbx = self.x + math.cos(tail_angle) * (r + 3)
        tby = self.y + math.sin(tail_angle) * (r + 3)
        ttx = tbx + math.cos(tail_angle) * visual_sword_length
        tty = tby + math.sin(tail_angle) * visual_sword_length
        
        # Deeply darkened smear color from the fighter's base color
        smear_r = int(self.color[0] * 0.2)
        smear_g = int(self.color[1] * 0.2)
        smear_b = int(self.color[2] * 0.2)
        
        # Build a surface large enough for the smear + sword area
        # Use a generous bounding box around the fighter center
        smear_extent = int((r + 3 + visual_sword_length) * 2 + 20)
        smear_surf = pygame.Surface((smear_extent, smear_extent), pygame.SRCALPHA)
        smear_cx = smear_extent // 2  # Center of the smear surface
        smear_cy = smear_extent // 2
        
        # Offset from world coords to smear surface coords
        sx_off = smear_cx - self.x
        sy_off = smear_cy - self.y
        
        # Draw layered fading polygon smear (4 layers, fading toward tail)
        num_layers = 4
        for layer in range(num_layers):
            t = layer / num_layers  # 0.0 (current sword) to ~0.75 (near tail)
            
            # Interpolate positions between main sword and tail
            l_bx = base_x + (tbx - base_x) * t
            l_by = base_y + (tby - base_y) * t
            l_tx = tip_x + (ttx - tip_x) * t
            l_ty = tip_y + (tty - tip_y) * t
            
            # Next layer interpolation (or tail end for the last layer)
            t_next = (layer + 1) / num_layers
            n_bx = base_x + (tbx - base_x) * t_next
            n_by = base_y + (tby - base_y) * t_next
            n_tx = tip_x + (ttx - tip_x) * t_next
            n_ty = tip_y + (tty - tip_y) * t_next
            
            # Fade alpha toward the tail end
            alpha = int(90 * (1.0 - t))
            if alpha <= 0:
                continue
            
            # Build polygon: current_base -> current_tip -> next_tip -> next_base
            poly_points = [
                (int(l_bx + sx_off), int(l_by + sy_off)),
                (int(l_tx + sx_off), int(l_ty + sy_off)),
                (int(n_tx + sx_off), int(n_ty + sy_off)),
                (int(n_bx + sx_off), int(n_by + sy_off)),
            ]
            
            pygame.draw.polygon(smear_surf, (smear_r, smear_g, smear_b, alpha), poly_points)
        
        # Blit smear surface onto the main screen
        surface.blit(smear_surf, (int(self.x + ox) - smear_cx, int(self.y + oy) - smear_cy))
        
        # --- Thinner, Sharper Sword (drawn on top of smear) ---
        sword_w = max(4, int(SWORD_WIDTH * 1.5))
        # Dark border outline (refined to fit thinner blade)
        pygame.draw.line(surface, dark_border_color,
                        (int(base_x + ox), int(base_y + oy)),
                        (int(tip_x + ox), int(tip_y + oy)), sword_w + 3)
        # Core blade matches body neon color
        pygame.draw.line(surface, self.color,
                        (int(base_x + ox), int(base_y + oy)),
                        (int(tip_x + ox), int(tip_y + oy)), sword_w)
    

    
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
        
        self.trail.clear()
