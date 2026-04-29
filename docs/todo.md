todos:

=======================================================


implement the video titles update.


=======================================================

not needed for now:

5. what to do after: better sounds.

Based on the current weapon configurations (Sword, Dagger, Spear, Axe, Hammer) and the existing audio files, you currently only have generic combat sounds (`hit_1`, `hit_2`, `critical_hit`, `sword_clash`). 

To make the combat feel much more visceral and unique, you should add **weapon-specific sound effects** that highlight their distinct mechanics and weights. Here are the types of sound effects you should add next:

### 1. Weapon-Specific Impact Sounds
Right now, every weapon shares the same hit sounds. You should add distinct impact sounds for each weapon to emphasize their damage types:
*   **Dagger (Fast, low reach):** Sharp, quick **"slice"** or **"shing"** sounds.
*   **Spear (Long reach, tip sweet-spot):** A piercing, visceral **"stab"** or **"puncture"** sound when hitting the sweet spot. 
*   **Axe (High knockback/damage):** A heavy, resonant **"chop"** or **"cleave"** sound.
*   **Hammer (Heavy, guaranteed sweet-spot):** A deep, booming **"thud"** or **"crush"** with a bit of bass.

### 2. Weapon-Specific Swing / "Whoosh" Sounds
Adding swing sounds based on the weapon's `spin_speed_mult` and weight will make the arena feel much more alive:
*   **Dagger (1.2x spin speed):** Quick, high-pitched, rapid **"swish"** sounds.
*   **Hammer / Axe (0.7x / 0.55x spin speed):** Low-pitched, heavy **"wub"** or thick air-displacement sounds to make them feel massive.

### 3. Mechanic-Specific Audio Cues
Your weapons have unique behaviors that are currently missing audio feedback:
*   **Hammer Spin Reversal:** The hammer's core identity is that it reverses the defender's spin on hit. Add a distinct **"whiplash"** or heavy **"clang/daze"** sound effect when this triggers.
*   **Dagger Guard Crush (Parry Drain):** The dagger has a 1.75x parry drain multiplier. You should add a **"guard break"** or **"shattering glass"** sound for when a fighter's parry is completely drained.
*   **Momentum Stacks:** You have a momentum system with up to 3 stacks. Add a subtle **power-up hum or chime** that pitches up each time a fighter gains a momentum stack (maybe a fast ascending tone).

### 4. Differentiated Clash Sounds
Instead of a single `sword_clash.mp3`, you could implement light vs. heavy clashes. 
*   **Dagger vs Sword:** A light, sharp **"tink"**.
*   **Hammer vs Axe:** A massive, reverberating **"gong"** or heavy **"clang"** that matches the high hit-stop frames of those weapons.

**Recommendation on what to tackle first:** 
I highly recommend starting with the **Weapon-Specific Impact Sounds** (especially the heavy Thud for the Hammer and the Chop for the Axe). Since you already have `HIT_SLOWMO_FRAMES` and `HIT_STOP_FRAMES` scaling for heavy hits, pairing those screen pauses with heavy, booming sound effects will instantly make the combat feel 10x more impactful!





=======================================================
=======================================================
=======================================================

Note to self: Doubtful, as too much can be boring now, but i do like the concept of blackout.


Do if applicable only. Focus on tasks above.

Last-minute chaos_manager.py notes before you wire it in:
1. BLACKOUT will need sword color coverage
Right now it sets render_color and render_color_bright to black — but your fighter_renderer.py almost certainly draws the sword using the fighter's color too. Before you add weapons, make sure blackout also blacks out the sword body/tip. Otherwise you'll have invisible fighters with a glowing sword giving them away.
2. get_knockback_mult() and Axe's 2x knockback need a decision
The Axe has its own 2x knockback multiplier and ULTRA KNOCKBACK returns 4.0x. When both are active simultaneously, decide now: multiplicative (8x total, absolutely chaotic) or capped (one wins). Multiplicative is funnier for the content format, but you need to be intentional. Currently combat_manager.py is probably just applying the chaos multiplier — you'll want to chain it with the weapon's value.
3. get_damage_mult() is a stub — keep it that way
It returns 1.0 hardcoded. Weapon damage multipliers (Spear tip = 2x, Axe sweet-spot-everywhere, etc.) should live on the weapon stats, not here. This is the right architecture — chaos_manager controls chaos-specific modifiers, weapons control weapon-specific modifiers, and combat_manager multiplies them together.
4. THE CRUSHER + Spear is broken by design (keep it)
The Crusher shrinks the arena; the Spear has ~85px reach vs. the default 55px sword. In a half-size arena the Spear can hit across nearly the whole space. This is a chaotic, content-worthy interaction — don't "fix" it.
5. HYPER SPEED won't conflict with Dagger's fast spin
As long as speed_multiplier only touches movement velocity and spin speed is a separate property, they're independent. Just make sure when you add spin_speed to Fighter, it's not accidentally driven by speed_multiplier.

