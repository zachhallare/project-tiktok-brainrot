"""
UI Rendering system for the AlgoRot battle simulation.

This module provides the head-up display (HUD), including Tekken-style 
health bars, winner announcements, and other cinematic overlays.
"""

import pygame
import random
import math

GHOST_DELAY       = 40    # frames to hold ghost after a hit (~0.67s at 60fps)
GHOST_DRAIN_SPEED = 0.007 # ghost drain rate per frame (full bar drains in ~140 frames)


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
        
        # Tiny font for in-bar name labels and weapon tags
        self.font_tiny = pygame.font.Font(None, 18)
        
        self.white = (255, 255, 255)
        self.bg_color = (30, 30, 30)
        self.dark_border_color = (60, 60, 60)
        self.event_label_anim_timer = 0

        # ghost_pct: the "frozen" HP level shown as a trailing indicator.
        # ghost_delay: countdown before the ghost begins draining toward current HP.
        # _prev_pct: last frame's HP, used to detect new incoming hits.
        self.blue_ghost_pct   = 1.0
        self.red_ghost_pct    = 1.0
        self.blue_ghost_delay = 0
        self.red_ghost_delay  = 0
        self._prev_blue_pct   = 1.0
        self._prev_red_pct    = 1.0


    def draw(self, game):
        """Main entry point for rendering the entire UI overlay."""
        self._draw_hud(game)


    def _update_ghost(self, cur_pct, ghost_pct, ghost_delay, prev_pct):
        """Advance ghost bar state for one frame.
 
        On a new hit (cur_pct drops below prev_pct), the delay resets so the
        ghost holds at its current position before draining again. This lets
        rapid combos register visually as a single large gap rather than
        flickering micro-movements.
 
        Returns:
            (new_ghost_pct, new_ghost_delay)
        """
        # New hit detected — reset hold timer (do NOT snap ghost to current HP)
        if cur_pct < prev_pct - 0.001:
            ghost_delay = GHOST_DELAY
 
        if cur_pct < ghost_pct:
            # HP is below ghost: either holding or actively draining
            if ghost_delay > 0:
                ghost_delay -= 1          # hold phase
            else:
                ghost_pct = max(cur_pct, ghost_pct - GHOST_DRAIN_SPEED)
        else:
            # HP matched or exceeded ghost (round reset / full heal) — sync instantly
            ghost_pct  = cur_pct
            ghost_delay = 0
 
        return ghost_pct, ghost_delay


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

        # --- Update ghost bars ---
        self.blue_ghost_pct, self.blue_ghost_delay = self._update_ghost(
            blue_pct, self.blue_ghost_pct, self.blue_ghost_delay, self._prev_blue_pct
        )

        self.red_ghost_pct, self.red_ghost_delay = self._update_ghost(
            red_pct, self.red_ghost_pct, self.red_ghost_delay, self._prev_red_pct
        )

        self._prev_blue_pct = blue_pct
        self._prev_red_pct  = red_pct

        # pulse fires every 80 ms (6 frames at 60fps), so it reads as a heartbeat.
        pulse = (pygame.time.get_ticks() // 80) % 2 == 0
        bsx = random.randint(-1, 1) if blue_pct <= 0.10 and pulse else 0
        bsy = random.randint(-1, 1) if blue_pct <= 0.10 and pulse else 0
        rsx = random.randint(-1, 1) if red_pct  <= 0.10 and pulse else 0
        rsy = random.randint(-1, 1) if red_pct  <= 0.10 and pulse else 0

        # Blue bar: left side, arrow tip points RIGHT (inward toward VS)
        bx = ax + CAP_R * 2 + bsx
        by = bar_y + bsy
        self._draw_bar_body(bx, by, BAR_W, BAR_H, TIP, blue_pct, self.blue_ghost_pct, game.blue, 'right')
        self._draw_bar_cap(ax + CAP_R + bsx, by + BAR_H // 2, CAP_R, game.blue)

        # Red bar: right side, arrow tip points LEFT (inward toward VS)
        rx = ax + aw - CAP_R * 2 - BAR_W + rsx
        ry = bar_y + rsy
        self._draw_bar_body(rx, ry, BAR_W, BAR_H, TIP, red_pct, self.red_ghost_pct, game.red, 'left')
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


    def _draw_bar_labels(self, x, y, w, h, name, weapon, fighter, facing):
        """Render fighter name and weapon tag overlaid inside the bar body.
 
        Name: bold-ish, white, left/right aligned inside the fill zone.
        Weapon: tiny, fighter-color at 55% brightness, anchored to the outer edge.
        Both are clipped to the bar rect so they never bleed outside.
        """
        color     = fighter.health_bar_color
        dim_color = tuple(max(0, int(c * 0.55)) for c in color)
 
        name_surf   = self.font_tiny.render(name.upper(),   True, (220, 220, 230))
        weapon_surf = self.font_tiny.render(weapon.upper(), True, dim_color)
 
        pad = 5  # inner horizontal padding from bar edge
 
        if facing == 'right':
            # Name left-aligned from bar start
            name_rect   = name_surf.get_rect(midleft=(x + pad, y + h // 2))
            # Weapon right-aligned toward the tip end
            weapon_rect = weapon_surf.get_rect(midright=(x + w - pad, y + h // 2))
        else:
            # Mirror for the right bar
            name_rect   = name_surf.get_rect(midright=(x + w - pad, y + h // 2))
            weapon_rect = weapon_surf.get_rect(midleft=(x + pad, y + h // 2))
 
        # Clip to bar rect so text never escapes the body
        old_clip = self.screen.get_clip()
        self.screen.set_clip(pygame.Rect(x, y, w, h))
        self.screen.blit(name_surf,   name_rect)
        self.screen.blit(weapon_surf, weapon_rect)
        self.screen.set_clip(old_clip)


    def _draw_bar_body(self, x, y, w, h, tip, hp_pct, ghost_pct, fighter, facing):
        """Arrow-shaped bar: ghost drain layer → active fill → stripes → dividers → border.
 
        Args:
            hp_pct:    Current health fraction (0.0 – 1.0).
            ghost_pct: Delayed ghost fraction, always >= hp_pct. The gap between
                       ghost and active fill is rendered in a mid-bright fighter color,
                       making large damage chunks dramatically visible.
        """
        color   = self._get_bar_color(fighter)
        half_h  = h // 2

        # Arrow-shaped background polygon
        if facing == 'right':
            bg_poly = [(x, y), (x+w, y), (x+w+tip, y+half_h), (x+w, y+h), (x, y+h)]
        else:
            bg_poly = [(x, y), (x+w, y), (x+w, y+h), (x, y+h), (x-tip, y+half_h)]

        # 1. Ghost drain layer — entire arrow filled with dim fighter color
        ghost_bg = tuple(max(0, int(c * 0.22)) for c in fighter.health_bar_color)
        pygame.draw.polygon(self.screen, ghost_bg, bg_poly)
        ghost_border_color = tuple(max(0, int(c * 0.45)) for c in fighter.health_bar_color)
        pygame.draw.polygon(self.screen, ghost_border_color, bg_poly, 1)
 
        # 2. Ghost fill (the trailing indicator — sits between ghost_pct and hp_pct)
        ghost_fill_w = int(w * ghost_pct)
        fill_w       = int(w * hp_pct)
 
        if ghost_fill_w > fill_w:
            ghost_color = tuple(max(0, int(c * 0.48)) for c in fighter.health_bar_color)
            if facing == 'right':
                ghost_poly = [
                    (x + fill_w, y), (x + ghost_fill_w, y),
                    (x + ghost_fill_w, y + h), (x + fill_w, y + h)
                ]
            else:
                g_left  = x + w - ghost_fill_w
                g_right = x + w - fill_w
                ghost_poly = [
                    (g_left, y), (g_right, y),
                    (g_right, y + h), (g_left, y + h)
                ]
            pygame.draw.polygon(self.screen, ghost_color, ghost_poly)
 
        # 3. Active fill
        if fill_w > 0:
            is_full = hp_pct >= 1.0
            if facing == 'right':
                fill_x    = x
                fill_poly = bg_poly if is_full else [
                    (x, y), (x+fill_w, y), (x+fill_w, y+h), (x, y+h)
                ]
            else:
                fill_x    = x + w - fill_w
                fill_poly = bg_poly if is_full else [
                    (fill_x, y), (x+w, y), (x+w, y+h), (fill_x, y+h)
                ]
 
            self._draw_poly_glow(fill_poly, color, expand=5)
            pygame.draw.polygon(self.screen, color, fill_poly)
 
            # Diagonal stripe texture clipped to fill rect
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
 
        # 4. Segment dividers
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
        dim = tuple(max(0, int(c * 0.45)) for c in color)
        dark = (18, 18, 25)

        # Shell
        pygame.draw.circle(self.screen, dark,  (cx, cy), r)
        pygame.draw.circle(self.screen, dim,   (cx, cy), r - 2)
        pygame.draw.circle(self.screen, dark,  (cx, cy), r - 5)

        # Gem diamond — sized to sit neatly inside the inner dark circle
        gem_r = r - 7
        gem = [
            (cx, cy - gem_r),   # top
            (cx + gem_r, cy),   # right
            (cx, cy + gem_r),   # bottom
            (cx - gem_r, cy),   # left
        ]
        pygame.draw.polygon(self.screen, color, gem)

        # Highlight facet (upper-left triangle of the diamond, 55% brighter)
        hi = tuple(min(255, int(c * 1.55)) for c in color)
        facet = [
            (cx, cy - gem_r),  # top
            (cx + gem_r, cy),          # right  (top-right half)
            (cx, cy),          # center
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
        if 0 < hp_pct <= 0.10:
            if (pygame.time.get_ticks() // 100) % 2 == 0:
                return fighter.health_bar_color
            r, g, b = fighter.health_bar_color
            return (int(r * 0.4), int(g * 0.4), int(b * 0.4))
        return fighter.health_bar_color

