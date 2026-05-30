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

# --- Matchup Label Layout ---
_LABEL_CENTER_Y  = SCREEN_HEIGHT // 4        # vertical anchor (~150px)
_LABEL_INSET_X   = SCREEN_WIDTH  // 4        # how far from center each side sits


class IntroRenderer:
    """
    Pluggable intro renderer.
    Game holds one instance: self.intro_renderer = IntroRenderer(...)
    """

    def __init__(self, screen, clock, f1_name, f2_name,
                 f1_color, f2_color, font_large,
                 f1_weapon="sword", f2_weapon="sword"):
        self.screen = screen
        self.clock = clock
        self.f1_weapon = f1_weapon
        self.f2_weapon = f2_weapon
        self.f1_name = f1_name
        self.f2_name = f2_name
        self.f1_color = f1_color
        self.f2_color = f2_color
        self.font_large = font_large
        
        # Pre-bake label fonts once — no per-frame allocation
        self._font_name   = pygame.font.Font(None, 52)   # fighter name
        self._font_weapon = pygame.font.Font(None, 26)   # weapon tag
        self._font_vs = pygame.font.Font(None, 32)
        self._text_cache = {}
        # Pre-allocate white flash surface to avoid per-frame allocations during countdown
        self._flash_surf = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT))
        self._flash_surf.fill(WHITE)

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
        return self._draw_old_title_screen()   

    def _draw_old_title_screen(self) -> bool:
        """Stub — old title screen removed. Returns False (no start trigger)."""
        return False

    # ------------------------------------------------------------------ #
    #  COUNTDOWN OVERLAY                                                   #
    #  Called from Game._draw_countdown_overlay()                         #
    # ------------------------------------------------------------------ #

    def draw_countdown(self, screen, stage, timer, durations, texts,
                       f1_color, f2_color, f1_bright, f2_bright,
                       flash_timer, flash_duration, font_large):
        def get_rendered_text(text, font, color):
            key = (text, color)
            if key not in self._text_cache:
                self._text_cache[key] = font.render(text, True, color)
            return self._text_cache[key]

        countdown_text = texts[stage]
        duration = durations[stage]
        progress = timer / max(1, duration)
        cx = SCREEN_WIDTH // 2
        cy = SCREEN_HEIGHT // 2

        # ── Stages 0-2: silent but show matchup labels ──────────────────
        if countdown_text != "FIGHT":
            # Still draw the flash on transitions so the beat feels rhythmic
            if flash_timer > 0:
                flash_alpha = int(200 * (flash_timer / max(1, flash_duration)))
                self._flash_surf.set_alpha(flash_alpha)
                screen.blit(self._flash_surf, (0, 0))

            self._draw_matchup_labels(
                screen, f1_color, f2_color,
                self.f1_name, self.f2_name,
                f1_bright, f2_bright,
            )

            # ── Big countdown number ─────────────────────────────────────
            # Pop-in: starts at 1.5× scale, settles to 1.0× in first 20% of duration.
            # Shrinks slightly toward end to build tension before the next beep.
            pop    = max(0.0, 1.0 - min(1.0, progress * 5))   # 0→1 during first 20%
            shrink = min(0.08, progress * 0.08)                # gentle shrink toward end
            scale  = 1.0 + pop * 0.5 - shrink
 
            num_surf = get_rendered_text(countdown_text, font_large, WHITE)
            new_w = max(1, int(num_surf.get_width()  * scale))
            new_h = max(1, int(num_surf.get_height() * scale))
            num_surf = pygame.transform.scale(num_surf, (new_w, new_h))
            num_rect = num_surf.get_rect(center=(cx, cy))
 
            # Glow halo in fighter colors — alternates between f1/f2 each stage
            glow_primary   = f1_color if stage % 2 == 0 else f2_color
            glow_secondary = f2_color if stage % 2 == 0 else f1_color
            for glow_color, alpha_val in [(glow_primary, 90), (glow_secondary, 55)]:
                glow = get_rendered_text(countdown_text, font_large, glow_color)
                glow = pygame.transform.scale(glow, (new_w, new_h))
                glow.set_alpha(alpha_val)
                for dx, dy in [(-5, 0), (5, 0), (0, -5), (0, 5),
                                (-4, -4), (4, 4), (-4, 4), (4, -4)]:
                    screen.blit(glow, num_rect.move(dx, dy))
 
            # Drop shadow
            shadow = get_rendered_text(countdown_text, font_large, BLACK)
            shadow = pygame.transform.scale(shadow, (new_w, new_h))
            shadow.set_alpha(160)
            screen.blit(shadow, num_rect.move(4, 4))
 
            # Main number
            screen.blit(num_surf, num_rect)

            return 

        # ── Stage 3: FIGHT ──────────────────────────────────────────────
        ease = 1 - (1 - progress) ** 3
        scale = 0.6 + ease * 1.0
        text_surface = get_rendered_text(countdown_text, font_large, WHITE)
        new_w = max(1, int(text_surface.get_width() * scale))
        new_h = max(1, int(text_surface.get_height() * scale))
        text_surface = pygame.transform.scale(text_surface, (new_w, new_h))
        text_rect = text_surface.get_rect(center=(cx, cy))
        
        for glow_color, alpha_val in [(f1_color, 80), (f2_color, 60)]:
            glow = get_rendered_text(countdown_text, font_large, glow_color)
            glow = pygame.transform.scale(glow, (new_w, new_h))
            glow.set_alpha(alpha_val)
            for dx, dy in [(-4,0),(4,0),(0,-4),(0,4),(-3,-3),(3,3),(-3,3),(3,-3)]:
                screen.blit(glow, text_rect.move(dx, dy))
        
        shadow = get_rendered_text(countdown_text, font_large, BLACK)
        shadow = pygame.transform.scale(shadow, (new_w, new_h))
        shadow.set_alpha(150)
        screen.blit(shadow, text_rect.move(3, 3))
        screen.blit(text_surface, text_rect)
        
        if flash_timer > 0:
            flash_alpha = int(200 * (flash_timer / max(1, flash_duration)))
            self._flash_surf.set_alpha(flash_alpha)
            screen.blit(self._flash_surf, (0, 0))


    # ------------------------------------------------------------------ #
    #  MATCHUP LABEL OVERLAY                                               #
    # ------------------------------------------------------------------ #
 
    def _draw_matchup_labels(self, screen, f1_color, f2_color,
                              f1_name, f2_name, f1_bright, f2_bright):
        """
        Render left/right matchup cards during the 3/2/1 countdown.
 
        Layout (centered on _LABEL_CENTER_Y):
            [F1 NAME]          [F2 NAME]
            [f1 weapon]        [f2 weapon]
 
        Each name gets a soft glow halo in the fighter's bright color.
        Weapon tag sits 4px below the name, dimmed to 60% brightness.
        A thin horizontal rule separates name from weapon.
        """
        cx      = SCREEN_WIDTH // 2
        cy      = _LABEL_CENTER_Y
        left_x  = cx - _LABEL_INSET_X   # center-x of left  card
        right_x = cx + _LABEL_INSET_X   # center-x of right card
 
        self._draw_label_card(screen, left_x,  cy, self.f1_weapon, f1_name,
                              f1_color, f1_bright, align='center')
        self._draw_label_card(screen, right_x, cy, self.f2_weapon, f2_name,
                              f2_color, f2_bright, align='center')

        # VS indicator — centered between the two cards
        vs_surf = self._font_vs.render("VS", True, (180, 180, 160))
        vs_rect = vs_surf.get_rect(center=(cx, cy))

        # Subtle glow behind VS
        vs_glow = self._font_weapon.render("VS", True, (200, 200, 220))
        vs_glow.set_alpha(30)
        for dx, dy in [(-2,0),(2,0),(0,-2),(0,2)]:
            screen.blit(vs_glow, vs_rect.move(dx, dy))

        screen.blit(vs_surf, vs_rect)
 
 
    def _draw_label_card(self, screen, cx, cy, weapon_name, fighter_name,
                         color, bright_color, align='center'):
        """
        Draw a single matchup card: glow halo → name → divider → weapon tag.
 
        Args:
            cx, cy:       Center anchor point.
            weapon_name:  Weapon identifier string (e.g. 'axe', 'dagger').
            fighter_name: Color/fighter name (e.g. 'CYAN', 'PURPLE').
            color:        Base fighter RGB tuple.
            bright_color: Brightened fighter RGB for glow.
            align:        Text alignment — 'center', 'left', or 'right'.
        """
        NAME_GAP   = 4    # px between name bottom and divider
        WEAPON_GAP = 6    # px between divider and weapon tag top
        RULE_W     = 60   # width of the horizontal divider rule
        dim_color  = tuple(max(0, int(c * 0.60)) for c in color)
 
        # --- Name surface ---
        display_name = fighter_name.split("_")[0]
        name_surf = self._font_name.render(display_name.upper(), True, WHITE)
        name_rect = name_surf.get_rect(center=(cx, cy))
 
        # Glow halo — 3 offset blits in bright_color at low alpha
        glow_surf = self._font_name.render(display_name.upper(), True, bright_color)
        glow_surf.set_alpha(55)
        for dx, dy in [(-2,0),(2,0),(0,-2),(0,2)]:
            screen.blit(glow_surf, name_rect.move(dx, dy))
 
        screen.blit(name_surf, name_rect)
 
        # --- Horizontal rule ---
        rule_y = name_rect.bottom + NAME_GAP
        rule_x = cx - RULE_W // 2
        rule_color = tuple(max(0, int(c * 0.50)) for c in color)
        pygame.draw.line(screen, rule_color,
                         (rule_x, rule_y), (rule_x + RULE_W, rule_y), 1)
 
        # --- Weapon tag ---
        weapon_surf = self._font_weapon.render(weapon_name.upper(), True, dim_color)
        weapon_rect = weapon_surf.get_rect(
            centerx=cx, top=rule_y + WEAPON_GAP
        )
        screen.blit(weapon_surf, weapon_rect)


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
        if align == "right": rect.right = x
        elif align == "left": rect.left = x
        else: rect.centerx = x
        rect.top = y
        self.screen.blit(surf, rect)

