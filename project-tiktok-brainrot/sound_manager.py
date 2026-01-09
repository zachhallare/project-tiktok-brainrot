"""
Sound Manager for skill and arena event audio.
Supports placeholder files (.txt) with graceful fallback to real audio (.wav/.ogg).
"""

import os
import pygame


class SoundManager:
    """Manages game sounds with fallback for missing audio files."""
    
    SOUND_DIR = os.path.join(os.path.dirname(__file__), 'sounds')
    
    # Sound categories with default volumes
    VOLUMES = {
        'skill': 0.6,
        'impact': 0.5,
        'arena': 0.4,
    }
    
    def __init__(self):
        self.sounds = {}
        self.enabled = True
        self._load_sounds()
    
    def _load_sounds(self):
        """Load all available sound files from sounds/ directory."""
        if not os.path.exists(self.SOUND_DIR):
            print(f"Sound directory not found: {self.SOUND_DIR}")
            return
        
        # Map sound IDs to their categories
        self.sound_categories = {
            'dash_slash': 'skill',
            'spin_parry': 'skill',
            'ground_slam': 'skill',
            'phantom_cross': 'skill',
            'blade_cyclone': 'skill',
            'final_flash_draw': 'skill',
            'shield': 'skill',
            'hit_impact': 'impact',
            'explosion': 'impact',
            'arena_pulse': 'arena',
            'arena_shrink': 'arena',
        }
        
        for sound_id in self.sound_categories.keys():
            self._try_load_sound(sound_id)
    
    def _try_load_sound(self, sound_id):
        """Try to load a sound file, checking .wav then .ogg."""
        for ext in ['.wav', '.ogg', '.mp3']:
            filepath = os.path.join(self.SOUND_DIR, f"{sound_id}{ext}")
            if os.path.exists(filepath):
                try:
                    sound = pygame.mixer.Sound(filepath)
                    category = self.sound_categories.get(sound_id, 'skill')
                    sound.set_volume(self.VOLUMES.get(category, 0.5))
                    self.sounds[sound_id] = sound
                    return True
                except Exception as e:
                    print(f"Failed to load sound {filepath}: {e}")
        return False
    
    def play(self, sound_id, volume_override=None):
        """Play a sound by ID. Silently fails if sound not available."""
        if not self.enabled:
            return
        
        sound = self.sounds.get(sound_id)
        if sound:
            if volume_override is not None:
                sound.set_volume(volume_override)
            sound.play()
    
    def play_skill(self, skill_name):
        """Play sound for a skill activation."""
        # Convert skill name to sound ID format
        sound_id = skill_name.lower().replace(' ', '_')
        self.play(sound_id)
    
    def set_enabled(self, enabled):
        """Enable or disable all sounds."""
        self.enabled = enabled
    
    def set_category_volume(self, category, volume):
        """Set volume for all sounds in a category."""
        self.VOLUMES[category] = volume
        for sound_id, sound in self.sounds.items():
            if self.sound_categories.get(sound_id) == category:
                sound.set_volume(volume)


# Global sound manager instance
_sound_manager = None

def get_sound_manager():
    """Get or create the global sound manager."""
    global _sound_manager
    if _sound_manager is None:
        _sound_manager = SoundManager()
    return _sound_manager
