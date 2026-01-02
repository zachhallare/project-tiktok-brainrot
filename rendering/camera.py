# ==============================================================================
# Camera System - Dynamic camera with zoom and smoothing
# ==============================================================================

import math
import config


class Camera:
    """
    Dynamic camera that follows action with smooth interpolation and zoom.
    """
    
    def __init__(self):
        # Position (center of view)
        self.x = config.WIDTH / 2
        self.y = config.HEIGHT / 2
        self.target_x = self.x
        self.target_y = self.y
        
        # Zoom
        self.zoom = 1.0
        self.target_zoom = 1.0
        
        # Bounds
        self.bounds_padding = 100
    
    def follow(self, center, spread):
        """
        Set camera target based on action center and spread.
        
        Args:
            center: (x, y) center of action
            spread: Max distance from center to furthest ball
        """
        self.target_x = center[0]
        self.target_y = center[1]
        
        # Calculate zoom based on spread
        # More spread = zoom out, less spread = zoom in
        ideal_zoom = min(
            config.WIDTH / (spread * 2.5 + self.bounds_padding),
            config.HEIGHT / (spread * 2.5 + self.bounds_padding)
        )
        self.target_zoom = max(config.MIN_ZOOM, min(config.MAX_ZOOM, ideal_zoom))
    
    def update(self, dt):
        """Smoothly interpolate camera to target."""
        # Smooth position
        lerp_factor = 1 - math.pow(1 - config.CAMERA_SMOOTHING, dt * 60)
        self.x += (self.target_x - self.x) * lerp_factor
        self.y += (self.target_y - self.y) * lerp_factor
        
        # Smooth zoom
        zoom_lerp = 1 - math.pow(1 - config.ZOOM_SMOOTHING, dt * 60)
        self.zoom += (self.target_zoom - self.zoom) * zoom_lerp
        
        # Clamp to bounds
        half_w = (config.WIDTH / 2) / self.zoom
        half_h = (config.HEIGHT / 2) / self.zoom
        
        self.x = max(half_w, min(config.WIDTH - half_w, self.x))
        self.y = max(half_h, min(config.HEIGHT - half_h, self.y))
    
    def world_to_screen(self, world_pos, shake_offset=(0, 0)):
        """
        Convert world position to screen position.
        
        Args:
            world_pos: (x, y) in world coordinates
            shake_offset: Screen shake offset to apply
            
        Returns:
            (x, y) in screen coordinates
        """
        # Apply zoom relative to camera center
        screen_x = (world_pos[0] - self.x) * self.zoom + config.WIDTH / 2
        screen_y = (world_pos[1] - self.y) * self.zoom + config.HEIGHT / 2
        
        # Apply shake
        screen_x += shake_offset[0]
        screen_y += shake_offset[1]
        
        return (screen_x, screen_y)
    
    def scale_size(self, size):
        """Scale a size value by current zoom."""
        return size * self.zoom
    
    def get_visible_rect(self):
        """Get the visible world rectangle."""
        half_w = (config.WIDTH / 2) / self.zoom
        half_h = (config.HEIGHT / 2) / self.zoom
        
        return (
            self.x - half_w,
            self.y - half_h,
            half_w * 2,
            half_h * 2
        )
    
    def trigger_zoom_pulse(self, amount=0.1, duration=0.3):
        """Trigger a quick zoom pulse for dramatic effect."""
        # Temporarily increase target zoom
        self.target_zoom = min(config.MAX_ZOOM, self.zoom + amount)
