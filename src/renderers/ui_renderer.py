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
        bar_width = (aw // 2) - 20
        bar_height = 20
        bar_y = ay - bar_height - 10

        # Danger Zone Feedback: Shake the bar if HP < 10%
        blue_hp_pct = max(0.0, game.blue.health / game.blue.max_health)
        blue_shake_x = random.randint(-4, 4) if blue_hp_pct <= 0.10 else 0
        blue_shake_y = random.randint(-4, 4) if blue_hp_pct <= 0.10 else 0

        red_hp_pct = max(0.0, game.red.health / game.red.max_health)
        red_shake_x = random.randint(-4, 4) if red_hp_pct <= 0.10 else 0
        red_shake_y = random.randint(-4, 4) if red_hp_pct <= 0.10 else 0

        # --- Blue (Left) Bar ---
        bar_x = ax
        blue_fill_w = max(0, min(bar_width, int(bar_width * blue_hp_pct)))

        bx = int(bar_x + blue_shake_x)
        by = int(bar_y + blue_shake_y)
        pygame.draw.rect(self.screen, self.bg_color,
                         (bx, by, bar_width, bar_height))
        if blue_fill_w > 0:
            blue_bar_color = self._get_bar_color(game.blue)
            pygame.draw.rect(self.screen, blue_bar_color,
                             (bx, by, blue_fill_w, bar_height))
        pygame.draw.rect(self.screen, self.dark_border_color,
                         (bx, by, bar_width, bar_height), 2)

        # --- Red (Right) Bar ---
        bar_x = ax + aw - bar_width
        red_fill_w = max(0, min(bar_width, int(bar_width * red_hp_pct)))

        rx = int(bar_x + red_shake_x)
        ry = int(bar_y + red_shake_y)
        pygame.draw.rect(self.screen, self.bg_color,
                         (rx, ry, bar_width, bar_height))
        if red_fill_w > 0:
            # Red bar fills from right to left for symmetry
            fill_x = int(bar_x + (bar_width - red_fill_w))
            red_bar_color = self._get_bar_color(game.red)
            pygame.draw.rect(self.screen, red_bar_color,
                             (int(fill_x + red_shake_x), ry, red_fill_w, bar_height))
        pygame.draw.rect(self.screen, self.dark_border_color,
                         (rx, ry, bar_width, bar_height), 2)

        # --- VS Text Indicator ---
        vs_surface = self.font_small.render("VS", True, self.white)
        vs_rect = vs_surface.get_rect(center=(ax + (aw // 2), bar_y + (bar_height // 2)))
        self.screen.blit(vs_surface, vs_rect)

    def _get_bar_color(self, fighter) -> tuple:
        """Returns the fighter's theme color, with a rapid blink effect at low HP.

        Args:
            fighter: The fighter whose health bar is being colored.

        Returns:
            An RGB tuple.
        """
        hp_pct = max(0.0, fighter.health / fighter.max_health)
        if hp_pct < 0.15 and hp_pct > 0:
            # Rapid blink: alternate every 100ms between normal and 40% darker shade
            if (pygame.time.get_ticks() // 100) % 2 == 0:
                return fighter.health_bar_color
            else:
                r, g, b = fighter.health_bar_color
                return (int(r * 0.4), int(g * 0.4), int(b * 0.4))
        return fighter.health_bar_color