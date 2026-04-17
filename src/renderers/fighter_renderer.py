import pygame
import math

from config import (
    WHITE, SWORD_WIDTH, TRAIL_FADE_RATE, GLOW_ALPHA, GLOW_RADIUS_MULT
)

class FighterRenderer:
    """Handles rendering of fighter visuals, including glow, trails, and cel-shaded swords."""
    
    def __init__(self):
        pass

    def render(self, fighter, surface, offset=(0, 0)):
        """Draw fighter with glow, trail, and neon effects."""
        ox, oy = offset
        r = fighter.radius
        
        # Draw motion trail first (behind fighter)
        self._draw_trail(fighter, surface, offset)
        
        # Draw glow effect (bloom simulation)
        self._draw_glow(fighter, surface, offset)
        
        # Calculate dark border color for cel-shaded outline
        dark_border_color = (int(fighter.color[0] * 0.4), int(fighter.color[1] * 0.4), int(fighter.color[2] * 0.4))
        
        # Dark border circle (drawn slightly larger behind the body)
        pygame.draw.circle(surface, dark_border_color,
                          (int(fighter.x + ox), int(fighter.y + oy)), int(r + 3))
        
        # Main body circle
        body_color = WHITE if fighter.flash_timer > 0 else fighter.color
        pygame.draw.circle(surface, body_color, 
                          (int(fighter.x + ox), int(fighter.y + oy)), int(r))
        

        
        # Sword
        self._draw_sword(fighter, surface, offset, dark_border_color)
    
    def _draw_glow(self, fighter, surface, offset):
        """Draw a glow/bloom effect behind the fighter."""
        ox, oy = offset
        glow_radius = int(fighter.radius * GLOW_RADIUS_MULT)
        
        # Create a surface for the glow with alpha
        glow_size = glow_radius * 2 + 4
        glow_surf = pygame.Surface((glow_size, glow_size), pygame.SRCALPHA)
        
        # Draw gradient circles for bloom effect
        for i in range(3):
            r = glow_radius - i * 4
            if r > 0:
                alpha = GLOW_ALPHA - i * 15
                color = (*fighter.color[:3], max(0, alpha))
                pygame.draw.circle(glow_surf, color, (glow_size // 2, glow_size // 2), r)
        
        # Blit the glow
        glow_x = int(fighter.x + ox) - glow_size // 2
        glow_y = int(fighter.y + oy) - glow_size // 2
        surface.blit(glow_surf, (glow_x, glow_y))
    
    def _draw_trail(self, fighter, surface, offset):
        """Draw motion trail as fading circles."""
        if len(fighter.trail) < 2:
            return
        
        ox, oy = offset
        
        for i, (tx, ty) in enumerate(fighter.trail):
            # Calculate fade based on position in trail
            fade = 1.0 - (i / len(fighter.trail))
            fade *= TRAIL_FADE_RATE
            
            if fade <= 0:
                continue
            
            # Trail circle gets smaller further back
            trail_r = int(fighter.radius * fade * 0.7)
            if trail_r < 2:
                continue
            
            # Create faded color
            alpha = int(100 * fade)
            trail_color = (*fighter.color[:3], alpha)
            
            # Draw on a temp surface for alpha
            trail_surf = pygame.Surface((trail_r * 2, trail_r * 2), pygame.SRCALPHA)
            pygame.draw.circle(trail_surf, trail_color, (trail_r, trail_r), trail_r)
            surface.blit(trail_surf, (int(tx + ox) - trail_r, int(ty + oy) - trail_r))
    
    def _draw_sword(self, fighter, surface, offset, dark_border_color):
        """Draw sword with cel-shaded blade, dark directional smear, and clean tip trail."""
        ox, oy = offset
        r = fighter.radius
        
        visual_sword_length = fighter.sword_length
        
        # --- Main sword geometry ---
        base_x = fighter.x + math.cos(fighter.sword_angle) * (r + 3)
        base_y = fighter.y + math.sin(fighter.sword_angle) * (r + 3)
        tip_x = base_x + math.cos(fighter.sword_angle) * visual_sword_length
        tip_y = base_y + math.sin(fighter.sword_angle) * visual_sword_length
        
        # --- Clean Tip Trail ---
        fighter.sword_trail.append((tip_x, tip_y))
        if len(fighter.sword_trail) > 5:
            fighter.sword_trail = fighter.sword_trail[-5:]
        
        # Draw thin fading trail lines connecting recent tip positions
        if len(fighter.sword_trail) >= 2:
            for i in range(1, len(fighter.sword_trail)):
                # Fade: older segments are more transparent
                alpha = int(255 * (i / len(fighter.sword_trail)) * 0.5)
                trail_color = (*fighter.color[:3], alpha)
                # Draw on a temp surface for alpha support
                x1, y1 = fighter.sword_trail[i - 1]
                x2, y2 = fighter.sword_trail[i]
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
        tail_angle = fighter.sword_angle - (fighter.spin_speed * fighter.spin_direction * 3.5)
        
        # Tail base and tip coordinates
        tbx = fighter.x + math.cos(tail_angle) * (r + 3)
        tby = fighter.y + math.sin(tail_angle) * (r + 3)
        ttx = tbx + math.cos(tail_angle) * visual_sword_length
        tty = tby + math.sin(tail_angle) * visual_sword_length
        
        # Deeply darkened smear color from the fighter's base color
        smear_r = int(fighter.color[0] * 0.2)
        smear_g = int(fighter.color[1] * 0.2)
        smear_b = int(fighter.color[2] * 0.2)
        
        # Build a surface large enough for the smear + sword area
        # Use a generous bounding box around the fighter center
        smear_extent = int((r + 3 + visual_sword_length) * 2 + 20)
        smear_surf = pygame.Surface((smear_extent, smear_extent), pygame.SRCALPHA)
        smear_cx = smear_extent // 2  # Center of the smear surface
        smear_cy = smear_extent // 2
        
        # Offset from world coords to smear surface coords
        sx_off = smear_cx - fighter.x
        sy_off = smear_cy - fighter.y
        
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
        surface.blit(smear_surf, (int(fighter.x + ox) - smear_cx, int(fighter.y + oy) - smear_cy))
        
        # --- Thinner, Sharper Sword (drawn on top of smear) ---
        sword_w = max(4, int(SWORD_WIDTH * 1.5))
        # Dark border outline (refined to fit thinner blade)
        pygame.draw.line(surface, dark_border_color,
                        (int(base_x + ox), int(base_y + oy)),
                        (int(tip_x + ox), int(tip_y + oy)), sword_w + 3)
        # Core blade matches body neon color
        pygame.draw.line(surface, fighter.color,
                        (int(base_x + ox), int(base_y + oy)),
                        (int(tip_x + ox), int(tip_y + oy)), sword_w)
