import pygame
import random
import math


class UIRenderer:
    """Handles rendering of the HUD, health bars, warnings, and CTA text."""
    
    def __init__(self, screen, font_medium, font_small):
        self.screen = screen
        self.font_medium = font_medium
        self.font_small = font_small
        self.white = (255, 255, 255)
        self.bg_color = (30, 30, 30)
        self.dark_border_color = (60, 60, 60)
        self.event_label_anim_timer = 0


    def draw(self, game):
        """Main draw method for all UI overlays."""
        self._draw_hud(game)

    def _draw_hud(self, game):
        """Draw Tekken-style static health bars flush above the arena."""
        ax, ay, aw, ah = game.arena_bounds
        bar_width = (aw // 2) - 20
        bar_height = 20
        bar_y = ay - bar_height - 10

        # Danger Zone shake at 10% HP
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
            fill_x = int(bar_x + (bar_width - red_fill_w))
            red_bar_color = self._get_bar_color(game.red)
            pygame.draw.rect(self.screen, red_bar_color,
                             (int(fill_x + red_shake_x), ry, red_fill_w, bar_height))
        pygame.draw.rect(self.screen, self.dark_border_color,
                         (rx, ry, bar_width, bar_height), 2)

        # --- VS Text ---
        vs_surface = self.font_small.render("VS", True, self.white)
        vs_rect = vs_surface.get_rect(center=(ax + (aw // 2), bar_y + (bar_height // 2)))
        self.screen.blit(vs_surface, vs_rect)

    def _get_bar_color(self, fighter):
        """Return the health bar color, blinking when HP < 15%."""
        hp_pct = max(0.0, fighter.health / fighter.max_health)
        if hp_pct < 0.15 and hp_pct > 0:
            # Rapid blink: alternate every 100ms between normal and dark shade
            if (pygame.time.get_ticks() // 100) % 2 == 0:
                return fighter.health_bar_color
            else:
                # 40% darker shade
                r, g, b = fighter.health_bar_color
                return (int(r * 0.4), int(g * 0.4), int(b * 0.4))
        return fighter.health_bar_color