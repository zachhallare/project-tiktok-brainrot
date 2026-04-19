=========================================
order to run:
1. prompts 0-3 (feat/combo-parry-physics)
2. prompts 4-gapC (vfx/hit-feedback-stack)
3. prompts 8-10 (system/chaos-events-loop)
=========================================





================================= PROMPT 4 =================================
First check if a ParticleSystem already exists in src/effects.py.
If it does, add the emit() call there instead of creating a new file.
Only create src/particles.py if no particle system exists.

Add a radial impact particle system that fires on every piercing hit.
Implement in a new file src/particles.py.

Step 1 — particles.py:
    import math, random, pygame

    class Particle:
        def __init__(self, x, y, color):
            angle = random.uniform(0, math.tau)
            speed = random.uniform(2, 7)
            self.x = x
            self.y = y
            self.vx = math.cos(angle) * speed
            self.vy = math.sin(angle) * speed
            self.life = 1.0
            self.decay = random.uniform(0.06, 0.12)
            self.color = color
            self.radius = random.randint(2, 5)

        def update(self):
            self.x += self.vx
            self.y += self.vy
            self.vx *= 0.88
            self.vy *= 0.88
            self.life -= self.decay
            return self.life > 0

        def draw(self, surf):
            alpha = int(255 * self.life)
            s = pygame.Surface((self.radius*2, self.radius*2), pygame.SRCALPHA)
            pygame.draw.circle(s, (*self.color, alpha),
                               (self.radius, self.radius), self.radius)
            surf.blit(s, (int(self.x - self.radius), int(self.y - self.radius)))

    class ParticleSystem:
        def __init__(self):
            self.particles = []

        def emit(self, x, y, color, count=18):
            for _ in range(count):
                self.particles.append(Particle(x, y, color))

        def update_and_draw(self, surf):
            self.particles = [p for p in self.particles if p.update()]
            for p in self.particles:
                p.draw(surf)

Step 2 — In combat_manager.py, on every piercing hit:
    particle_system.emit(defender.x, defender.y, defender.color, count=18)

Step 3 — In the main draw loop, call after drawing fighters:
    particle_system.update_and_draw(screen)





================================= PROMPT 5 =================================
Make the arena border a feedback layer.

Add to game state:
    border_flash_timer = 0
    border_color = YELLOW
    border_width = 2

    def trigger_border_flash(color, width=4, frames=3):
        global border_flash_timer, border_color, border_width
        border_color = color
        border_width = width
        border_flash_timer = frames

Call at these events:
    Any body hit:        trigger_border_flash((255,255,255), 3, 3)
    Pierce hit:          trigger_border_flash((255,255,255), 5, 4)
    Parry deflection:    trigger_border_flash((100,200,255), 4, 3)

In draw loop:
    if border_flash_timer > 0:
        pygame.draw.rect(screen, border_color, ARENA_RECT, border_width)
        border_flash_timer -= 1
    else:
        either_low = (game.blue.health/game.blue.max_health < 0.10 or
                      game.red.health/game.red.max_health < 0.10)
        if either_low:
            t = (pygame.time.get_ticks() % 500) / 500.0
            g = int(255 * (1 - t))
            pygame.draw.rect(screen, (255, g, 0), ARENA_RECT, 2)
        else:
            pygame.draw.rect(screen, YELLOW, ARENA_RECT, 2)





================================= PROMPT 6 =================================
Replace the instant health bar shrink with a two-layer ghost bar system.

Step 1 — In Fighter.__init__, add:
    self.display_hp = self.health

Step 2 — In Fighter.update every frame:
    self.display_hp += (self.health - self.display_hp) * 0.04

