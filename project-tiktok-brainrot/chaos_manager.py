"""
Chaos Manager for TikTok Brainrot events.
Triggers random chaos events every 5-8 seconds to create unpredictable gameplay.
"""

import random
import math
import pygame

from config import (
    FPS, CHAOS_MIN_INTERVAL, CHAOS_MAX_INTERVAL, CHAOS_DURATION,
    NEON_RED, NEON_BLUE, NEON_BG, WHITE, BLACK, ORANGE
)


class ChaosManager:
    """Manages chaos events that alter gameplay dramatically."""
    
    # All available chaos events
    EVENTS = [
        "HYPER SPEED",   # 3.0x physics speed (incredibly fast)
        "SPIKE WALLS",   # Walls deal damage + 3x knockback
        "TINY TERROR",   # 0.5x body size, normal sword, slower attacks, 1.5x damage
        "DISCO FEVER",   # Rainbow colors, particles, 100% life steal
        "TUMBLE DRYER",  # VERY strong rotational gravity
        "THE CRUSHER",   # Arena shrinks to 50%
        "BLACKOUT"       # White BG, black fighters + health bars
    ]
    
    def __init__(self):
        self.active_event = None
        self.event_timer = 0.0
        self.next_event_time = self._random_interval()
        self.event_duration_remaining = 0.0
        
        # Disco fever state
        self.disco_hue = 0.0
        self.disco_particle_timer = 0
        
        # Tumble dryer angle
        self.tumble_angle = 0.0
        
        # Crusher state
        self.crusher_arena_mult = 1.0
        self.crusher_shrinking = True
        self.crusher_fighters_pushed = False  # Safety teleport flag
        
        # Spike walls state
        self.spike_wall_flash_timer = 0
        
        # Stored original arena for Crusher
        self.original_arena = None
    
    def _random_interval(self):
        """Get random time until next chaos event."""
        return random.uniform(CHAOS_MIN_INTERVAL, CHAOS_MAX_INTERVAL)
    
    def update(self, dt, particles=None, fighters=None):
        """Update chaos timer and active event."""
        if self.active_event:
            # Event is active, count down
            self.event_duration_remaining -= dt
            
            # Update event-specific logic
            if self.active_event == "DISCO FEVER":
                self.disco_hue = (self.disco_hue + 5) % 360
                self.disco_particle_timer += 1
                # Emit particles from fighters
                if particles and fighters and self.disco_particle_timer % 3 == 0:
                    for fighter in fighters:
                        color = self._hue_to_rgb((self.disco_hue + random.randint(0, 60)) % 360)
                        particles.emit(fighter.x, fighter.y, color, count=2, size=3, lifetime=15)
            
            elif self.active_event == "TUMBLE DRYER":
                self.tumble_angle += 0.15  # Much faster rotation
            
            elif self.active_event == "SPIKE WALLS":
                self.spike_wall_flash_timer += 1
            
            elif self.active_event == "THE CRUSHER":
                if self.crusher_shrinking:
                    self.crusher_arena_mult = max(0.5, self.crusher_arena_mult - dt * 0.3)
                    if self.crusher_arena_mult <= 0.5:
                        self.crusher_shrinking = False
            
            # Check if event ended
            if self.event_duration_remaining <= 0:
                self.reset_chaos()
        else:
            # No event active, count up to next event
            self.event_timer += dt
            
            if self.event_timer >= self.next_event_time:
                self.trigger_event()
    
    def trigger_event(self):
        """Trigger a random chaos event."""
        self.active_event = random.choice(self.EVENTS)
        self.event_duration_remaining = CHAOS_DURATION
        self.event_timer = 0.0
        
        # Reset event-specific state
        if self.active_event == "DISCO FEVER":
            self.disco_hue = random.uniform(0, 360)
            self.disco_particle_timer = 0
        
        elif self.active_event == "TUMBLE DRYER":
            self.tumble_angle = 0.0
        
        elif self.active_event == "THE CRUSHER":
            self.crusher_arena_mult = 1.0
            self.crusher_shrinking = True
            self.crusher_fighters_pushed = False  # Reset safety flag
        
        elif self.active_event == "SPIKE WALLS":
            self.spike_wall_flash_timer = 0
        
        return self.active_event
    
    def reset_chaos(self):
        """Reset all chaos modifiers to default."""
        self.active_event = None
        self.event_duration_remaining = 0.0
        self.next_event_time = self._random_interval()
        
        # Reset Crusher
        self.crusher_arena_mult = 1.0
        self.crusher_shrinking = True
        self.crusher_fighters_pushed = False
    
    def get_speed_mult(self):
        """Get current physics/movement speed multiplier."""
        if self.active_event == "HYPER SPEED":
            return 3.0  # Incredibly fast/uncontrollable
        return 1.0
    
    def get_body_size_mult(self):
        """Get current fighter BODY size multiplier (separate from sword)."""
        if self.active_event == "TINY TERROR":
            return 0.5  # Body shrinks
        return 1.0
    
    def get_sword_size_mult(self):
        """Get current SWORD size multiplier (stays normal for Tiny Terror)."""
        # Sword always stays normal size
        return 1.0
    
    def get_attack_speed_mult(self):
        """Get attack speed multiplier (lower = slower attacks)."""
        if self.active_event == "TINY TERROR":
            return 0.5  # Slower attacks
        return 1.0
    
    def get_damage_mult(self):
        """Get current damage multiplier."""
        if self.active_event == "TINY TERROR":
            return 1.5
        return 1.0
    
    def get_life_steal(self):
        """Get life steal percentage (0.0 to 1.0)."""
        if self.active_event == "DISCO FEVER":
            return 1.0  # 100% life steal (vampirism)
        return 0.0
    
    def get_fighter_color(self, original_color, is_blue=True):
        """Get fighter color (modified for Disco/Blackout)."""
        if self.active_event == "BLACKOUT":
            return BLACK
        elif self.active_event == "DISCO FEVER":
            # Offset hue for blue vs red
            offset = 0 if is_blue else 180
            return self._hue_to_rgb((self.disco_hue + offset) % 360)
        return original_color
    
    def get_health_bar_color(self, original_color):
        """Get health bar color (black during Blackout, otherwise normal)."""
        if self.active_event == "BLACKOUT":
            return BLACK
        return original_color
    
    def get_bg_color(self):
        """Get background color."""
        if self.active_event == "BLACKOUT":
            return WHITE
        elif self.active_event == "DISCO FEVER":
            # Dark shifting background
            h = (self.disco_hue + 180) % 360
            r, g, b = self._hue_to_rgb(h)
            # Keep it dark
            return (r // 8, g // 8, b // 8)
        return NEON_BG
    
    def get_gravity_force(self, fighter_x, fighter_y, center_x, center_y):
        """Get Tumble Dryer rotational gravity force - VERY STRONG."""
        if self.active_event != "TUMBLE DRYER":
            return (0, 0)
        
        # Calculate angle from center to fighter
        dx = fighter_x - center_x
        dy = fighter_y - center_y
        dist = max(1, math.hypot(dx, dy))
        
        # Push perpendicular (clockwise) with VERY STRONG force
        # Force proportional to distance from center
        angle = math.atan2(dy, dx)
        push_angle = angle - math.pi / 2  # Perpendicular clockwise
        
        # MUCH stronger force - overrides normal bouncing
        force_strength = 3.5 + (dist / 100)  # Stronger further from center
        fx = math.cos(push_angle) * force_strength
        fy = math.sin(push_angle) * force_strength
        
        return (fx, fy)
    
    def get_arena_mult(self):
        """Get arena size multiplier (for The Crusher)."""
        if self.active_event == "THE CRUSHER":
            return self.crusher_arena_mult
        return 1.0
    
    def is_spike_walls(self):
        """Check if Spike Walls event is active."""
        return self.active_event == "SPIKE WALLS"
    
    def get_spike_wall_damage(self):
        """Get damage dealt by spike walls on contact."""
        if self.active_event == "SPIKE WALLS":
            return 15
        return 0
    
    def get_spike_wall_knockback_mult(self):
        """Get knockback multiplier for spike walls (pinball effect)."""
        if self.active_event == "SPIKE WALLS":
            return 3.0
        return 1.0
    
    def get_wall_glow_color(self):
        """Get wall glow color for Spike Walls."""
        if self.active_event == "SPIKE WALLS":
            # Pulsing between red and orange
            pulse = (math.sin(self.spike_wall_flash_timer * 0.15) + 1) / 2
            r = int(255 * pulse + 200 * (1 - pulse))
            g = int(100 * pulse + 50 * (1 - pulse))
            b = int(0)
            return (r, g, b)
        return None
    
    def is_blackout(self):
        """Check if Blackout event is active."""
        return self.active_event == "BLACKOUT"
    
    def is_disco(self):
        """Check if Disco Fever is active."""
        return self.active_event == "DISCO FEVER"
    
    def is_crusher(self):
        """Check if The Crusher event is active."""
        return self.active_event == "THE CRUSHER"
    
    def needs_crusher_safety_push(self):
        """Check if fighters need to be pushed inside Crusher arena."""
        if self.active_event == "THE CRUSHER" and not self.crusher_fighters_pushed:
            self.crusher_fighters_pushed = True
            return True
        return False
    
    def get_event_progress(self):
        """Get progress through current event (0.0 to 1.0)."""
        if not self.active_event:
            return 0.0
        return 1.0 - (self.event_duration_remaining / CHAOS_DURATION)
    
    def _hue_to_rgb(self, hue):
        """Convert HSV hue (0-360) to RGB with full saturation and value."""
        h = hue / 60.0
        i = int(h) % 6
        f = h - int(h)
        
        v = 255
        p = 0
        q = int(255 * (1 - f))
        t = int(255 * f)
        
        if i == 0:
            return (v, t, p)
        elif i == 1:
            return (q, v, p)
        elif i == 2:
            return (p, v, t)
        elif i == 3:
            return (p, q, v)
        elif i == 4:
            return (t, p, v)
        else:
            return (v, p, q)
