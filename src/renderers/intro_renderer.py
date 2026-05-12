"""
Owns all pre-fight visuals:
  - TITLE screen (draw_title → returns True when player starts)
  - In-game countdown overlay (draw_countdown)

To redesign the intro: only edit this file.
main.py and draw() are never touched.
"""

import pygame
import math
from config import SCREEN_WIDTH, SCREEN_HEIGHT, WHITE, BLACK, YELLOW


class IntroRenderer:
    """
    Pluggable intro renderer.
    Game holds one instance: self.intro_renderer = IntroRenderer(...)
    """

    def __init__(self, screen, clock, f1_name, f2_name,
                 f1_color, f2_color, font_large):
        self.screen = screen
        self.clock = clock
        self.f1_name = f1_name
        self.f2_name = f2_name
        self.f1_color = f1_color
        self.f2_color = f2_color
        self.font_large = font_large

    # ------------------------------------------------------------------ #
    #  TITLE SCREEN                                                        #
    #  Called from run() when game_state == 'TITLE'                       #
    #  Returns True when the player triggers game start                   #
    # ------------------------------------------------------------------ #

    def draw_title(self) -> bool:
        """
        Draw the TITLE/intro screen.
        Returns True if the player pressed SPACE or clicked → triggers game start.

        ── To swap intro styles: replace or extend this method only. ──
        """
        return self._draw_old_title_screen()   # ← change this one line to swap styles

    # ------------------------------------------------------------------ #
    #  COUNTDOWN OVERLAY                                                   #
    #  Called from Game._draw_countdown_overlay()                         #
    # ------------------------------------------------------------------ #

    def draw_countdown(self, screen, stage, timer, durations, texts,
                       f1_color, f2_color, f1_bright, f2_bright,
                       flash_timer, flash_duration, font_large):
        """
        In-game countdown overlay (3, 2, 1, FIGHT).
        Copied verbatim from original draw() — safe to redesign here.
        """
        countdown_text = texts[stage]
        # ── Silent countdown: hide 3/2/1, only show FIGHT ──
        if countdown_text != "FIGHT":
            # Still draw the flash on transitions so the beat feels rhythmic
            if flash_timer > 0:
                flash_alpha = int(200 * (flash_timer / max(1, flash_duration)))
                flash_surf = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT))
                flash_surf.fill(WHITE)
                flash_surf.set_alpha(flash_alpha)
                screen.blit(flash_surf, (0, 0))
            return  # ← skip all number text rendering
        duration = durations[stage]
        progress = timer / max(1, duration)
        cx = SCREEN_WIDTH // 2
        cy = SCREEN_HEIGHT // 2

        ease = 1 - (1 - progress) ** 3
        scale = 0.6 + ease * 1.0
        text_surface = font_large.render(countdown_text, True, WHITE)
        new_w = max(1, int(text_surface.get_width() * scale))
        new_h = max(1, int(text_surface.get_height() * scale))
        text_surface = pygame.transform.smoothscale(text_surface, (new_w, new_h))
        text_rect = text_surface.get_rect(center=(cx, cy))
        
        for glow_color, alpha_val in [(f1_color, 80), (f2_color, 60)]:
            glow = font_large.render(countdown_text, True, glow_color)
            glow = pygame.transform.smoothscale(glow, (new_w, new_h))
            glow.set_alpha(alpha_val)
            for dx, dy in [(-4,0),(4,0),(0,-4),(0,4),(-3,-3),(3,3),(-3,3),(3,-3)]:
                screen.blit(glow, text_rect.move(dx, dy))
        
        shadow = font_large.render(countdown_text, True, BLACK)
        shadow = pygame.transform.smoothscale(shadow, (new_w, new_h))
        shadow.set_alpha(150)
        screen.blit(shadow, text_rect.move(3, 3))
        screen.blit(text_surface, text_rect)
        
        if flash_timer > 0:
            flash_alpha = int(200 * (flash_timer / max(1, flash_duration)))
            flash_surf = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT))
            flash_surf.fill(WHITE)
            flash_surf.set_alpha(flash_alpha)
            screen.blit(flash_surf, (0, 0))

    # ------------------------------------------------------------------ #
    #  Shared helpers                                                      #
    # ------------------------------------------------------------------ #

    def _blit_weapon(self, surf, x, y, size, flip=False):
        scaled = pygame.transform.scale(surf, (size, size))
        if flip:
            scaled = pygame.transform.flip(scaled, True, False)
        self.screen.blit(scaled, (x, y))

    def _draw_crossed_weapons(self, surf_a, surf_b, cx, cy, size, angle_offset):
        self._blit_weapon(surf_a, cx - size - 5, cy - size // 2, size)
        self._blit_weapon(surf_b, cx + 5,         cy - size // 2, size, flip=True)

    def _draw_name_tag(self, name, x, y, alpha, align="center"):
        font = pygame.font.SysFont("Impact", 28)
        surf = font.render(name.upper(), True, WHITE)
        surf.set_alpha(alpha)
        rect = surf.get_rect()
        if align == "right":   rect.right = x
        elif align == "left":  rect.left = x
        else:                  rect.centerx = x
        rect.top = y
        self.screen.blit(surf, rect)

