"""
Chaos Manager for TikTok Brainrot events.
Triggers random chaos events every 3-5 seconds to create unpredictable gameplay.
10 chaos events with no-repeat constraint.
"""

import random
import math

from config import (
    FPS, CHAOS_MIN_INTERVAL, CHAOS_MAX_INTERVAL, CHAOS_DURATION,
    NEON_RED, NEON_BLUE, NEON_BG, WHITE, BLACK, SCREEN_WIDTH, SCREEN_HEIGHT
)


class ChaosManager:
    """Manages chaos events that alter gameplay dramatically."""
    
    # All 10 chaos events
    EVENTS = [
        "HYPER SPEED",      # 3.0x physics speed
        "TINY TERROR",      # 0.5x body, 1.0x sword, 1.5x damage
        "DISCO FEVER",      # Rainbow colors, 100% life steal
        "THE CRUSHER",      # Arena shrinks to 50%
        "BLACKOUT",         # White BG, black fighters
        "TRON MODE",        # Solid neon walls, opponent trail = damage
        "GLITCH TRAP",      # Glitch VFX, random teleports
        "BREATHING ROOM",   # Arena pulses 60%-110% sine wave
        "MOVING WALLS",     # Pong-style vertical bar
        "ULTRA KNOCKBACK"   # 5x knockback, massive shake
    ]
    
    def __init__(self):
        self.active_event = None
        self.last_event = None  # Track to prevent repeat
        self.event_timer = 0.0
        self.next_event_time = self._random_interval()
        self.event_duration_remaining = 0.0
        
        # Disco Fever state
        self.disco_hue = 0.0
        self.disco_particle_timer = 0
        
        # Crusher state
        self.crusher_arena_mult = 1.0
        self.crusher_shrinking = True
        self.crusher_fighters_pushed = False
        
        # TRON MODE state
        self.tron_trails = {'blue': [], 'red': []}  # List of (x, y) positions
        self.tron_trail_timer = 0
        
        # GLITCH TRAP state
        self.glitch_teleport_timer = 0.0
        self.glitch_rects = []  # Visual glitch rectangles [(x, y, w, h, color)]
        self.glitch_rect_timer = 0
        
        # BREATHING ROOM state
        self.breathing_phase = 0.0
        
        # MOVING WALLS state
        self.moving_wall_x = SCREEN_WIDTH // 2
        self.moving_wall_dir = 1  # 1 = right, -1 = left
        self.moving_wall_speed = 4
        self.moving_wall_width = 12
    
    def _random_interval(self):
        """Get random time until next chaos event."""
        return random.uniform(CHAOS_MIN_INTERVAL, CHAOS_MAX_INTERVAL)
    
    def update(self, dt, particles=None, fighters=None):
        """Update chaos timer and active event."""
        if self.active_event:
            self.event_duration_remaining -= dt
            
            # Event-specific updates
            if self.active_event == "DISCO FEVER":
                self.disco_hue = (self.disco_hue + 5) % 360
                self.disco_particle_timer += 1
                if particles and fighters and self.disco_particle_timer % 3 == 0:
                    for fighter in fighters:
                        color = self._hue_to_rgb((self.disco_hue + random.randint(0, 60)) % 360)
                        particles.emit(fighter.x, fighter.y, color, count=2, size=3, lifetime=15)
            
            elif self.active_event == "THE CRUSHER":
                if self.crusher_shrinking:
                    self.crusher_arena_mult = max(0.5, self.crusher_arena_mult - dt * 0.3)
                    if self.crusher_arena_mult <= 0.5:
                        self.crusher_shrinking = False
            
            elif self.active_event == "TRON MODE":
                self.tron_trail_timer += 1
                # Record trail positions every few frames
                if fighters and self.tron_trail_timer % 3 == 0:
                    for fighter in fighters:
                        key = 'blue' if fighter.is_blue else 'red'
                        self.tron_trails[key].append((fighter.x, fighter.y))
                        # Limit trail length
                        if len(self.tron_trails[key]) > 100:
                            self.tron_trails[key].pop(0)
            
            elif self.active_event == "GLITCH TRAP":
                self.glitch_teleport_timer += dt
                self.glitch_rect_timer += 1
                # Update glitch rectangles every few frames
                if self.glitch_rect_timer % 5 == 0:
                    self._generate_glitch_rects()
            
            elif self.active_event == "BREATHING ROOM":
                self.breathing_phase += dt * 2 * math.pi  # 1 second full cycle
            
            elif self.active_event == "MOVING WALLS":
                # Move wall back and forth
                self.moving_wall_x += self.moving_wall_speed * self.moving_wall_dir
                arena_margin = 80
                if self.moving_wall_x >= SCREEN_WIDTH - arena_margin:
                    self.moving_wall_x = SCREEN_WIDTH - arena_margin
                    self.moving_wall_dir = -1
                elif self.moving_wall_x <= arena_margin:
                    self.moving_wall_x = arena_margin
                    self.moving_wall_dir = 1
            
            # Check if event ended
            if self.event_duration_remaining <= 0:
                self.reset_chaos()
        else:
            self.event_timer += dt
            if self.event_timer >= self.next_event_time:
                self.trigger_event()
    
    def trigger_event(self):
        """Trigger a random chaos event (no repeats)."""
        available_events = [e for e in self.EVENTS if e != self.last_event]
        self.active_event = random.choice(available_events)
        self.last_event = self.active_event
        self.event_duration_remaining = CHAOS_DURATION
        self.event_timer = 0.0
        
        # Initialize event-specific state
        if self.active_event == "DISCO FEVER":
            self.disco_hue = random.uniform(0, 360)
            self.disco_particle_timer = 0
        
        elif self.active_event == "THE CRUSHER":
            self.crusher_arena_mult = 1.0
            self.crusher_shrinking = True
            self.crusher_fighters_pushed = False
        
        elif self.active_event == "TRON MODE":
            self.tron_trails = {'blue': [], 'red': []}  # Clear old trails
            self.tron_trail_timer = 0
        
        elif self.active_event == "GLITCH TRAP":
            self.glitch_teleport_timer = 0.0
            self.glitch_rects = []
            self.glitch_rect_timer = 0
        
        elif self.active_event == "BREATHING ROOM":
            self.breathing_phase = 0.0
        
        elif self.active_event == "MOVING WALLS":
            self.moving_wall_x = SCREEN_WIDTH // 2
            self.moving_wall_dir = random.choice([1, -1])
        
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
        
        # Reset Tron trails (IMPORTANT: prevents old trails from flashing)
        self.tron_trails = {'blue': [], 'red': []}
        
        # Reset Glitch
        self.glitch_rects = []
        self.glitch_teleport_timer = 0.0
        
        # Reset Breathing
        self.breathing_phase = 0.0
    
    # ==================== GETTERS ====================
    
    def get_speed_mult(self):
        """Get physics/movement speed multiplier."""
        if self.active_event == "HYPER SPEED":
            return 50.0
        return 1.0
    
    def get_body_size_mult(self):
        """Get fighter BODY size multiplier."""
        if self.active_event == "TINY TERROR":
            return 0.5
        return 1.0
    
    def get_sword_size_mult(self):
        """Get SWORD size multiplier (always 1.0)."""
        return 1.0
    
    def get_attack_speed_mult(self):
        """Get attack speed multiplier."""
        if self.active_event == "TINY TERROR":
            return 0.5
        return 1.0
    
    def get_damage_mult(self):
        """Get damage multiplier."""
        if self.active_event == "TINY TERROR":
            return 1.5
        return 1.0
    
    def get_life_steal(self):
        """Get life steal (0.0 to 1.0)."""
        if self.active_event == "DISCO FEVER":
            return 1.0
        return 0.0
    
    def get_knockback_mult(self):
        """Get knockback multiplier."""
        if self.active_event == "ULTRA KNOCKBACK":
            return 30.0
        return 1.0
    
    def get_fighter_color(self, original_color, is_blue=True):
        """Get fighter color (modified for Disco/Blackout/Tron)."""
        if self.active_event == "BLACKOUT":
            return BLACK
        elif self.active_event == "DISCO FEVER":
            offset = 0 if is_blue else 180
            return self._hue_to_rgb((self.disco_hue + offset) % 360)
        elif self.active_event == "TRON MODE":
            # Brighter neon for Tron
            return NEON_BLUE if is_blue else NEON_RED
        return original_color
    
    def get_health_bar_color(self, original_color):
        """Get health bar color."""
        if self.active_event == "BLACKOUT":
            return BLACK
        return original_color
    
    def get_bg_color(self):
        """Get background color."""
        if self.active_event == "BLACKOUT":
            return WHITE
        elif self.active_event == "DISCO FEVER":
            h = (self.disco_hue + 180) % 360
            r, g, b = self._hue_to_rgb(h)
            return (r // 8, g // 8, b // 8)
        elif self.active_event == "TRON MODE":
            return (5, 5, 10)  # Very dark for Tron effect
        return NEON_BG
    
    def get_arena_mult(self):
        """Get arena size multiplier."""
        if self.active_event == "THE CRUSHER":
            return self.crusher_arena_mult
        elif self.active_event == "BREATHING ROOM":
            # Sine wave: oscillates between 0.6 and 1.1
            return 0.85 + 0.25 * math.sin(self.breathing_phase)
        return 1.0
    
    # ==================== EVENT CHECKS ====================
    
    def is_blackout(self):
        return self.active_event == "BLACKOUT"
    
    def is_tron_mode(self):
        return self.active_event == "TRON MODE"
    
    def is_glitch_trap(self):
        return self.active_event == "GLITCH TRAP"
    
    def is_moving_walls(self):
        return self.active_event == "MOVING WALLS"
    
    def is_ultra_knockback(self):
        return self.active_event == "ULTRA KNOCKBACK"
    
    def needs_crusher_safety_push(self):
        """Check if fighters need safety push for Crusher/Breathing."""
        if self.active_event in ["THE CRUSHER", "BREATHING ROOM"]:
            if not self.crusher_fighters_pushed:
                self.crusher_fighters_pushed = True
                return True
        return False
    
    # ==================== TRON MODE ====================
    
    def get_tron_trails(self):
        """Get trail positions for drawing."""
        return self.tron_trails
    
    def check_tron_collision(self, fighter, other_fighter):
        """Check if fighter collides with opponent's trail. Returns damage or 0."""
        if self.active_event != "TRON MODE":
            return 0
        
        other_key = 'blue' if other_fighter.is_blue else 'red'
        trail = self.tron_trails[other_key]
        
        for tx, ty in trail:
            dist = math.hypot(fighter.x - tx, fighter.y - ty)
            if dist < fighter.current_radius + 8:
                return 10  # Trail damage
        return 0
    
    # ==================== GLITCH TRAP ====================
    
    def should_glitch_teleport(self):
        """Check if fighters should teleport (30% chance every 0.5s)."""
        if self.active_event != "GLITCH TRAP":
            return False
        if self.glitch_teleport_timer >= 0.5:
            self.glitch_teleport_timer = 0.0
            return random.random() < 0.3
        return False
    
    def get_glitch_teleport_offset(self):
        """Get random teleport offset (50px in random direction)."""
        angle = random.uniform(0, 2 * math.pi)
        return (math.cos(angle) * 50, math.sin(angle) * 50)
    
    def get_glitch_rects(self):
        """Get glitch rectangles for visual effect."""
        return self.glitch_rects
    
    def _generate_glitch_rects(self):
        """Generate random glitch rectangles."""
        self.glitch_rects = []
        for _ in range(random.randint(3, 8)):
            x = random.randint(0, SCREEN_WIDTH)
            y = random.randint(0, SCREEN_HEIGHT)
            w = random.randint(20, 150)
            h = random.randint(5, 30)
            color = random.choice([NEON_RED, NEON_BLUE, (255, 0, 255), (0, 255, 0)])
            self.glitch_rects.append((x, y, w, h, color))
    
    # ==================== MOVING WALLS ====================
    
    def get_moving_wall(self):
        """Get moving wall position and size (x, width, direction)."""
        return (self.moving_wall_x, self.moving_wall_width, self.moving_wall_dir)
    
    def handle_moving_wall_collision(self, fighter, arena_bounds):
        """Push fighter away from moving wall. Direction matches wall movement."""
        if self.active_event != "MOVING WALLS":
            return
        
        wall_x = self.moving_wall_x
        wall_half = self.moving_wall_width // 2
        
        # Check if fighter overlaps wall
        if abs(fighter.x - wall_x) < fighter.current_radius + wall_half:
            # Push in wall's movement direction (not just away from center)
            push_strength = 8
            fighter.x += self.moving_wall_dir * push_strength
            fighter.vx = self.moving_wall_dir * abs(fighter.vx) * 0.5 + self.moving_wall_dir * 5
    
    # ==================== UTILITY ====================
    
    def get_event_progress(self):
        """Get progress through current event (0.0 to 1.0)."""
        if not self.active_event:
            return 0.0
        return 1.0 - (self.event_duration_remaining / CHAOS_DURATION)
    
    def _hue_to_rgb(self, hue):
        """Convert HSV hue (0-360) to RGB."""
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
