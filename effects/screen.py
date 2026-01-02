# ==============================================================================
# Screen Effects - Screen shake, flash, and time effects
# ==============================================================================

import random
import math
import config


class ScreenEffects:
    """Manages screen-level visual effects like shake and flash."""
    
    def __init__(self):
        # Screen shake
        self.shake_intensity = 0
        self.shake_offset = (0, 0)
        
        # Screen flash
        self.flash_color = (255, 255, 255)
        self.flash_alpha = 0
        self.flash_decay = 5
        
        # Vignette pulse
        self.vignette_pulse = 0
        
        # Impact intensity accumulator (for dramatic buildup)
        self.impact_accumulator = 0
    
    def trigger_shake(self, intensity=None):
        """
        Trigger screen shake effect.
        
        Args:
            intensity: Shake intensity (default from config)
        """
        intensity = intensity or config.SCREEN_SHAKE_INTENSITY
        self.shake_intensity = max(self.shake_intensity, intensity)
    
    def trigger_flash(self, color=(255, 255, 255), alpha=0.3):
        """
        Trigger screen flash effect.
        
        Args:
            color: Flash color RGB
            alpha: Flash opacity (0-1)
        """
        self.flash_color = color
        self.flash_alpha = max(self.flash_alpha, alpha)
    
    def trigger_impact(self, intensity):
        """
        Register an impact for building up effects.
        
        Args:
            intensity: Impact intensity (0-1)
        """
        self.impact_accumulator = min(1.0, self.impact_accumulator + intensity * 0.2)
        
        # Heavy impacts trigger shake
        if intensity > 0.3:
            self.trigger_shake(intensity * config.SCREEN_SHAKE_INTENSITY)
        
        # Very heavy impacts trigger flash
        if intensity > 0.7:
            self.trigger_flash(alpha=intensity * 0.2)
    
    def trigger_death_flash(self, color):
        """Trigger flash effect for a death event."""
        # Brighten the color for flash
        flash_color = tuple(min(255, c + 100) for c in color)
        self.trigger_flash(flash_color, 0.15)
        self.trigger_shake(config.SCREEN_SHAKE_INTENSITY * 1.5)
        self.vignette_pulse = 1.0
    
    def update(self, dt):
        """Update all screen effects."""
        # Update shake
        if self.shake_intensity > 0.1:
            angle = random.uniform(0, 2 * math.pi)
            self.shake_offset = (
                math.cos(angle) * self.shake_intensity,
                math.sin(angle) * self.shake_intensity
            )
            self.shake_intensity *= config.SCREEN_SHAKE_DECAY
        else:
            self.shake_intensity = 0
            self.shake_offset = (0, 0)
        
        # Update flash
        if self.flash_alpha > 0:
            self.flash_alpha -= dt * self.flash_decay
            self.flash_alpha = max(0, self.flash_alpha)
        
        # Update vignette pulse
        if self.vignette_pulse > 0:
            self.vignette_pulse -= dt * 3
            self.vignette_pulse = max(0, self.vignette_pulse)
        
        # Decay impact accumulator
        self.impact_accumulator *= 0.95
    
    def get_shake_offset(self):
        """Get current shake offset for rendering."""
        return self.shake_offset
    
    def get_flash(self):
        """Get current flash color and alpha."""
        return self.flash_color, self.flash_alpha
    
    def get_vignette_intensity(self):
        """Get vignette intensity for dramatic effect."""
        return self.vignette_pulse * 0.3 + self.impact_accumulator * 0.2
