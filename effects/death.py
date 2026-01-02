# ==============================================================================
# Death Effects - Specialized death/elimination animations
# ==============================================================================

import math
import random
import config


class DeathFragment:
    """A fragment of a shattered ball."""
    
    def __init__(self, pos, velocity, color, size, arc_points):
        self.x, self.y = pos
        self.vx, self.vy = velocity
        self.color = color
        self.size = size
        self.arc_points = arc_points  # Shape of fragment
        self.rotation = random.uniform(0, 360)
        self.rotation_speed = random.uniform(-800, 800)
        self.lifetime = random.uniform(0.5, 1.0)
        self.max_lifetime = self.lifetime
    
    def update(self, dt):
        """Update fragment physics."""
        self.vy += config.GRAVITY * dt
        self.x += self.vx * dt
        self.y += self.vy * dt
        self.rotation += self.rotation_speed * dt
        self.lifetime -= dt
        return self.lifetime > 0
    
    @property
    def alpha(self):
        return max(0, self.lifetime / self.max_lifetime)


class DeathEffect:
    """Manages death animation for a single ball."""
    
    def __init__(self, pos, velocity, color, radius):
        self.x, self.y = pos
        self.color = color
        self.radius = radius
        self.fragments = []
        self.lifetime = 1.0
        self.max_lifetime = 1.0
        
        # Create shatter fragments
        num_fragments = random.randint(6, 12)
        for i in range(num_fragments):
            angle = (2 * math.pi * i / num_fragments) + random.uniform(-0.3, 0.3)
            speed = random.uniform(100, 350)
            
            frag_velocity = (
                velocity[0] * 0.5 + math.cos(angle) * speed,
                velocity[1] * 0.5 + math.sin(angle) * speed - 100
            )
            
            # Create arc shape for fragment
            arc_start = angle - 0.3
            arc_end = angle + 0.3
            arc_points = [
                (0, 0),  # Center
                (math.cos(arc_start) * radius * 0.8, math.sin(arc_start) * radius * 0.8),
                (math.cos(angle) * radius, math.sin(angle) * radius),
                (math.cos(arc_end) * radius * 0.8, math.sin(arc_end) * radius * 0.8),
            ]
            
            fragment = DeathFragment(
                pos=pos,
                velocity=frag_velocity,
                color=color,
                size=radius * random.uniform(0.2, 0.5),
                arc_points=arc_points
            )
            self.fragments.append(fragment)
        
        # Shockwave effect
        self.shockwave_radius = 0
        self.shockwave_max = radius * 4
        self.shockwave_alpha = 1.0
    
    def update(self, dt):
        """Update death effect."""
        self.lifetime -= dt
        
        # Update fragments
        self.fragments = [f for f in self.fragments if f.update(dt)]
        
        # Update shockwave
        if self.shockwave_radius < self.shockwave_max:
            self.shockwave_radius += 600 * dt
            self.shockwave_alpha = 1 - (self.shockwave_radius / self.shockwave_max)
        
        return self.lifetime > 0 or self.fragments
    
    @property
    def alpha(self):
        return max(0, self.lifetime / self.max_lifetime)


class DeathEffectManager:
    """Manages all active death effects."""
    
    def __init__(self):
        self.effects = []
    
    def create_death_effect(self, pos, velocity, color, radius):
        """Create a new death effect for a destroyed ball."""
        effect = DeathEffect(pos, velocity, color, radius)
        self.effects.append(effect)
        return effect
    
    def update(self, dt):
        """Update all death effects."""
        self.effects = [e for e in self.effects if e.update(dt)]
    
    def clear(self):
        """Clear all effects."""
        self.effects = []
