"""
Audio management system for the AlgoRot battle simulation.

This module provides the SoundManager class, which handles all sound
loading and playback. Audio assets are pre-loaded into memory to avoid
stutters during high-intensity combat clashes.

Sound Bank Layout
-----------------
assets/audios/
├── combat/
│   ├── death_final_hit.mp3      — kill blow (shared)
│   └── guard_break.mp3          — guard break shatter
├── weapons/<weapon>/            — per-weapon hit/clash variants
│   ├── hit_1.mp3
│   ├── hit_2.mp3
│   ├── sweet_spot.mp3
│   └── clash.mp3
├── countdown/
│   ├── countdown_beep.mp3
│   └── sword-fight.mp3
├── ending/
│   ├── victory_fireworks.mp3
│   └── sword_to_the_ground.mp3
└── feedback/
    └── arena_pulse.mp3
"""

import pygame
import os

# Canonical weapon identifiers (must match WEAPON_CONFIGS keys in config.py)
WEAPON_NAMES = ("sword", "dagger", "spear", "axe", "hammer")


class SoundManager:
    """Central controller for game audio.

    The SoundManager pre-caches frequently used sound effects (hits, clashing,
    explosions) to ensure that disk I/O latency does not interfere with the
    60 FPS physics loop.

    Per-weapon audio banks are stored as dicts keyed by weapon name so that
    each archetype can have its own sonic signature without code duplication.
    """

    def __init__(self):
        """Initializes the Pygame mixer and pre-loads all audio assets."""
        # Initialize the mixer once to avoid memory leaks or initialization overhead
        pygame.mixer.init()

        self.muted = False
        self.master_volume = 1.0

        base_path = os.path.join(
            os.path.dirname(os.path.dirname(os.path.dirname(__file__))),
            "assets", "audios"
        )

        def load(subfolder: str, filename: str, volume: float = 0.5):
            """Internal helper: load a sound file and set its base volume.

            Args:
                subfolder: Directory under assets/audios/.
                filename:  Name of the audio file.
                volume:    Initial volume level [0.0 – 1.0].

            Returns:
                A Pygame Sound object, or None if the file is missing.
            """
            path = os.path.join(base_path, subfolder, filename)
            if os.path.exists(path):
                snd = pygame.mixer.Sound(path)
                snd.set_volume(volume)
                return snd
            return None

        # ------------------------------------------------------------------
        # Per-weapon sound banks
        # Each weapon gets its own hit_1, hit_2, sweet_spot, and clash sound.
        # An alternating index per weapon prevents audio fatigue on rapid hits.
        # ------------------------------------------------------------------
        self._weapon_hit_banks: dict[str, list] = {}
        self._weapon_hit_index: dict[str, int] = {}
        self._weapon_sweet_spot: dict[str, object] = {}
        self._weapon_clash: dict[str, object] = {}

        for wpn in WEAPON_NAMES:
            folder = os.path.join("weapons", wpn)
            h1 = load(folder, "hit_1.mp3", 0.55)
            h2 = load(folder, "hit_2.mp3", 0.55)
            self._weapon_hit_banks[wpn] = [h1, h2]
            self._weapon_hit_index[wpn] = 0
            self._weapon_sweet_spot[wpn] = load(folder, "sweet_spot.mp3", 0.65)
            self._weapon_clash[wpn] = load(folder, "clash.mp3", 0.55)

        # ------------------------------------------------------------------
        # Shared combat sounds
        # ------------------------------------------------------------------
        self.death_final_hit_sound  = load("combat", "death_final_hit.mp3",  0.70)
        self.guard_break_sound      = load("combat", "guard_break.mp3",       0.70)

        # ------------------------------------------------------------------
        # Countdown / cinematic sounds
        # ------------------------------------------------------------------
        self.countdown_beep_sound = load("countdown", "countdown_beep.mp3", 0.60)
        self.sword_fight_sound    = load("countdown", "sword-fight.mp3",     0.50)

        # ------------------------------------------------------------------
        # Ending sounds  (sword_to_the_ground now lives in ending/)
        # ------------------------------------------------------------------
        self.sword_to_ground_sound    = load("ending", "sword_to_the_ground.mp3", 0.60)
        self.victory_fireworks_sound  = load("ending", "victory_fireworks.mp3",   0.60)

        # ------------------------------------------------------------------
        # Feedback / ambient sounds
        # ------------------------------------------------------------------
        self.arena_pulse_sound = load("feedback", "arena_pulse.mp3", 0.50)

    # ------------------------------------------------------------------
    # Per-weapon playback helpers
    # ------------------------------------------------------------------

    def _resolve_weapon(self, weapon: str) -> str:
        """Return the weapon key, falling back to 'sword' if unknown."""
        return weapon if weapon in WEAPON_NAMES else "sword"


    def play_weapon_hit(self, weapon: str):
        """Play a normal hit sound for the given weapon, alternating variants.

        Args:
            weapon: Weapon archetype key (e.g. 'sword', 'hammer').
        """
        if self.muted:
            return
        wpn = self._resolve_weapon(weapon)
        bank = self._weapon_hit_banks[wpn]
        idx  = self._weapon_hit_index[wpn]
        if bank[0] or bank[1]:
            snd = bank[idx % len(bank)]
            if snd:
                snd.play()
        self._weapon_hit_index[wpn] = (idx + 1) % 2


    def play_weapon_sweet_spot(self, weapon: str):
        """Play the sweet-spot (critical zone) hit sound for the given weapon.

        Args:
            weapon: Weapon archetype key.
        """
        if self.muted:
            return
        wpn = self._resolve_weapon(weapon)
        snd = self._weapon_sweet_spot.get(wpn)
        if snd:
            snd.play()


    def play_weapon_clash(self, weapon: str):
        """Play the parry/clash sound tuned for the given weapon's material.

        When two weapons meet, the attacker's clash sound is used; callers
        should pass the attacker's weapon so heavier weapons sound heavier.

        Args:
            weapon: Weapon archetype key.
        """
        if self.muted:
            return
        wpn = self._resolve_weapon(weapon)
        snd = self._weapon_clash.get(wpn)
        if snd:
            snd.play()

    # ------------------------------------------------------------------
    # Shared combat sound helpers
    # ------------------------------------------------------------------

    def play_guard_break(self):
        """Plays the guard-break shatter sound."""
        if not self.muted and self.guard_break_sound:
            self.guard_break_sound.play()



    def play_death_final_hit(self):
        """Plays the cinematic final blow sound."""
        if not self.muted and self.death_final_hit_sound:
            self.death_final_hit_sound.play()

    # ------------------------------------------------------------------
    # Countdown / cinematic helpers
    # ------------------------------------------------------------------

    def play_countdown_beep(self):
        """Plays a standard countdown beep (3, 2, 1)."""
        if not self.muted and self.countdown_beep_sound:
            self.countdown_beep_sound.play()

    def play_sword_fight(self):
        """Plays the 'FIGHT' announcer clash sound."""
        if not self.muted and self.sword_fight_sound:
            self.sword_fight_sound.play()

    # ------------------------------------------------------------------
    # Ending helpers
    # ------------------------------------------------------------------

    def play_sword_to_ground(self):
        """Plays the sound of a weapon dropping to the floor after death."""
        if not self.muted and self.sword_to_ground_sound:
            self.sword_to_ground_sound.play()


    def play_victory_fireworks(self):
        """Plays the celebratory fireworks sequence sound."""
        if not self.muted and self.victory_fireworks_sound:
            self.victory_fireworks_sound.play()

    # ------------------------------------------------------------------
    # Feedback helpers
    # ------------------------------------------------------------------

    def play_arena_pulse(self):
        """Plays the arena pulse feedback sound."""
        if not self.muted and self.arena_pulse_sound:
            self.arena_pulse_sound.play()

    # ------------------------------------------------------------------
    # Legacy shim — kept so any remaining call sites don't error out.
    # New code should call play_weapon_hit / play_weapon_sweet_spot instead.
    # ------------------------------------------------------------------

    def play_hit(self):
        """Legacy: plays the sword hit sound (alternating variants)."""
        self.play_weapon_hit("sword")

    def play_crit(self):
        """Legacy: plays the sword sweet-spot sound."""
        self.play_weapon_sweet_spot("sword")

    def play_clash(self):
        """Legacy: plays the sword clash sound."""
        self.play_weapon_clash("sword")

    # ------------------------------------------------------------------
    # Global volume control
    # ------------------------------------------------------------------

    def toggle_mute(self):
        """Toggles the global mute state."""
        self.muted = not self.muted

    def set_master_volume(self, level: float):
        """Adjusts the volume of all pre-loaded sounds proportionally.

        Args:
            level: Target volume multiplier [0.0 – 1.0].
        """
        self.master_volume = max(0.0, min(1.0, level))
        v = self.master_volume

        # Per-weapon banks
        for wpn in WEAPON_NAMES:
            for snd in self._weapon_hit_banks[wpn]:
                if snd: snd.set_volume(0.55 * v)
            ss = self._weapon_sweet_spot.get(wpn)
            if ss: ss.set_volume(0.65 * v)
            cl = self._weapon_clash.get(wpn)
            if cl: cl.set_volume(0.55 * v)

        # Shared combat
        if self.death_final_hit_sound:  self.death_final_hit_sound.set_volume(0.70 * v)
        if self.guard_break_sound:      self.guard_break_sound.set_volume(0.70 * v)

        # Countdown
        if self.countdown_beep_sound:   self.countdown_beep_sound.set_volume(0.60 * v)
        if self.sword_fight_sound:      self.sword_fight_sound.set_volume(0.50 * v)

        # Ending
        if self.sword_to_ground_sound:   self.sword_to_ground_sound.set_volume(0.60 * v)
        if self.victory_fireworks_sound: self.victory_fireworks_sound.set_volume(0.60 * v)

        # Feedback
        if self.arena_pulse_sound: self.arena_pulse_sound.set_volume(0.50 * v)
