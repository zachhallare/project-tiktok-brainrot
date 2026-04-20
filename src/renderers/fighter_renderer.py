import os
import pygame
import math

from config import (
    WHITE, TRAIL_FADE_RATE
)

class FighterRenderer:
    """Handles rendering of fighter visuals, including glow, trails, and cel-shaded swords."""
    
    def __init__(self):
        sword_path = os.path.join(
            os.path.dirname(os.path.dirname(os.path.dirname(__file__))),
            "assets", "weapons", "sword.png"
        )
        raw = pygame.image.load(sword_path).convert_alpha()
        # Scale to match SWORD_LENGTH (55px) x a reasonable height
        self._sword_base = pygame.transform.scale(raw, (116, 36))

    def render(self, fighter, surface, offset=(0, 0)):
        """Draw fighter with glow, trail, and neon effects."""
        ox, oy = offset
        r = fighter.radius
        
        # Draw motion trail first (behind fighter)
        self._draw_trail(fighter, surface, offset)
        
        # Calculate dark border color for cel-shaded outline
        dark_border_color = (int(fighter.color[0] * 0.4), int(fighter.color[1] * 0.4), int(fighter.color[2] * 0.4))
        
        # Main body circle
        body_color = WHITE if fighter.flash_timer > 0 else fighter.color
        pygame.draw.circle(surface, body_color, 
                          (int(fighter.x + ox), int(fighter.y + oy)), int(r))
        

        
        # Sword
        self._draw_sword(fighter, surface, offset, dark_border_color)
    


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
        """Draw sword as a clean rotated PNG sprite (no effects)."""
        ox, oy = offset

        r = fighter.radius

        # Base position at edge of fighter body
        base_x = fighter.x + math.cos(fighter.sword_angle) * (r + 3)
        base_y = fighter.y + math.sin(fighter.sword_angle) * (r + 3)

        # Keep sword_trail updated for any external consumers (combat_manager etc.)
        tip_x = base_x + math.cos(fighter.sword_angle) * fighter.sword_length
        tip_y = base_y + math.sin(fighter.sword_angle) * fighter.sword_length
        fighter.sword_trail.append((tip_x, tip_y))
        if len(fighter.sword_trail) > 5:
            fighter.sword_trail = fighter.sword_trail[-5:]

        # ── Recolor sword sprite to match fighter color ──────────────
        colored = self._sword_base.copy()
        colored.fill((*fighter.render_color[:3], 180),
                     special_flags=pygame.BLEND_RGBA_MULT)

        # ── Rotate sprite to match sword_angle ───────────────────────
        angle_deg = -math.degrees(fighter.sword_angle)
        rotated = pygame.transform.rotate(colored, angle_deg)

        # ── Position: pivot at the sword base ────────────────────────
        sprite_w, sprite_h = self._sword_base.get_size()
        pivot_local = pygame.math.Vector2(0, sprite_h / 2)
        pivot_rotated = pivot_local.rotate(math.degrees(fighter.sword_angle))

        base_world = pygame.math.Vector2(base_x + ox, base_y + oy)
        rot_rect = rotated.get_rect()
        blit_pos = (base_world
                    - pivot_rotated
                    - pygame.math.Vector2(0, rot_rect.height / 2))

        surface.blit(rotated, (int(blit_pos.x), int(blit_pos.y)))
