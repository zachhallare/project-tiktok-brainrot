import os
import pygame
import math

from config import (
    WHITE, TRAIL_FADE_RATE
)

class FighterRenderer:
    """Handles rendering of fighter visuals, including trails and the attached sword."""

    def __init__(self):
        sword_path = os.path.join(
            os.path.dirname(os.path.dirname(os.path.dirname(__file__))),
            "assets", "weapons", "sword.png"
        )
        raw = pygame.image.load(sword_path).convert_alpha()
        self._sword_base = pygame.transform.scale(raw, (87, 27))

    def render(self, fighter, surface, offset=(0, 0)):
        ox, oy = offset
        r = fighter.radius

        self._draw_trail(fighter, surface, offset)

        dark_border_color = (
            int(fighter.color[0] * 0.4),
            int(fighter.color[1] * 0.4),
            int(fighter.color[2] * 0.4),
        )

        # Body circle
        body_color = WHITE if fighter.flash_timer > 0 else fighter.color
        cx = int(fighter.x + ox)
        cy = int(fighter.y + oy)
        pygame.draw.circle(surface, body_color, (cx, cy), int(r))

        # Sword rigidly attached to body
        self._draw_sword(fighter, surface, offset)


    def _draw_trail(self, fighter, surface, offset):
        if len(fighter.trail) < 2:
            return
        ox, oy = offset
        for i, (tx, ty) in enumerate(fighter.trail):
            fade = (1.0 - (i / len(fighter.trail))) * TRAIL_FADE_RATE
            if fade <= 0:
                continue
            trail_r = int(fighter.radius * fade * 0.7)
            if trail_r < 2:
                continue
            alpha = int(100 * fade)
            trail_surf = pygame.Surface((trail_r * 2, trail_r * 2), pygame.SRCALPHA)
            pygame.draw.circle(trail_surf, (*fighter.color[:3], alpha), (trail_r, trail_r), trail_r)
            surface.blit(trail_surf, (int(tx + ox) - trail_r, int(ty + oy) - trail_r))

    def _draw_sword(self, fighter, surface, offset):
        """
        Sword is rigidly fixed to the body at rotation_angle.

        Key geometry (screen coords, Y-down):
          - Sprite points RIGHT at 0 rotation.
          - pygame.transform.rotate uses positive = CCW visual.
          - Game angle `a` means direction (cos a, sin a) in screen space, so
            angle=π/2 → points DOWN → sprite must rotate CW 90° → rotate(surf, -90).
            Therefore: rotate(surf, -degrees(angle)).

          - Sprite center lives at: handle_pos + (orig_w/2) * sword_direction
            (because handle is at the left edge of the sprite, center is half-width away)
        """
        ox, oy = offset
        r = fighter.radius
        angle = fighter.rotation_angle

        cos_a = math.cos(angle)
        sin_a = math.sin(angle)

        # World-space tip position for combat_manager hit detection
        tip_wx = fighter.x + cos_a * (r + 3 + fighter.sword_length)
        tip_wy = fighter.y + sin_a * (r + 3 + fighter.sword_length)
        fighter.sword_trail.append((tip_wx, tip_wy))
        if len(fighter.sword_trail) > 5:
            fighter.sword_trail = fighter.sword_trail[-5:]

        # Screen-space handle position (where body edge meets sword grip)
        base_sx = fighter.x + ox + cos_a * (r + 3)
        base_sy = fighter.y + oy + sin_a * (r + 3)

        # Recolor sprite to match fighter color
        colored = self._sword_base.copy()
        colored.fill((*fighter.render_color[:3], 180), special_flags=pygame.BLEND_RGBA_MULT)

        # Rotate sprite CW by angle (negative = CW in pygame's CCW-positive convention)
        angle_deg = math.degrees(angle)
        rotated = pygame.transform.rotate(colored, -angle_deg)

        # Sprite center = handle_pos + (orig_w / 2) in sword direction.
        # This is the exact inverse of "handle is orig_w/2 behind the center along
        # the sword axis", which holds regardless of rotation angle.
        orig_w, orig_h = self._sword_base.get_size()
        rot_center_x = base_sx + (orig_w / 2) * cos_a
        rot_center_y = base_sy + (orig_w / 2) * sin_a

        rot_rect = rotated.get_rect(center=(int(rot_center_x), int(rot_center_y)))
        surface.blit(rotated, rot_rect)