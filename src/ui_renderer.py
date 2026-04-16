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

    def draw(self, game):
        """Main draw method for all UI overlays."""
        # 1. Tekken-style HUD
        self._draw_hud(game)
        
        # 2. Sudden Death Warning
        if getattr(game, 'total_parries', 0) >= 15:
            sd_text = self.font_medium.render("SUDDEN DEATH", True, (255, 0, 0))
            sd_ax, sd_ay, sd_aw, sd_ah = game.arena_bounds
            sd_y = sd_ay - 55
            sd_rect = sd_text.get_rect(center=(sd_ax + sd_aw // 2, sd_y))
            if (game.round_timer // 8) % 2 == 0:
                self.screen.blit(sd_text, sd_rect)
                
        # 3. WHO ARE YOU ROOTING FOR? CTA
        cta_text = self.font_small.render("WHO ARE YOU ROOTING FOR?", True, self.white)
        ax, ay, aw, ah = game.arena_bounds
        cta_y = ay + ah + 30
        cta_rect = cta_text.get_rect(center=(ax + aw // 2, cta_y))
        
        # Adding a subtle pulse
        pulse_alpha = int(155 + 100 * math.sin(game.round_timer * 0.05))
        pulse_surf = cta_text.copy()
        pulse_surf.set_alpha(pulse_alpha)
        self.screen.blit(pulse_surf, cta_rect)

    def _draw_hud(self, game):
        """Draw Tekken-style static health bars flush above the arena."""
        ax, ay, aw, ah = game.arena_bounds
        bar_width = (aw // 2) - 20
        bar_height = 20
        bar_y = ay - bar_height - 10  # 10px padding above arena top line
        
        # Calculate Danger Zone Offsets (10% HP threshold)
        blue_hp_pct = max(0.0, game.blue.health / game.blue.max_health)
        blue_shake_x = random.randint(-4, 4) if blue_hp_pct <= 0.10 else 0
        blue_shake_y = random.randint(-4, 4) if blue_hp_pct <= 0.10 else 0
        
        red_hp_pct = max(0.0, game.red.health / game.red.max_health)
        red_shake_x = random.randint(-4, 4) if red_hp_pct <= 0.10 else 0
        red_shake_y = random.randint(-4, 4) if red_hp_pct <= 0.10 else 0
        
        # --- Blue (Left) Bar: depletes right-to-left, anchored to left arena wall ---
        bar_x = ax
        blue_fill_w = int(bar_width * blue_hp_pct)
        
        # Background (missing health)
        pygame.draw.rect(self.screen, self.bg_color, (bar_x + blue_shake_x, bar_y + blue_shake_y, bar_width, bar_height))
        # Health fill (anchored to left edge, depletes from right)
        if blue_fill_w > 0:
            pygame.draw.rect(self.screen, game.blue.color,
                            (bar_x + blue_shake_x, bar_y + blue_shake_y, blue_fill_w, bar_height))
        # Dark border outline
        pygame.draw.rect(self.screen, self.dark_border_color, (bar_x + blue_shake_x, bar_y + blue_shake_y, bar_width, bar_height), 2)
        
        # Blue Energy Bar
        energy_pct_blue = max(0.0, game.blue.parry_energy / game.blue.max_parry_energy)
        energy_bar_width = bar_width
        energy_bar_y = bar_y + bar_height + 4
        # Draw background (dark gray)
        pygame.draw.rect(self.screen, (40, 40, 40), (bar_x + blue_shake_x, energy_bar_y + blue_shake_y, energy_bar_width, 3))
        # Draw current energy (cyan)
        if energy_pct_blue > 0:
            pygame.draw.rect(self.screen, (0, 255, 255), (bar_x + blue_shake_x, energy_bar_y + blue_shake_y, int(energy_bar_width * energy_pct_blue), 3))
        
        # --- Red (Right) Bar: depletes left-to-right, anchored to right arena wall ---
        bar_x = ax + aw - bar_width
        red_fill_w = int(bar_width * red_hp_pct)
        
        # Background (missing health)
        pygame.draw.rect(self.screen, self.bg_color, (bar_x + red_shake_x, bar_y + red_shake_y, bar_width, bar_height))
        # Health fill (anchored to right edge, depletes from left)
        if red_fill_w > 0:
            fill_x = bar_x + (bar_width - red_fill_w)
            pygame.draw.rect(self.screen, game.red.color,
                            (fill_x + red_shake_x, bar_y + red_shake_y, red_fill_w, bar_height))
        # Dark border outline
        pygame.draw.rect(self.screen, self.dark_border_color, (bar_x + red_shake_x, bar_y + red_shake_y, bar_width, bar_height), 2)
        
        # Red Energy Bar
        energy_pct_red = max(0.0, game.red.parry_energy / game.red.max_parry_energy)
        red_energy_x = bar_x + (bar_width - energy_bar_width)
        # Draw background (dark gray)
        pygame.draw.rect(self.screen, (40, 40, 40), (red_energy_x + red_shake_x, energy_bar_y + red_shake_y, energy_bar_width, 3))
        # Draw current energy (cyan)
        if energy_pct_red > 0:
            red_energy_fill_w = int(energy_bar_width * energy_pct_red)
            red_energy_fill_x = red_energy_x + (energy_bar_width - red_energy_fill_w)
            pygame.draw.rect(self.screen, (0, 255, 255), (red_energy_fill_x + red_shake_x, energy_bar_y + red_shake_y, red_energy_fill_w, 3))
        
        # --- VS Text (centered between the two bars) ---
        vs_surface = self.font_small.render("VS", True, self.white)
        vs_rect = vs_surface.get_rect(center=(ax + (aw // 2), bar_y + (bar_height // 2)))
        self.screen.blit(vs_surface, vs_rect)
