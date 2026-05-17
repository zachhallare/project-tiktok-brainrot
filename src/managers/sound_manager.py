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

Weapon Pitch Modifiers
----------------------
Light weapons (dagger)  pitch UP   ~5%  (ratio 1.05)
Heavy weapons (hammer)  pitch DOWN ~8%  (ratio 0.92)
Mid-weight (sword, axe, spear) stay at baseline (ratio 1.0)

Pitch shifting is applied at load time via numpy resampling so there is
zero per-frame CPU cost during playback.
"""

import pygame
import os
import numpy as np

# Canonical weapon identifiers (must match WEAPON_CONFIGS keys in config.py)
WEAPON_NAMES = ("sword", "dagger", "spear", "axe", "hammer")

# Pitch multipliers per weapon archetype.
# Values > 1.0 raise pitch; values < 1.0 lower pitch.
# A ratio of R means the resampled array is R× shorter/longer,
# which pygame plays back at the mixer's native sample rate — yielding
# an effective pitch shift of R semitones-worth.
WEAPON_PITCH_MODIFIERS: dict[str, float] = {
    "dagger": 1.05,   # light — pitch up ~5 %
    "sword":  1.00,   # mid   — baseline
    "axe":    1.00,   # mid   — baseline
    "spear":  1.00,   # mid   — baseline
    "hammer": 0.92,   # heavy — pitch down ~8 %
}


def _compute_rms(snd) -> float:
    """Return the RMS amplitude of a pygame Sound object."""
    try:
        samples = pygame.sndarray.array(snd).astype(np.float32)
        rms = float(np.sqrt(np.mean(samples ** 2)))
        return rms if rms > 0 else 1.0
    except Exception:
        return 1.0


def _pitch_shift_sound(snd, ratio: float) -> pygame.mixer.Sound:
    """Return a new pygame Sound pitched by *ratio* via numpy resampling.

    A ratio of 1.05 raises pitch ~5 %; 0.92 lowers it ~8 %.  The sample
    array is interpolated to 1/ratio of its original length and then
    wrapped back into a Sound object.  The original Sound is unchanged.

    Args:
        snd:   Source pygame Sound object.
        ratio: Pitch multiplier (>1 = higher, <1 = lower).

    Returns:
        A new pygame Sound object, or the original if ratio ≈ 1.0 or on
        any error.
    """
    if abs(ratio - 1.0) < 1e-4:
        return snd
    try:
        arr = pygame.sndarray.array(snd)          # shape: (frames,) or (frames, channels)
        original_len = arr.shape[0]
        new_len = max(1, int(round(original_len / ratio)))

        if arr.ndim == 1:
            # Mono
            x_old = np.linspace(0, 1, original_len)
            x_new = np.linspace(0, 1, new_len)
            shifted = np.interp(x_new, x_old, arr.astype(np.float32))
            shifted = np.clip(shifted, -32768, 32767).astype(arr.dtype)
        else:
            # Stereo / multi-channel
            channels = arr.shape[1]
            x_old = np.linspace(0, 1, original_len)
            x_new = np.linspace(0, 1, new_len)
            shifted_channels = [
                np.interp(x_new, x_old, arr[:, c].astype(np.float32))
                for c in range(channels)
            ]
            shifted = np.stack(shifted_channels, axis=1)
            shifted = np.clip(shifted, -32768, 32767).astype(arr.dtype)

        new_snd = pygame.sndarray.make_sound(shifted)
        # Preserve volume from the original
        new_snd.set_volume(snd.get_volume())
        return new_snd
    except Exception:
        # Graceful fallback — return the un-pitched original
        return snd


class SoundManager:
    """Central controller for game audio.

    The SoundManager pre-caches frequently used sound effects (hits, clashing,
    explosions) to ensure that disk I/O latency does not interfere with the
    60 FPS physics loop.

    Per-weapon audio banks are stored as dicts keyed by weapon name so that
    each archetype can have its own sonic signature without code duplication.

    Pitch variation is applied at construction time: light weapons (dagger)
    play hit/clash sounds ~5 % higher; heavy weapons (hammer) ~8 % lower.
    Mid-weight weapons (sword, axe, spear) play at baseline pitch.
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

        # Registry: maps each sound to its desired category weight
        _sound_registry: dict = {}

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
                _sound_registry[snd] = volume
                return snd
            return None


        # ------------------------------------------------------------------
        # Per-weapon sound banks
        # Each weapon gets its own hit_1, hit_2, sweet_spot, and clash sound.
        # An alternating index per weapon prevents audio fatigue on rapid hits.
        # Hit and clash sounds are pitch-shifted at load time according to
        # WEAPON_PITCH_MODIFIERS — no runtime cost during playback.
        # ------------------------------------------------------------------
        self._weapon_hit_banks: dict[str, list] = {}
        self._weapon_hit_index: dict[str, int] = {}
        self._weapon_sweet_spot: dict[str, object] = {}
        self._weapon_clash: dict[str, object] = {}

        for wpn in WEAPON_NAMES:
            folder = os.path.join("weapons", wpn)
            pitch = WEAPON_PITCH_MODIFIERS.get(wpn, 1.0)

            h1_raw = load(folder, "hit_1.mp3", 0.55)
            h2_raw = load(folder, "hit_2.mp3", 0.55)

            # Apply pitch shift to hit sounds; register pitched copies so that
            # _normalize_all picks them up instead of the raw originals.
            h1 = _pitch_shift_sound(h1_raw, pitch) if h1_raw else None
            h2 = _pitch_shift_sound(h2_raw, pitch) if h2_raw else None
            if h1 and h1 is not h1_raw:
                _sound_registry[h1] = 0.55
            if h2 and h2 is not h2_raw:
                _sound_registry[h2] = 0.55

            self._weapon_hit_banks[wpn] = [h1, h2]
            self._weapon_hit_index[wpn] = 0

            # sweet_spot (crit) stays at baseline pitch
            self._weapon_sweet_spot[wpn] = load(folder, "sweet_spot.mp3", 0.65)

            # clash (parry) is pitch-shifted to match the weapon's weight feel
            clash_raw = load(folder, "clash.mp3", 0.55)
            clash = _pitch_shift_sound(clash_raw, pitch) if clash_raw else None
            if clash and clash is not clash_raw:
                _sound_registry[clash] = 0.55
            self._weapon_clash[wpn] = clash

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

        self._sound_registry = _sound_registry
        self._normalize_all(self._sound_registry)

    # ------------------------------------------------------------------
    # Per-weapon playback helpers
    # ------------------------------------------------------------------

    def _normalize_all(self, registry: dict):
        if not registry:
            return
        rms_map = {snd: _compute_rms(snd) for snd in registry}
        min_rms = min(rms_map.values())
        for snd, category_weight in registry.items():
            factor = min_rms / rms_map[snd]
            snd.set_volume(max(0.0, min(1.0, factor * category_weight * self.master_volume)))

    def set_master_volume(self, level: float):
        self.master_volume = max(0.0, min(1.0, level))
        self._normalize_all(self._sound_registry)  # re-runs normalization with new level

    def _resolve_weapon(self, weapon: str) -> str:
        """Return the weapon key, falling back to 'sword' if unknown."""
        return weapon if weapon in WEAPON_NAMES else "sword"


    def play_weapon_hit(self, weapon: str):
        """Play a normal hit sound for the given weapon, alternating variants.

        The sound is played at the pre-pitched rate for this weapon archetype
        (dagger ~5 % higher, hammer ~8 % lower, others baseline).

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

        Sweet-spot sounds play at baseline pitch regardless of weapon weight.

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
        The clash sound is pre-pitched to the weapon's archetype modifier
        (dagger ~5 % higher, hammer ~8 % lower, others baseline).

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


