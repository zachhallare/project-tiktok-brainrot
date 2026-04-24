import os
import pygame
import math

from config import WHITE, TRAIL_FADE_RATE, WEAPON_CONFIGS


class FighterRenderer:
    def __init__(self, weapon='sword'):
        cfg = WEAPON_CONFIGS[weapon]
        weapons_dir = os.path.join(
            os.path.dirname(os.path.dirname(os.path.dirname(__file__))),
            "assets", "images", "weapons"
        )
        raw = pygame.image.load(
            os.path.join(weapons_dir, cfg['sprite_file'])
        ).convert_alpha()
        self._weapon_base = pygame.transform.scale(raw, cfg['sprite_size'])
        self._orig_w, self._orig_h = cfg['sprite_size']


    def render(self, fighter, surface, offset=(0, 0)):
        ox, oy = offset
        r = fighter.radius

        self._draw_trail(fighter, surface, offset)

        body_color = WHITE if fighter.flash_timer > 0 else fighter.color
        cx = int(fighter.x + ox)
        cy = int(fighter.y + oy)
        pygame.draw.circle(surface, body_color, (cx, cy), int(r))

        self._draw_weapon(fighter, surface, offset)


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
            pygame.draw.circle(
                trail_surf, (*fighter.color[:3], alpha), (trail_r, trail_r), trail_r
            )
            surface.blit(trail_surf, (int(tx + ox) - trail_r, int(ty + oy) - trail_r))

 
    def _draw_weapon(self, fighter, surface, offset):
        """
        Draw weapon rigidly attached to body at rotation_angle.

        Geometry (Y-down screen space):
          - Sprite points RIGHT at angle=0.
          - pygame.transform.rotate is CCW-positive, so to rotate the sprite
            CW by `angle` (matching screen math): rotate(surf, -degrees(angle)).
          - Sprite center = handle_pos + (sprite_width / 2) along blade direction.
            (Handle is at the LEFT edge of the sprite; center is half-width away.)
        """
        ox, oy = offset
        r = fighter.radius
        angle = fighter.rotation_angle
        cos_a = math.cos(angle)
        sin_a = math.sin(angle)

        # World-space tip (used by combat_manager for sword_trail)
        tip_wx = fighter.x + cos_a * (r + 3 + fighter.sword_length)
        tip_wy = fighter.y + sin_a * (r + 3 + fighter.sword_length)
        fighter.sword_trail.append((tip_wx, tip_wy))
        if len(fighter.sword_trail) > 5:
            fighter.sword_trail = fighter.sword_trail[-5:]

        # Screen-space handle (body edge)
        base_sx = fighter.x + ox + cos_a * (r + 3)
        base_sy = fighter.y + oy + sin_a * (r + 3)

        # # Recolor the weapon.
        # colored = self._weapon_base.copy()
        # colored.fill(
        #     (*fighter.render_color[:3], 180),
        #     special_flags=pygame.BLEND_RGBA_MULT
        # )

        # Rotate CW by angle
        angle_deg = math.degrees(angle)
        rotated = pygame.transform.rotate(self._weapon_base, -angle_deg)    

        # Sprite center = handle_pos + (orig_w / 2) along blade axis
        rot_center_x = base_sx + (self._orig_w / 2) * cos_a
        rot_center_y = base_sy + (self._orig_w / 2) * sin_a

        rot_rect = rotated.get_rect(center=(int(rot_center_x), int(rot_center_y)))
        surface.blit(rotated, rot_rect)