# ==============================================================================
# Sound Generator - Procedural sound synthesis for impacts
# ==============================================================================

import numpy as np
from scipy.io import wavfile
import io
import os
import config


class SoundGenerator:
    """
    Generates procedural impact sounds using numpy synthesis.
    Creates punchy, satisfying sounds based on impact intensity.
    """
    
    def __init__(self):
        self.sample_rate = config.SAMPLE_RATE
        self.sound_events = []  # (time, sound_data) for mixing
    
    def generate_impact_sound(self, intensity, is_critical=False):
        """
        Generate an impact sound based on intensity.
        
        Args:
            intensity: Impact intensity (0-1)
            is_critical: Whether this is a critical hit
            
        Returns:
            numpy array: Audio samples
        """
        intensity = max(0.1, min(1.0, intensity))
        duration = 0.08 + intensity * 0.12  # 80-200ms
        
        if is_critical:
            duration *= 1.3
        
        t = np.linspace(0, duration, int(self.sample_rate * duration))
        
        # Base frequency varies with intensity (heavier = lower)
        base_freq = 180 - intensity * 100  # 80-180 Hz
        
        # Generate multiple harmonics for rich sound
        sound = np.zeros_like(t)
        
        # Fundamental (bassy thump)
        sound += np.sin(2 * np.pi * base_freq * t) * 0.6
        
        # First harmonic
        sound += np.sin(2 * np.pi * base_freq * 2 * t) * 0.3
        
        # High frequency click (attack)
        click_freq = 1500 + intensity * 2000
        click_env = np.exp(-t * 80)  # Fast decay
        sound += np.sin(2 * np.pi * click_freq * t) * click_env * 0.4
        
        # Add noise burst for texture
        noise = np.random.randn(len(t)) * 0.15
        noise_env = np.exp(-t * 40)
        sound += noise * noise_env
        
        # Apply envelope (quick attack, medium decay)
        attack = 0.005  # 5ms attack
        decay = duration - attack
        
        envelope = np.ones_like(t)
        attack_samples = int(attack * self.sample_rate)
        envelope[:attack_samples] = np.linspace(0, 1, attack_samples)
        envelope[attack_samples:] = np.exp(-np.linspace(0, 5, len(t) - attack_samples))
        
        sound *= envelope
        
        # Critical hit: add pitch sweep and extra punch
        if is_critical:
            sweep = np.sin(2 * np.pi * (base_freq * 1.5) * t * (1 - t/duration * 0.3))
            sound += sweep * envelope * 0.3
        
        # Normalize and apply volume
        sound = sound / np.max(np.abs(sound)) * config.SOUND_VOLUME * intensity
        
        return sound.astype(np.float32)
    
    def generate_death_sound(self, intensity=1.0):
        """
        Generate a crunchy death/elimination sound.
        
        Args:
            intensity: Death effect intensity
            
        Returns:
            numpy array: Audio samples
        """
        duration = 0.25
        t = np.linspace(0, duration, int(self.sample_rate * duration))
        
        sound = np.zeros_like(t)
        
        # Low frequency boom
        boom_freq = 60
        boom_env = np.exp(-t * 8)
        sound += np.sin(2 * np.pi * boom_freq * t) * boom_env * 0.7
        
        # Crunch noise
        noise = np.random.randn(len(t))
        crunch_env = np.exp(-t * 15)
        
        # Filter noise for crunchiness
        from scipy import signal
        b, a = signal.butter(4, [200, 3000], btype='band', fs=self.sample_rate)
        filtered_noise = signal.filtfilt(b, a, noise)
        sound += filtered_noise * crunch_env * 0.4
        
        # Pop transient
        pop_t = t[:int(0.02 * self.sample_rate)]
        pop = np.sin(2 * np.pi * 400 * pop_t) * np.exp(-pop_t * 200)
        sound[:len(pop)] += pop * 0.5
        
        # Glass shatter texture
        shatter = np.zeros_like(t)
        for _ in range(5):
            freq = np.random.uniform(2000, 6000)
            phase = np.random.uniform(0, 2 * np.pi)
            delay = int(np.random.uniform(0, 0.05) * self.sample_rate)
            shatter_env = np.exp(-t * np.random.uniform(20, 40))
            shatter_wave = np.sin(2 * np.pi * freq * t + phase) * shatter_env * 0.1
            if delay < len(shatter):
                shatter[delay:] += shatter_wave[:-delay] if delay > 0 else shatter_wave
        sound += shatter
        
        # Normalize
        sound = sound / np.max(np.abs(sound)) * config.SOUND_VOLUME * intensity
        
        return sound.astype(np.float32)
    
    def generate_soft_click(self):
        """Generate a soft click for light touches."""
        duration = 0.03
        t = np.linspace(0, duration, int(self.sample_rate * duration))
        
        # High frequency click
        freq = 2500
        envelope = np.exp(-t * 150)
        sound = np.sin(2 * np.pi * freq * t) * envelope * 0.3
        
        return sound.astype(np.float32)
    
    def add_sound_event(self, time, sound_data):
        """
        Add a sound event to be mixed into the final audio.
        
        Args:
            time: Time in seconds when sound starts
            sound_data: numpy array of audio samples
        """
        self.sound_events.append((time, sound_data))
    
    def mix_audio(self, total_duration):
        """
        Mix all sound events into a single audio track.
        
        Args:
            total_duration: Total duration in seconds
            
        Returns:
            numpy array: Mixed stereo audio
        """
        total_samples = int(total_duration * self.sample_rate)
        mixed = np.zeros(total_samples, dtype=np.float32)
        
        for time, sound_data in self.sound_events:
            start_sample = int(time * self.sample_rate)
            end_sample = start_sample + len(sound_data)
            
            if start_sample >= total_samples:
                continue
            
            if end_sample > total_samples:
                sound_data = sound_data[:total_samples - start_sample]
                end_sample = total_samples
            
            mixed[start_sample:end_sample] += sound_data
        
        # Normalize to prevent clipping
        max_val = np.max(np.abs(mixed))
        if max_val > 1.0:
            mixed = mixed / max_val * 0.95
        
        # Convert to stereo
        stereo = np.column_stack([mixed, mixed])
        
        return stereo
    
    def save_audio(self, filepath, total_duration):
        """
        Save mixed audio to a WAV file.
        
        Args:
            filepath: Output file path
            total_duration: Total duration in seconds
        """
        audio = self.mix_audio(total_duration)
        # Convert to 16-bit PCM
        audio_16bit = (audio * 32767).astype(np.int16)
        wavfile.write(filepath, self.sample_rate, audio_16bit)
    
    def clear(self):
        """Clear all sound events."""
        self.sound_events = []
