"""
Audio management system for the AlgoRot battle simulation.

This module provides the SoundManager class, which handles all sound 
loading and playback. Audio assets are pre-loaded into memory to avoid 
stutters during high-intensity combat clashes.
"""

import pygame
import os

class SoundManager:
    """Central controller for game audio.

    The SoundManager pre-caches frequently used sound effects (hits, clashing, 
    explosions) to ensure that Disk I/O latency does not interfere with the 
    60 FPS physics loop.
    """
    
    def __init__(self):
        """Initializes the Pygame mixer and pre-loads all audio assets."""
        # Initialize the mixer once to avoid memory leaks or initialization overhead
        pygame.mixer.init()
        
        self.muted = False
        self.master_volume = 1.0
        
        base_path = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), "assets", "audios")
        
        def load_sound(subfolder: str, filename: str, volume: float = 0.5) -> pygame.mixer.Sound:
            """Internal helper to load a sound file and set its base volume.

            Args:
                subfolder: Directory under assets/audios/.
                filename: Name of the audio file.
                volume: Initial volume level [0.0 - 1.0].

            Returns:
                A Pygame Sound object, or None if the file is missing.
            """
            path = os.path.join(base_path, subfolder, filename)
            if os.path.exists(path):
                sound = pygame.mixer.Sound(path)
                sound.set_volume(volume)
                return sound
            return None
            
        # Preload combat sounds: these are fired frequently and must remain in memory
        self.hit_sounds = [
            load_sound("combat", "hit_1.mp3", 0.5),
            load_sound("combat", "hit_2.mp3", 0.5)
        ]
        self.hit_sound_index = 0
        self.critical_hit_sound = load_sound("combat", "critical_hit.mp3", 0.6)
        self.sword_clash_sound = load_sound("combat", "sword_clash.mp3", 0.5)
        
        # Preload feedback and cinematic sounds
        self.arena_pulse_sound = load_sound("feedback", "arena_pulse.mp3", 0.5)
        self.death_final_hit_sound = load_sound("combat", "death_final_hit.mp3", 0.7)
        self.sword_to_ground_sound = load_sound("combat", "sword_to_the_ground.mp3", 0.6)
        self.countdown_beep_sound = load_sound("countdown", "countdown_beep.mp3", 0.6)
        self.sword_fight_sound = load_sound("countdown", "sword-fight.mp3", 0.5)
        self.victory_fireworks_sound = load_sound("ending", "victory_fireworks.mp3", 0.6)

    def play_arena_pulse(self):
        """Plays the arena pulse feedback sound."""
        if not self.muted and self.arena_pulse_sound:
            self.arena_pulse_sound.play()

    def play_death_final_hit(self):
        """Plays the cinematic final blow sound."""
        if not self.muted and self.death_final_hit_sound:
            self.death_final_hit_sound.play()

    def play_sword_to_ground(self):
        """Plays the sound of a weapon dropping to the floor."""
        if not self.muted and self.sword_to_ground_sound:
            self.sword_to_ground_sound.play()

    def play_countdown_beep(self):
        """Plays a standard countdown beep."""
        if not self.muted and self.countdown_beep_sound:
            self.countdown_beep_sound.play()

    def play_sword_fight(self):
        """Plays the 'FIGHT' announcer/clash sound."""
        if not self.muted and self.sword_fight_sound:
            self.sword_fight_sound.play()

    def play_victory_fireworks(self):
        """Plays the celebratory fireworks sequence sound."""
        if not self.muted and self.victory_fireworks_sound:
            self.victory_fireworks_sound.play()

    def play_clash(self):
        """Plays the metallic sword-on-sword clash sound."""
        if self.muted or not self.sword_clash_sound:
            return
        self.sword_clash_sound.play()

    def play_crit(self):
        """Plays the high-impact critical hit sound."""
        if self.muted or not self.critical_hit_sound:
            return
        self.critical_hit_sound.play()

    def play_hit(self):
        """Plays one of the randomized standard hit sounds to prevent audio fatigue."""
        if self.muted:
            return
        if self.hit_sounds[0] and self.hit_sounds[1]:
            self.hit_sounds[self.hit_sound_index].play()
            self.hit_sound_index = (self.hit_sound_index + 1) % 2

    def toggle_mute(self):
        """Toggles the global mute state."""
        self.muted = not self.muted

    def set_master_volume(self, level: float):
        """Adjusts the volume of all sounds based on a master multiplier.

        Args:
            level: The target volume [0.0 - 1.0].
        """
        self.master_volume = max(0.0, min(1.0, level))
        # Update volumes of the preloaded sounds
        if self.sword_clash_sound: 
            self.sword_clash_sound.set_volume(0.5 * self.master_volume)
        if self.critical_hit_sound: 
            self.critical_hit_sound.set_volume(0.6 * self.master_volume)
        if self.hit_sounds[0]: 
            self.hit_sounds[0].set_volume(0.5 * self.master_volume)
        if self.hit_sounds[1]: 
            self.hit_sounds[1].set_volume(0.5 * self.master_volume)
        if hasattr(self, 'arena_pulse_sound') and self.arena_pulse_sound:
            self.arena_pulse_sound.set_volume(0.5 * self.master_volume)
        if hasattr(self, 'death_final_hit_sound') and self.death_final_hit_sound:
            self.death_final_hit_sound.set_volume(0.7 * self.master_volume)
        if hasattr(self, 'sword_to_ground_sound') and self.sword_to_ground_sound:
            self.sword_to_ground_sound.set_volume(0.6 * self.master_volume)
        if hasattr(self, 'countdown_beep_sound') and self.countdown_beep_sound:
            self.countdown_beep_sound.set_volume(0.6 * self.master_volume)
        if hasattr(self, 'sword_fight_sound') and self.sword_fight_sound:
            self.sword_fight_sound.set_volume(0.5 * self.master_volume)
        if hasattr(self, 'victory_fireworks_sound') and self.victory_fireworks_sound:
            self.victory_fireworks_sound.set_volume(0.6 * self.master_volume)
