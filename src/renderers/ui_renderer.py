"""
UI Rendering system for the AlgoRot battle simulation.

This module provides the head-up display (HUD), including Tekken-style 
health bars, winner announcements, and other cinematic overlays.
"""

import pygame
import random
import math


class UIRenderer:
    """Manages the visual state of the game's interface.

    Handles the rendering of health bars, VS indicators, and specialized 
    feedback for low-health (Danger Zone) states.
    """
    
    def __init__(self, screen: pygame.Surface, font_medium: pygame.font.Font, font_small: pygame.font.Font):
        """Initializes the UI renderer with required assets.

        Args:
            screen: The main display surface.
            font_medium: Font used for primary labels.
            font_small: Font used for secondary details.
        """
        self.screen = screen
        self.font_medium = font_medium
        self.font_small = font_small
        self.white = (255, 255, 255)
        self.bg_color = (30, 30, 30)
        self.dark_border_color = (60, 60, 60)
        self.event_label_anim_timer = 0


    def draw(self, game):
        """Main entry point for rendering the entire UI overlay."""
        self._draw_hud(game)


    def _draw_hud(self, game):
        """Renders the static, top-aligned health bars flush above the arena.

        Designed after classic fighting games (Tekken style), these bars 
        mirror each other and provide visceral feedback (shake/blink) when 
        health reaches critical levels.
        """
        ax, ay, aw, ah = game.arena_bounds
        BAR_H = 28
        CAP_R = 13
        TIP = 10  # arrow tip width
        BAR_W = (aw // 2) - CAP_R * 2 - 20
        bar_y = (ay - BAR_H) // 2

        blue_pct = max(0.0, game.blue.health / game.blue.max_health)
        red_pct  = max(0.0, game.red.health  / game.red.max_health)

        # Fires every 80 ms (6 frames at 60fps), so it reads as a heartbeat.
        pulse = (pygame.time.get_ticks() // 80) % 2 == 0

        bsx = random.randint(-1, 1) if blue_pct <= 0.10 and pulse else 0
        bsy = random.randint(-1, 1) if blue_pct <= 0.10 and pulse else 0
        rsx = random.randint(-1, 1) if red_pct  <= 0.10 and pulse else 0
        rsy = random.randint(-1, 1) if red_pct  <= 0.10 and pulse else 0

        # Blue bar: left side, arrow tip points RIGHT (inward toward VS)
        bx = ax + CAP_R * 2 + bsx
        by = bar_y + bsy
        self._draw_bar_body(bx, by, BAR_W, BAR_H, TIP, blue_pct, game.blue, 'right')
        self._draw_bar_cap(ax + CAP_R + bsx, by + BAR_H // 2, CAP_R, game.blue)

        # Red bar: right side, arrow tip points LEFT (inward toward VS)
        rx = ax + aw - CAP_R * 2 - BAR_W + rsx
        ry = bar_y + rsy
        self._draw_bar_body(rx, ry, BAR_W, BAR_H, TIP, red_pct, game.red, 'left')
        self._draw_bar_cap(ax + aw - CAP_R + rsx, ry + BAR_H // 2, CAP_R, game.red)

        # Diamond health bar separator.
        cx = ax + aw // 2
        cy = bar_y + BAR_H // 2
        sep_color = (90, 90, 110)
        gem_color = (160, 160, 185)
        line_gap = 10

        # Thin separator lines.
        pygame.draw.line(self.screen, sep_color,
                        (cx - line_gap - 16, cy), (cx - line_gap, cy), 1)
        pygame.draw.line(self.screen, sep_color,
                        (cx + line_gap, cy), (cx + line_gap + 16, cy), 1)

        # Small diamond (4-point polygon, 7px radius)
        dr = 7
        diamond = [(cx, cy - dr), (cx + dr, cy), (cx, cy + dr), (cx - dr, cy)]
        pygame.draw.polygon(self.screen, (30, 30, 40), diamond)        # dark fill
        pygame.draw.polygon(self.screen, gem_color,   diamond, 1)      # light border
        # Single specular dot — upper-left facet
        pygame.draw.circle(self.screen, (210, 210, 230), (cx - 2, cy - 2), 1)


    def _draw_bar_body(self, x, y, w, h, tip, hp_pct, fighter, facing):
        """Arrow-shaped bar with glow, diagonal stripe texture, and segment dividers."""
        color   = self._get_bar_color(fighter)
        half_h  = h // 2

        # Arrow-shaped background polygon
        if facing == 'right':
            bg_poly = [(x, y), (x+w, y), (x+w+tip, y+half_h), (x+w, y+h), (x, y+h)]
        else:
            bg_poly = [(x, y), (x+w, y), (x+w, y+h), (x, y+h), (x-tip, y+half_h)]

        pygame.draw.polygon(self.screen, (15, 15, 20), bg_poly)

        # 1. Ghost / drain layer: darkened fighter color fills the entire arrow
        #    This makes lost HP read as "dim [fighter color]" not "black void"
        ghost = tuple(max(0, int(c * 0.22)) for c in fighter.health_bar_color)
        pygame.draw.polygon(self.screen, ghost, bg_poly)

        # 2. Subtle inner border on the ghost to separate it from the arena bg
        ghost_border = tuple(max(0, int(c * 0.45)) for c in fighter.health_bar_color)
        pygame.draw.polygon(self.screen, ghost_border, bg_poly, 1)

        # 3. Active fill
        fill_w = int(w * hp_pct)
        if fill_w > 0:
            is_full = hp_pct >= 1.0
            if facing == 'right':
                fill_x = x
                fill_poly = bg_poly if is_full else [
                    (x, y), (x+fill_w, y), (x+fill_w, y+h), (x, y+h)
                ]
            else:
                fill_x = x + w - fill_w
                fill_poly = bg_poly if is_full else [
                    (fill_x, y), (x+w, y), (x+w, y+h), (fill_x, y+h)
                ]

            # Additive glow behind the fill
            self._draw_poly_glow(fill_poly, color, expand=5)

            # Main fill
            pygame.draw.polygon(self.screen, color, fill_poly)

            # Diagonal stripe texture, clipped to the fill rectangle
            old_clip = self.screen.get_clip()
            self.screen.set_clip(pygame.Rect(fill_x, y, fill_w, h))
            stripe_surf = pygame.Surface((fill_w + h, h), pygame.SRCALPHA)
            for i in range(-h, fill_w + h, 13):
                pygame.draw.line(stripe_surf, (255, 255, 255, 28),
                                (i, 0), (i + h, h), 4)
            self.screen.blit(stripe_surf, (fill_x, y))
            self.screen.set_clip(old_clip)

            # Top-edge highlight
            hi = tuple(min(255, int(c * 1.7)) for c in color)
            pygame.draw.line(self.screen, hi, (fill_x, y+2), (fill_x+fill_w, y+2), 2)

        # 4. Segment dividers — draw over both ghost and fill
        for i in range(1, 10):
            sx = x + int(w * i / 10)
            pygame.draw.line(self.screen, (0, 0, 0), (sx, y+2), (sx, y+h-2), 1)

        # 5. Outer border
        pygame.draw.polygon(self.screen, (80, 80, 100), bg_poly, 2)


    def _draw_poly_glow(self, poly, color, expand=5):
        """Additively blends a soft color bloom behind the given polygon."""
        xs = [p[0] for p in poly]
        ys = [p[1] for p in poly]
        min_x = min(xs) - expand
        min_y = min(ys) - expand
        surf_w = max(1, max(xs) - min(xs) + expand * 2)
        surf_h = max(1, max(ys) - min(ys) + expand * 2)

        glow = pygame.Surface((surf_w, surf_h), pygame.SRCALPHA)
        shifted = [(p[0] - min_x, p[1] - min_y) for p in poly]
        pygame.draw.polygon(glow, (*color, 60), shifted)
        self.screen.blit(glow, (min_x, min_y), special_flags=pygame.BLEND_RGBA_ADD)


    def _draw_bar_cap(self, cx, cy, r, fighter):
        """Clean procedural gem cap — no font rendering, sharp at any size.
        
        Layers: dark shell → fighter-colored diamond → highlight facet → border ring
        """
        cx, cy = int(cx), int(cy)
        color = fighter.health_bar_color
        dim   = tuple(max(0, int(c * 0.45)) for c in color)
        dark  = (18, 18, 25)

        # Shell
        pygame.draw.circle(self.screen, dark,  (cx, cy), r)
        pygame.draw.circle(self.screen, dim,   (cx, cy), r - 2)
        pygame.draw.circle(self.screen, dark,  (cx, cy), r - 5)

        # Gem diamond — sized to sit neatly inside the inner dark circle
        gem_r = r - 7
        gem = [
            (cx,        cy - gem_r),   # top
            (cx + gem_r, cy),          # right
            (cx,        cy + gem_r),   # bottom
            (cx - gem_r, cy),          # left
        ]
        pygame.draw.polygon(self.screen, color, gem)

        # Highlight facet (upper-left triangle of the diamond, 55% brighter)
        hi = tuple(min(255, int(c * 1.55)) for c in color)
        facet = [
            (cx,         cy - gem_r),  # top
            (cx + gem_r, cy),          # right  (top-right half)
            (cx,         cy),          # center
        ]
        pygame.draw.polygon(self.screen, hi, facet)

        # Small specular dot
        spec_r = max(1, gem_r // 3)
        pygame.draw.circle(self.screen, (255, 255, 255), (cx - spec_r, cy - spec_r), spec_r)

        # Outer border ring
        pygame.draw.circle(self.screen, (90, 90, 115), (cx, cy), r, 2)


    def _get_bar_color(self, fighter) -> tuple:
        """Returns the fighter's color, with a rapid blink effect below 15% HP."""
        hp_pct = max(0.0, fighter.health / fighter.max_health)
        if 0 < hp_pct < 0.15:
            if (pygame.time.get_ticks() // 100) % 2 == 0:
                return fighter.health_bar_color
            r, g, b = fighter.health_bar_color
            return (int(r * 0.4), int(g * 0.4), int(b * 0.4))
        return fighter.health_bar_color