========================================================

Create a new file src/chaos_manager.py with the following code exactly:

    import random
    import pygame
    from config import (
        FPS, SCREEN_WIDTH, SCREEN_HEIGHT,
        WHITE, BLACK
    )

    CHAOS_DURATION    = 4.0
    CHAOS_INTERVAL    = 3.0
    BLACKOUT_DURATION = 3.0

    class ChaosManager:
        EVENTS = [
            "HYPER SPEED",
            "ULTRA KNOCKBACK",
            "THE CRUSHER",
            "BLACKOUT",
        ]

        def __init__(self):
            self.active_event       = None
            self.last_event         = None
            self.event_timer        = 0.0
            self.interval_timer     = CHAOS_INTERVAL
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
                    f.render_color        = BLACK
                    f.render_color_bright = BLACK
                    f.health_bar_color    = f.color

        def _update_active(self, dt, fighters, arena_bounds):
            if self.active_event == "THE CRUSHER" and arena_bounds:
                if self.crusher_shrinking:
                    self.crusher_arena_mult = max(
                        0.5, self.crusher_arena_mult - dt * 0.15
                    )
                    if self.crusher_arena_mult <= 0.5:
                        self.crusher_shrinking = False
                if fighters:
                    ax, ay, aw, ah = self.get_crusher_bounds(arena_bounds)
                    for f in fighters:
                        r = f.radius
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
            ax, ay, aw, ah = base_bounds
            cx = ax + aw / 2
            cy = ay + ah / 2
            new_w = aw * self.crusher_arena_mult
            new_h = ah * self.crusher_arena_mult
            return (cx - new_w/2, cy - new_h/2, new_w, new_h)

        def get_effective_bounds(self, base_bounds):
            if self.active_event == "THE CRUSHER":
                return self.get_crusher_bounds(base_bounds)
            return base_bounds

        def get_knockback_mult(self):
            return 4.0 if self.active_event == "ULTRA KNOCKBACK" else 1.0

        def get_damage_mult(self):
            return 1.0

        def is_ultra_knockback(self):
            return self.active_event == "ULTRA KNOCKBACK"

        def is_blackout(self):
            return self.active_event == "BLACKOUT"

        def get_active_label(self):
            return self.active_event or ""

        def get_interval_remaining(self):
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

========================================================

Wire the existing src/chaos_manager.py into the game. Make all of the
following changes exactly.

─────────────────────────────────────────
STEP 1 — src/entities/fighter.py
─────────────────────────────────────────
In Fighter.__init__, after the line:
    self.color_bright = color_bright
Add:
    self.render_color        = color
    self.render_color_bright = color_bright
    self.health_bar_color    = color

In Fighter.__init__, after the line:
    self.spin_speed = 0.25
Add:
    self.speed_multiplier = 1.0

In Fighter.update(), find the velocity clamp block:
    max_vel = MAX_VELOCITY
    if speed > max_vel:
        ...
    min_vel = MIN_VELOCITY
    if speed < min_vel and speed > 0:
        ...
Replace those two variable assignments with:
    max_vel = MAX_VELOCITY * self.speed_multiplier
    ...
    min_vel = MIN_VELOCITY * self.speed_multiplier

In Fighter.reset(), after the line:
    self.spin_speed = 0.25
Add:
    self.speed_multiplier    = 1.0
    self.render_color        = self.color
    self.render_color_bright = self.color_bright
    self.health_bar_color    = self.color