Step 3 — In ui_renderer.py, replace single bar draw with three layers:

    # Layer 1: Ghost bar in dark muted color
    ghost_w = max(0, int(bar_width * (self.display_hp / self.max_health)))
    pygame.draw.rect(screen, (120, 20, 20),
                     (bar_x, bar_y, ghost_w, bar_height))

    # Layer 2: Active bar in fighter color
    real_w = max(1, int(bar_width * (self.health / self.max_health))) \
             if self.health > 0 else 0
    pygame.draw.rect(screen, fighter.color,
                     (bar_x, bar_y, real_w, bar_height))

    # Layer 3: Sub-10% white pulse overlay
    if self.health / self.max_health < 0.10 and self.health > 0:
        t = math.sin(pygame.time.get_ticks() * 0.008) * 0.5 + 0.5
        pulse_surf = pygame.Surface((real_w, bar_height), pygame.SRCALPHA)
        pulse_surf.fill((255, 255, 255, int(180 * t)))
        screen.blit(pulse_surf, (bar_x, bar_y))

Apply same logic mirrored for the right-anchored red bar.





================================= PROMPT 7 =================================
Add a visual impact sequence when a parry deflection triggers
(sword-vs-sword collision). Since guard break no longer exists,
this is now the most hype moment in the game — give it weight.
Implement in src/effects.py.

Step 1 — Fixed chromatic aberration:
    def draw_chroma_aberration(screen, offset=4):
        snap = screen.copy()
        r_surf = snap.copy()
        b_surf = snap.copy()
        r_surf.fill((255, 0, 0), special_flags=pygame.BLEND_RGB_MULT)
        b_surf.fill((0, 0, 255), special_flags=pygame.BLEND_RGB_MULT)
        screen.blit(r_surf, (-offset, 0), special_flags=pygame.BLEND_RGB_ADD)
        screen.blit(b_surf, (offset,  0), special_flags=pygame.BLEND_RGB_ADD)

Step 2 — Parry sequence state machine:
    parry_phase = None
    parry_timer = 0

    def trigger_parry_sequence():
        global parry_phase, parry_timer
        parry_phase = 'flash'
        parry_timer = 2

