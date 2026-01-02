# ==============================================================================
# Particle System - Visual effects for impacts, sparks, and debris
# ==============================================================================

import random
import math
import config


class Particle:
    """A single particle for visual effects."""
    
    def __init__(self, pos, velocity, color, size, lifetime, particle_type='spark'):
        self.x, self.y = pos
        self.vx, self.vy = velocity
        self.color = color
        self.size = size
        self.max_lifetime = lifetime
        self.lifetime = lifetime
        self.particle_type = particle_type
        self.rotation = random.uniform(0, 360)
        self.rotation_speed = random.uniform(-500, 500)
    
    def update(self, dt):
        """Update particle position and state."""
        # Apply gravity
        self.vy += config.GRAVITY * 0.5 * dt
        
        # Apply movement
        self.x += self.vx * dt
        self.y += self.vy * dt
        
        # Apply drag
        self.vx *= 0.98
        self.vy *= 0.98
        
        # Update rotation
        self.rotation += self.rotation_speed * dt
        
        # Update lifetime
        self.lifetime -= dt
        
        return self.lifetime > 0
    
    @property
    def alpha(self):
        """Get particle opacity based on remaining lifetime."""
        return max(0, min(1, self.lifetime / self.max_lifetime))
    
    @property
    def current_size(self):
        """Get current size based on lifetime."""
        return self.size * self.alpha


class ParticleSystem:
    """Manages all particles in the scene."""
    
    def __init__(self):
        self.particles = []
    
    def emit_sparks(self, pos, color, count=None, intensity=1.0):
        """
        Emit spark particles at a position.
        
        Args:
            pos: (x, y) position
            color: RGB tuple
            count: Number of particles (default from config)
            intensity: Multiplier for speed and count
        """
        count = count or int(config.PARTICLE_COUNT_ON_HIT * intensity)
        
        for _ in range(count):
            angle = random.uniform(0, 2 * math.pi)
            speed = random.uniform(100, 400) * intensity
            velocity = (math.cos(angle) * speed, math.sin(angle) * speed - 100)
            
            # Vary color slightly
            varied_color = tuple(
                max(0, min(255, c + random.randint(-30, 30)))
                for c in color
            )
            
            particle = Particle(
                pos=pos,
                velocity=velocity,
                color=varied_color,
                size=random.uniform(2, 6) * intensity,
                lifetime=random.uniform(0.2, 0.5),
                particle_type='spark'
            )
            self.particles.append(particle)
    
    def emit_explosion(self, pos, color, radius, count=None):
        """
        Emit explosion particles (for death effects).
        
        Args:
            pos: (x, y) position
            color: RGB tuple
            radius: Ball radius for sizing
            count: Number of particles
        """
        count = count or config.PARTICLE_COUNT_ON_DEATH
        
        for _ in range(count):
            angle = random.uniform(0, 2 * math.pi)
            speed = random.uniform(150, 500)
            velocity = (math.cos(angle) * speed, math.sin(angle) * speed - 150)
            
            # Create debris-like particles
            particle = Particle(
                pos=(pos[0] + random.uniform(-radius/2, radius/2),
                     pos[1] + random.uniform(-radius/2, radius/2)),
                velocity=velocity,
                color=color,
                size=random.uniform(4, radius * 0.4),
                lifetime=random.uniform(0.4, 1.0),
                particle_type='debris'
            )
            self.particles.append(particle)
        
        # Add bright flash particles
        for _ in range(count // 3):
            angle = random.uniform(0, 2 * math.pi)
            speed = random.uniform(50, 150)
            
            flash_color = tuple(min(255, c + 100) for c in color)
            
            particle = Particle(
                pos=pos,
                velocity=(math.cos(angle) * speed, math.sin(angle) * speed),
                color=flash_color,
                size=random.uniform(8, 15),
                lifetime=random.uniform(0.1, 0.3),
                particle_type='flash'
            )
            self.particles.append(particle)
    
    def emit_dust(self, pos, count=5):
        """Emit dust/smoke particles."""
        for _ in range(count):
            velocity = (
                random.uniform(-30, 30),
                random.uniform(-80, -20)
            )
            
            gray = random.randint(60, 100)
            
            particle = Particle(
                pos=(pos[0] + random.uniform(-10, 10), pos[1]),
                velocity=velocity,
                color=(gray, gray, gray),
                size=random.uniform(5, 12),
                lifetime=random.uniform(0.3, 0.6),
                particle_type='dust'
            )
            self.particles.append(particle)
    
    def update(self, dt):
        """Update all particles, removing dead ones."""
        self.particles = [p for p in self.particles if p.update(dt)]
    
    def clear(self):
        """Clear all particles."""
        self.particles = []
