"""
Owns all post-fight winner announcement visuals.

To redesign the outro: only edit this file.
main.py and draw() are never touched.

Interface:
    OutroRenderer(screen, clock, font_large).draw_winner(...)
"""

import pygame
import math

from config import SCREEN_WIDTH, SCREEN_HEIGHT, WHITE, FIGHTER_RADIUS


class OutroRenderer:
    """
    Pluggable outro renderer.
    Game holds one instance: self.outro_renderer = OutroRenderer(...)

    Receives all needed state as arguments to draw_winner() — never holds
    a reference to Game, so it cannot accidentally mutate combat state.
    """

    def __init__(self, screen: pygame.Surface, clock: pygame.time.Clock,
                 font_large: pygame.font.Font):
        self.screen = screen
        self.clock = clock
        self.font_large = font_large

    # ------------------------------------------------------------------ #
    #  WINNER OUTRO                                                        #
    #  Called from Game._draw_winner_outro() every frame while active.    #
    # ------------------------------------------------------------------ #

    def draw_winner(
        self,
        screen: pygame.Surface,
        winner,
        winner_text: str,
        f1_color: tuple,
        f2_color: tuple,
        blue,
        red,
        particles,
        damage_numbers,
        arena_bounds: list,
        sound_manager,
        winner_particles_spawned: bool,
    ):
        """
        Draw the winner announcement screen.

        Verbatim port from the original draw() winner block — zero logic changes.
        Safe to redesign by replacing the body of this method only.

        Note: winner_particles_spawned is read-only here. Game._draw_winner_outro()
        sets self.winner_particles_spawned = True after this call returns, so
        particles are only spawned on the first frame.
        """
        win_color = f1_color if winner == blue else f2_color
        ax, ay, aw, ah = arena_bounds

        # ── Fireworks burst — first frame only ───────────────────────────
        if not winner_particles_spawned:
            damage_numbers.clear()
            particles.clear()

            cx_burst = SCREEN_WIDTH // 2
            cy_burst = SCREEN_HEIGHT // 2
            particles.emit_explosion(cx_burst, cy_burst, win_color, count=60)

            # Extra bursts from upper-left and upper-right
            for bx, by in [(cx_burst - 80, cy_burst - 60),
                           (cx_burst + 80, cy_burst - 60)]:
                particles.emit_explosion(bx, by, win_color, count=25)

            if sound_manager:
                sound_manager.play_victory_fireworks()

        # ── Layout math ──────────────────────────────────────────────────
        cx = SCREEN_WIDTH // 2
        text_surface = self.font_large.render(winner_text, True, WHITE)
        gap = 25
        total_height = (FIGHTER_RADIUS * 2) + gap + text_surface.get_height()
        top_y = SCREEN_HEIGHT // 2 - total_height // 2
        circle_cy = top_y + FIGHTER_RADIUS

        # ── Winner body, repositioned to center ──────────────────────────
        draw_offset = (cx - winner.x, circle_cy - winner.y)
        winner.draw_body_only(screen, draw_offset)

        # ── Subtle glow ring ─────────────────────────────────────────────
        glow_surf = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT), pygame.SRCALPHA)
        pygame.draw.circle(glow_surf, (*win_color, 18), (cx, circle_cy), FIGHTER_RADIUS + 14)
        screen.blit(glow_surf, (0, 0))

        # ── Spinning weapon orbiting the fighter body ─────────────────────
        raw_sprite = None
        orig_w = 0
        if hasattr(winner, '_renderer') and hasattr(winner._renderer, '_weapon_base'):
            raw_sprite = winner._renderer._weapon_base
            orig_w = winner._renderer._orig_w

        if raw_sprite:
            spin_angle = (pygame.time.get_ticks() / 150.0) % (2 * math.pi)
            cos_a = math.cos(spin_angle)
            sin_a = math.sin(spin_angle)

            scaled_sprite = pygame.transform.rotozoom(raw_sprite, 0, 1.0)
            scaled_w = orig_w * 1.0

            handle_x = cx + cos_a * (FIGHTER_RADIUS + 5)
            handle_y = circle_cy + sin_a * (FIGHTER_RADIUS + 5)

            rotated = pygame.transform.rotate(scaled_sprite, -math.degrees(spin_angle))
            rot_center_x = handle_x + (scaled_w / 2) * cos_a
            rot_center_y = handle_y + (scaled_w / 2) * sin_a

            weapon_rect = rotated.get_rect(center=(int(rot_center_x), int(rot_center_y)))

            # Clip weapon to arena bounds so it doesn't bleed into the HUD
            clip_rect = pygame.Rect(int(ax), int(ay), int(aw), int(ah))
            screen.set_clip(clip_rect)
            screen.blit(rotated, weapon_rect)
            screen.set_clip(None)

        # ── "WINS" text with color glow ───────────────────────────────────
        text_cy = top_y + FIGHTER_RADIUS * 2 + gap + text_surface.get_height() // 2
        text_rect = text_surface.get_rect(center=(cx, text_cy))

        glow_surface = self.font_large.render(winner_text, True, win_color)
        glow_surface.set_alpha(90)
        for dx, dy in [(-4, 0), (4, 0), (0, -4), (0, 4)]:
            screen.blit(glow_surface, text_rect.move(dx, dy))

        screen.blit(text_surface, text_rect)