Step 3 — Advance each frame:
    if parry_phase == 'flash':
        screen.fill((255, 255, 255))
        parry_timer -= 1
        if parry_timer <= 0:
            parry_phase = 'hitstop'
            parry_timer = 6

    elif parry_phase == 'hitstop':
        parry_timer -= 1
        if parry_timer <= 0:
            parry_phase = 'chroma'
            parry_timer = 4

    elif parry_phase == 'chroma':
        draw_chroma_aberration(screen, offset=5)
        parry_timer -= 1
        if parry_timer <= 0:
            parry_phase = 'text'
            parry_timer = 25

    elif parry_phase == 'text':
        font = pygame.font.SysFont(None, 72, bold=True)
        label = font.render("PARRY", True, (100, 200, 255))
        screen.blit(label, label.get_rect(center=(SCREEN_WIDTH//2, SCREEN_HEIGHT//2)))
        parry_timer -= 1
        if parry_timer <= 0:
            parry_phase = None





================================= PROMPT GAP-C =================================
In ui_renderer.py, in the HUD draw method, after drawing each 
fighter's health bar, add a small combo-state label directly 
below it.

Add a font reference at the top of the HUD draw method:
    combo_font = pygame.font.SysFont(None, 28, bold=True)

For the blue fighter (left bar), after drawing the bar layers:
    stage = game.blue.combo_stage
    if stage == 0:
        combo_text = ""
    elif stage == 1:
        combo_text = "COMBO x2"
        combo_color = (255, 220, 80)
    else:
        combo_text = "PIERCE READY"
        combo_color = (100, 200, 255)

    if combo_text:
        label = combo_font.render(combo_text, True, combo_color)
        screen.blit(label, (bar_x, bar_y + bar_height + 4))

Apply the same logic mirrored for the red fighter (right bar),
right-aligning the label:
    if combo_text:
        label = combo_font.render(combo_text, True, combo_color)
        screen.blit(label,
            (bar_x + bar_width - label.get_width(),
             bar_y + bar_height + 4))

Do not add any label at combo_stage == 0. The absence of text 
at stage 0 is intentional — it makes COMBO x2 and PIERCE READY 
feel like events worth watching for.


==================================================================================


================================= PROMPT 8 =================================
Create a new file src/chaos_manager.py. The old codebase had this
but it was removed. Rebuild it with the following spec.

Full class:

    import random
    import pygame
    from config import (
        FPS, SCREEN_WIDTH, SCREEN_HEIGHT,
        NEON_YELLOW, WHITE, BLACK
    )

    CHAOS_DURATION   = 4.0   # seconds (Blackout override is 3.0)
    CHAOS_INTERVAL   = 3.0   # fixed seconds between events
    BLACKOUT_DURATION = 3.0  # Blackout is riskier, keep it shorter

    class ChaosManager:
        EVENTS = [
            "HYPER SPEED",
            "ULTRA KNOCKBACK",
            "THE CRUSHER",
            "BLACKOUT",
        ]

        def __init__(self):
            self.active_event   = None
            self.last_event     = None
            self.event_timer    = 0.0   # seconds remaining in active event
            self.interval_timer = CHAOS_INTERVAL  # countdown to next event
            self.crusher_arena_mult = 1.0
            self.crusher_shrinking  = True

        def update(self, dt, fighters=None, arena_bounds=None):
            if self.active_event:
                self.event_timer -= dt
                self._update_active(dt, fighters, arena_bounds)
                if self.event_timer <= 0:
                    self._end_event(fighters, arena_bounds)
            else:
                self.interval_timer -= dt
                if self.interval_timer <= 0:
                    self._trigger_event(fighters)
                    self.interval_timer = CHAOS_INTERVAL

        def _trigger_event(self, fighters):
            pool = [e for e in self.EVENTS if e != self.last_event]
            self.active_event = random.choice(pool)
            self.last_event   = self.active_event
            duration = BLACKOUT_DURATION if self.active_event == "BLACKOUT" \
                       else CHAOS_DURATION
            self.event_timer = duration

            if self.active_event == "HYPER SPEED" and fighters:
                for f in fighters:
                    f.speed_multiplier = 2.5

            elif self.active_event == "THE CRUSHER":
                self.crusher_arena_mult = 1.0
                self.crusher_shrinking  = True

            elif self.active_event == "BLACKOUT" and fighters:
                for f in fighters:
                    f.render_color       = BLACK
                    f.render_color_bright = BLACK
                    f.health_bar_color   = f.color  # keep HP bar visible

        def _update_active(self, dt, fighters, arena_bounds):
            if self.active_event == "THE CRUSHER" and arena_bounds:
                if self.crusher_shrinking:
                    self.crusher_arena_mult = max(
                        0.5, self.crusher_arena_mult - dt * 0.15
                    )
                    if self.crusher_arena_mult <= 0.5:
                        self.crusher_shrinking = False
                # Push fighters inside shrunk walls
                if fighters:
                    ax, ay, aw, ah = self.get_crusher_bounds(arena_bounds)
                    for f in fighters:
                        r = f.current_radius
                        if f.x - r < ax: f.x = ax + r
                        if f.x + r > ax + aw: f.x = ax + aw - r
                        if f.y - r < ay: f.y = ay + r
                        if f.y + r > ay + ah: f.y = ay + ah - r

        def _end_event(self, fighters, arena_bounds):
            if self.active_event == "HYPER SPEED" and fighters:
                for f in fighters:
                    f.speed_multiplier = 1.0

            elif self.active_event == "THE CRUSHER":
                self.crusher_arena_mult = 1.0
                self.crusher_shrinking  = True

            elif self.active_event == "BLACKOUT" and fighters:
                for f in fighters:
                    f.render_color        = f.color
                    f.render_color_bright = f.color_bright
                    f.health_bar_color    = f.color

            self.active_event = None

        def get_crusher_bounds(self, base_bounds):
            """Return shrunk arena bounds during THE CRUSHER."""
            ax, ay, aw, ah = base_bounds
            cx = ax + aw / 2
            cy = ay + ah / 2
            new_w = aw * self.crusher_arena_mult
            new_h = ah * self.crusher_arena_mult
            return (cx - new_w/2, cy - new_h/2, new_w, new_h)

        def get_effective_bounds(self, base_bounds):
            """Use this everywhere instead of raw arena bounds."""
            if self.active_event == "THE CRUSHER":
                return self.get_crusher_bounds(base_bounds)
            return base_bounds

        def get_knockback_mult(self):
            return 4.0 if self.active_event == "ULTRA KNOCKBACK" else 1.0

        def get_damage_mult(self):
            return 1.0  # reserved for future events

        def is_ultra_knockback(self):
            return self.active_event == "ULTRA KNOCKBACK"

        def is_blackout(self):
            return self.active_event == "BLACKOUT"

        def get_active_label(self):
            return self.active_event or ""

        def get_interval_remaining(self):
            """Seconds until next event (for countdown display)."""
            if self.active_event:
                return self.event_timer
            return self.interval_timer

        def reset(self):
            self.active_event       = None
            self.last_event         = None
            self.event_timer        = 0.0
            self.interval_timer     = CHAOS_INTERVAL
            self.crusher_arena_mult = 1.0
            self.crusher_shrinking  = True





================================= PROMPT 9 =================================
The chaos manager now exists at src/chaos_manager.py.
Wire it into the game loop and renderer.

Step 1 — Import and instantiate in main.py:
    from chaos_manager import ChaosManager
    self.chaos = ChaosManager()

Step 2 — In the main game update loop, pass dt in seconds:
    dt = 1.0 / FPS   # or use your clock.tick() value
    self.chaos.update(dt,
                      fighters=[self.blue, self.red],
                      arena_bounds=self.arena_bounds)

Step 3 — The chaos-aware bounds replacement happens ONLY in main.py
where arena_bounds is passed INTO fighter.update().
Change the call from:
    fighter.update(opponent, self.arena_bounds, ...)
To:
    fighter.update(opponent,
                   self.chaos.get_effective_bounds(self.arena_bounds), ...)
Do NOT modify fighter.py itself — it receives bounds as a parameter.

Step 4 — Wire knockback multiplier into hit logic in main.py:
    knockback *= self.chaos.get_knockback_mult()
    if self.chaos.is_ultra_knockback():
        self.screen_shake = max(self.screen_shake,
                                SCREEN_SHAKE_INTENSITY * 3)

Step 5 — Blackout screen overlay in the draw loop.
Draw this AFTER all fighters and particles, BEFORE the HUD:
    if self.chaos.is_blackout():
        grey_surf = pygame.Surface(
            (SCREEN_WIDTH, SCREEN_HEIGHT), pygame.SRCALPHA)
        grey_surf.fill((20, 20, 20, 210))
        screen.blit(grey_surf, (0, 0))
        # Health bars are exempt — drawn after this in the HUD

Step 6 — In ui_renderer.py, add to imports at the top:
    from chaos_manager import CHAOS_DURATION, CHAOS_INTERVAL

Add to the renderer's __init__:
    self.event_label_anim_timer = 0
    self.last_chaos_event = None

In the HUD draw method, add the following. Use game.arena_bounds
to get the arena top edge — do NOT use self.arena_bounds:

    # Detect new event trigger to start slam-in animation
    current_event = self.chaos.get_active_label()
    if current_event and current_event != self.last_chaos_event:
        self.event_label_anim_timer = 8
    self.last_chaos_event = current_event

    # Draw event label with slam-in scale
    if current_event:
        font = pygame.font.SysFont(None, 64, bold=True)
        text = font.render(current_event, True, (255, 255, 255))
        if self.event_label_anim_timer > 0:
            scale = 2.0 - (8 - self.event_label_anim_timer) * 0.125
            self.event_label_anim_timer -= 1
        else:
            scale = 1.0
        scaled = pygame.transform.scale(text,
            (int(text.get_width() * scale),
             int(text.get_height() * scale)))
        screen.blit(scaled, scaled.get_rect(
            centerx=SCREEN_WIDTH // 2, top=8))

    # Countdown bar — derive arena top edge from game.arena_bounds
    # If arena_bounds is not on the game object, fall back to:
    # ay = ARENA_MARGIN (from config)
    try:
        _, ay, _, _ = game.arena_bounds
    except AttributeError:
        from config import ARENA_MARGIN
        ay = ARENA_MARGIN

    remaining = self.chaos.get_interval_remaining()
    total     = CHAOS_DURATION if self.chaos.active_event else CHAOS_INTERVAL
    pct       = max(0.0, min(1.0, remaining / total))
    bar_w, bar_h = 160, 4
    bar_x = SCREEN_WIDTH // 2 - bar_w // 2
    bar_y = ay - 10
    pygame.draw.rect(screen, (60, 60, 60), (bar_x, bar_y, bar_w, bar_h))
    fill_color = (255, 80, 80) if self.chaos.active_event else (180, 180, 180)
    pygame.draw.rect(screen, fill_color,
                     (bar_x, bar_y, int(bar_w * pct), bar_h))

Step 7 — On match reset, call:
    self.chaos.reset()
    for f in [self.blue, self.red]:
        f.render_color        = f.color
        f.render_color_bright = f.color_bright
        f.health_bar_color    = f.color
        f.speed_multiplier    = 1.0





================================= PROMPT GAP-A =================================
In sound_manager.py, add the following procedurally generated 
sounds. Use the same numpy/pygame.sndarray approach already in 
the file for all existing sounds.

Add these methods to SoundManager:

    def _gen_parry_clang(self):
        # Metallic clang: high-freq sine + immediate decay
        duration = 0.30
        t = np.linspace(0, duration, int(self.sample_rate * duration))
        wave = (
            np.sin(2 * np.pi * 880 * t) * np.exp(-18 * t) +
            np.sin(2 * np.pi * 1320 * t) * np.exp(-22 * t)
        ) * 0.6
        return self._make_sound(wave)

    def _gen_pierce_hit(self):
        # Whoosh + thud: low sine burst under a short noise crack
        duration = 0.22
        t = np.linspace(0, duration, int(self.sample_rate * duration))
        thud = np.sin(2 * np.pi * 60 * t) * np.exp(-20 * t) * 0.9
        crack = (np.random.uniform(-1, 1, len(t)) *
                 np.exp(-40 * t)) * 0.4
        return self._make_sound(thud + crack)

    def _gen_chaos_sweep(self):
        # Rising synth sweep for HYPER SPEED
        duration = 0.40
        t = np.linspace(0, duration, int(self.sample_rate * duration))
        freq = 300 + 800 * (t / duration)
        wave = np.sin(2 * np.pi * freq * t) * np.exp(-3 * t) * 0.5
        return self._make_sound(wave)

    def _gen_ultra_thud(self):
        # Sub-bass + crack for ULTRA KNOCKBACK landing
        duration = 0.20
        t = np.linspace(0, duration, int(self.sample_rate * duration))
        bass = np.sin(2 * np.pi * 55 * t) * np.exp(-15 * t) * 1.0
        crack = (np.random.uniform(-1, 1, len(t)) *
                 np.exp(-50 * t)) * 0.5
        return self._make_sound(bass + crack)

    def _gen_blackout_static(self):
        # Short static burst then silence for BLACKOUT
        duration = 0.15
        t = np.linspace(0, duration, int(self.sample_rate * duration))
        wave = (np.random.uniform(-1, 1, len(t)) *
                np.exp(-30 * t)) * 0.7
        return self._make_sound(wave)

    def _gen_crusher_grind(self):
        # Low grinding tone, played once on trigger (not looped)
        duration = 0.60
        t = np.linspace(0, duration, int(self.sample_rate * duration))
        wave = (
            np.sin(2 * np.pi * 80 * t) +
            0.4 * np.sin(2 * np.pi * 160 * t)
        ) * np.exp(-4 * t) * 0.55
        return self._make_sound(wave)

In SoundManager.__init__, generate and store all six:
    self.snd_parry_clang   = self._gen_parry_clang()
    self.snd_pierce_hit    = self._gen_pierce_hit()
    self.snd_chaos_sweep   = self._gen_chaos_sweep()
    self.snd_ultra_thud    = self._gen_ultra_thud()
    self.snd_blackout      = self._gen_blackout_static()
    self.snd_crusher_grind = self._gen_crusher_grind()

Add convenience play methods:
    def play_parry(self):       self.snd_parry_clang.play()
    def play_pierce_hit(self):  self.snd_pierce_hit.play()
    def play_chaos_sweep(self): self.snd_chaos_sweep.play()
    def play_ultra_thud(self):  self.snd_ultra_thud.play()
    def play_blackout(self):    self.snd_blackout.play()
    def play_crusher(self):     self.snd_crusher_grind.play()

Wire into existing call sites:

In effects.py, trigger_parry_sequence():
    sound_manager.play_parry()

In combat_manager.py, on a confirmed pierce hit landing:
    sound_manager.play_pierce_hit()

In chaos_manager.py _trigger_event():
    if self.active_event == "HYPER SPEED":
        sound_manager.play_chaos_sweep()
    elif self.active_event == "ULTRA KNOCKBACK":
        pass  # sound fires on hit, not on trigger
    elif self.active_event == "THE CRUSHER":
        sound_manager.play_crusher()
    elif self.active_event == "BLACKOUT":
        sound_manager.play_blackout()

In combat_manager.py, on any hit during ULTRA KNOCKBACK active:
    if chaos.is_ultra_knockback():
        sound_manager.play_ultra_thud()
    else:
        sound_manager.play_hit()   # existing hit sound

Do NOT add a sound_manager import to chaos_manager.py directly —
pass sound_manager in as a parameter to _trigger_event() or 
handle all sound calls from combat_manager.py and effects.py
where sound_manager is already accessible.





================================= GAP-D =================================
Create a new file src/moment_detector.py.

This class watches game state each frame and scores the match.
At match end, the score determines whether the recording is 
worth uploading.

Full class:

    class MomentDetector:

        # Minimum score to flag a match as worth uploading
        UPLOAD_THRESHOLD = 40

        def __init__(self):
            self.score = 0
            self.moments = []   # human-readable log for debugging
            self._last_blue_hp = None
            self._last_red_hp  = None

        def update(self, game, chaos):
            """Call once per frame during battle phase only."""
            blue = game.blue
            red  = game.red

            # Initialise HP tracking on first frame
            if self._last_blue_hp is None:
                self._last_blue_hp = blue.health
                self._last_red_hp  = red.health
                return

            blue_pct = blue.health / blue.max_health
            red_pct  = red.health  / red.max_health
            either_low = blue_pct < 0.10 or red_pct < 0.10

            # --- Condition checks (called once per qualifying event) ---
            # These are checked against state deltas, not every frame.
            # Store and compare last-frame values to detect transitions.

            self._last_blue_hp = blue.health
            self._last_red_hp  = red.health

        def on_pierce_hit(self, attacker, defender, chaos):
            """Call from combat_manager on every confirmed pierce."""
            defender_pct = defender.health / defender.max_health

            base = 10

            # Compound multipliers — stack, don't replace
            if defender_pct < 0.10:
                base += 25   # near-death pierce = near-comeback kill
                self._log("NEAR-DEATH PIERCE", base)
            elif defender_pct < 0.25:
                base += 10
                self._log("LOW-HP PIERCE", base)
            else:
                self._log("PIERCE", base)

            if chaos.is_blackout():
                base += 15   # pierce through the darkness
                self._log("+ BLACKOUT BONUS", 15)

            if chaos.is_ultra_knockback():
                base += 8
                self._log("+ ULTRA KNOCKBACK BONUS", 8)

            self.score += base

        def on_parry(self, blue, red, chaos):
            """Call from combat_manager on every sword-vs-sword parry."""
            blue_pct = blue.health / blue.max_health
            red_pct  = red.health  / red.max_health
            either_low = blue_pct < 0.10 or red_pct < 0.10

            base = 8

            if either_low:
                base += 20   # parry when one fighter is nearly dead
                self._log("CLUTCH PARRY (low HP)", base)
            else:
                self._log("PARRY", base)

            if chaos.is_blackout():
                base += 12   # both invisible, swords still clash
                self._log("+ BLACKOUT PARRY BONUS", 12)

            if chaos.active_event == "THE CRUSHER":
                base += 6    # tight space makes parry harder to dodge
                self._log("+ CRUSHER PARRY BONUS", 6)

            self.score += base

        def on_chaos_event(self, event_name, blue, red):
            """Call from chaos_manager._trigger_event()."""
            blue_pct = blue.health / blue.max_health
            red_pct  = red.health  / red.max_health
            either_low = blue_pct < 0.10 or red_pct < 0.10

            # Chaos during a low-HP finish is cinematic
            if either_low:
                if event_name == "THE CRUSHER":
                    self.score += 18
                    self._log("CRUSHER DURING LOW HP", 18)
                elif event_name == "BLACKOUT":
                    self.score += 20
                    self._log("BLACKOUT DURING LOW HP", 20)
                elif event_name == "ULTRA KNOCKBACK":
                    self.score += 12
                    self._log("ULTRA KB DURING LOW HP", 12)
            else:
                # Still worth something — events are always good
                self.score += 3

        def on_match_end(self, winner, loser):
            """Call once when health reaches zero."""
            loser_pct = loser.health / loser.max_health  # should be ~0

            # Close match: winner survived under 20%
            winner_pct = winner.health / winner.max_health
            if winner_pct < 0.20:
                self.score += 30
                self._log("CLOSE MATCH (winner < 20% HP)", 30)
            elif winner_pct < 0.35:
                self.score += 12
                self._log("CLOSE-ISH MATCH (winner < 35% HP)", 12)

        def should_upload(self):
            return self.score >= self.UPLOAD_THRESHOLD

        def get_summary(self):
            return {
                "score": self.score,
                "upload": self.should_upload(),
                "moments": self.moments
            }

        def _log(self, label, points):
            self.moments.append(f"+{points:>3}  {label}")

        def reset(self):
            self.score = 0
            self.moments = []
            self._last_blue_hp = None
            self._last_red_hp  = None


Wire into the rest of the codebase:

In main.py, import and instantiate:
    from moment_detector import MomentDetector
    self.moment_detector = MomentDetector()

In the battle phase update loop, call every frame:
    self.moment_detector.update(self, self.chaos)

In combat_manager.py, on confirmed pierce land:
    moment_detector.on_pierce_hit(attacker, defender, chaos)

In combat_manager.py, on sword-vs-sword parry:
    moment_detector.on_parry(game.blue, game.red, chaos)

In chaos_manager.py, at the end of _trigger_event():
    if moment_detector and fighters:
        moment_detector.on_chaos_event(
            self.active_event, fighters[0], fighters[1])
    # Pass moment_detector in as an optional parameter:
    # def _trigger_event(self, fighters, moment_detector=None)

In main.py, in the match-end logic before OBS stop:
    self.moment_detector.on_match_end(winner, loser)
    summary = self.moment_detector.get_summary()
    print(f"[MOMENT SCORE] {summary['score']} — upload: {summary['upload']}")
    for line in summary['moments']:
        print(f"  {line}")

In record.py, replace the unconditional OBS stop-and-save with:
    if game.moment_detector.should_upload():
        obs.stop_recording()     # saves the file
        upload_to_youtube(...)   # your existing upload logic
    else:
        obs.stop_recording()
        os.remove(latest_recording_path)   # discard silently
        print("[SKIP] Match scored below threshold — discarded.")

    game.moment_detector.reset()

On match reset in main.py:
    self.moment_detector.reset()




================================= PROMPT 10 =================================
Make the match loop seamlessly for TikTok autoplay.

In the game over / end screen logic:
    end_screen_timer = 90   # 1.5 seconds at 60fps

    Each frame on end screen:
        end_screen_timer -= 1
        if end_screen_timer <= 0:
            reset_match()
            chaos_manager.reset()    # reset chaos timer and active event
            game.phase = 'countdown'
            countdown_value = 3

Title card must stay fully visible until the instant of the cut.
No fade. The abruptness is intentional — it makes viewers rewatch.