─────────────────────────────────────────
STEP 2 — src/renderers/fighter_renderer.py
─────────────────────────────────────────
In FighterRenderer.render(), find:
    body_color = WHITE if fighter.flash_timer > 0 else fighter.color
Replace with:
    body_color = WHITE if fighter.flash_timer > 0 else fighter.render_color

In FighterRenderer._draw_sword(), find the dark border color calculation:
    dark_border_color = (int(fighter.color[0] * 0.4), ...)
Replace with:
    dark_border_color = (int(fighter.render_color[0] * 0.4),
                         int(fighter.render_color[1] * 0.4),
                         int(fighter.render_color[2] * 0.4))

In _draw_sword(), find the core blade line:
    pygame.draw.line(surface, fighter.color, ...)
Replace with:
    pygame.draw.line(surface, fighter.render_color, ...)

─────────────────────────────────────────
STEP 3 — src/managers/combat_manager.py
─────────────────────────────────────────
In handle_collisions(), in the body hit section, find:
    knockback = BASE_KNOCKBACK * crit_mult * (1.0 + (total_damage_mult - 1.0) * 0.5) * 1.5
Immediately after that line add:
    if hasattr(game, 'chaos'):
        knockback *= game.chaos.get_knockback_mult()
        if game.chaos.is_ultra_knockback():
            game.screen_shake = max(game.screen_shake, SCREEN_SHAKE_INTENSITY * 3)

─────────────────────────────────────────
STEP 4 — src/main.py
─────────────────────────────────────────
At the top of main.py, add to the existing imports:
    from chaos_manager import ChaosManager

In Game.__init__, after the line:
    self.combat_manager = CombatManager()
Add:
    self.chaos = ChaosManager()

In Game.update(), find:
    effective_arena = tuple(self.arena_bounds)
Replace with:
    effective_arena = self.chaos.get_effective_bounds(tuple(self.arena_bounds))

In Game.update(), find the chaos update location — add this line just BEFORE
the two fighter.update() calls:
    self.chaos.update(1.0 / FPS,
                      fighters=[self.blue, self.red],
                      arena_bounds=tuple(self.arena_bounds))

In Game._reset_round(), after the line:
    self.inactivity_timer = 0
Add:
    self.chaos.reset()

In Game.draw(), find the comment:
    # UI Overlays
    self.ui_renderer.draw(self)
BEFORE that line, insert the blackout overlay block:
    if self.chaos.is_blackout():
        grey_surf = pygame.Surface(
            (SCREEN_WIDTH, SCREEN_HEIGHT), pygame.SRCALPHA)
        grey_surf.fill((20, 20, 20, 210))
        self.screen.blit(grey_surf, (0, 0))

─────────────────────────────────────────
STEP 5 — src/renderers/ui_renderer.py
─────────────────────────────────────────
Add to imports at the top:
    from chaos_manager import CHAOS_DURATION, CHAOS_INTERVAL

In UIRenderer.__init__, add:
    self.event_label_anim_timer = 0
    self.last_chaos_event       = None

In UIRenderer.draw() (or whatever the main HUD draw method is called),
at the END of the method before the final return, add:

    # ── Chaos event label ──────────────────────────────────────────
    current_event = game.chaos.get_active_label()
    if current_event and current_event != self.last_chaos_event:
        self.event_label_anim_timer = 8
    self.last_chaos_event = current_event

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

    # ── Chaos countdown bar ────────────────────────────────────────
    ax, ay, aw, ah = game.arena_bounds
    remaining = game.chaos.get_interval_remaining()
    total     = CHAOS_DURATION if game.chaos.active_event else CHAOS_INTERVAL
    pct       = max(0.0, min(1.0, remaining / total))
    bar_w, bar_h = 160, 4
    bar_x = SCREEN_WIDTH // 2 - bar_w // 2
    bar_y = int(ay) - 10
    pygame.draw.rect(screen, (60, 60, 60), (bar_x, bar_y, bar_w, bar_h))
    fill_color = (255, 80, 80) if game.chaos.active_event else (180, 180, 180)
    pygame.draw.rect(screen, fill_color,
                     (bar_x, bar_y, int(bar_w * pct), bar_h))

========================================================
