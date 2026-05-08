"""
Visual effects and particle systems for the AlgoRot battle simulation.

This module provides high-performance visual feedback systems, including 
standard particles, expanding shockwaves, arena pulses, and floating 
damage numbers. Effects are designed for maximum "juice" with minimal 
performance overhead.
"""

import pygame
import math
import random

from config import WHITE, YELLOW, PURPLE, GOLD, DAMAGE_NUMBER_LIFETIME, DAMAGE_NUMBER_SPEED


class Particle:
    """A single visual entity with physical properties.

    Particles use basic Newtonian physics (velocity, gravity, drag) and a 
    finite lifecycle to create transient visual artifacts like sparks or dust.
    """
    
    def __init__(self, x: float, y: float, color: tuple, velocity: tuple = None, size: float = 4, lifetime: int = 25):
        """Initializes a particle.

        Args:
            x, y: Starting world coordinates.
            color: RGB tuple.
            velocity: (vx, vy) tuple. If None, a random radial burst is generated.
            size: Starting radius in pixels.
            lifetime: Duration in frames before the particle is destroyed.
        """
        self.x = x
        self.y = y
        self.color = color
        if velocity:
            self.vx, self.vy = velocity
        else:
            angle = random.uniform(0, 2 * math.pi)
            speed = random.uniform(3, 8)
            self.vx = math.cos(angle) * speed
            self.vy = math.sin(angle) * speed
        self.size = size
        self.lifetime = lifetime
        self.max_lifetime = lifetime
    
    def update(self) -> bool:
        """Updates physics and reduces lifetime.

        Returns:
            bool: True if the particle is still alive, False if it should be culled.
        """
        self.x += self.vx
        self.y += self.vy
        self.vy += 0.2  # Gravity simulation
        self.vx *= 0.98 # Horizontal air resistance
        self.lifetime -= 1
        self.size = max(1, self.size * 0.95) # Gradually shrink
        return self.lifetime > 0
    
    def draw(self, surface: pygame.Surface, offset=(0, 0)):
        """Renders the particle to the surface."""
        if self.lifetime <= 0:
            return
        ox, oy = offset
        pygame.draw.circle(surface, self.color, 
                          (int(self.x + ox), int(self.y + oy)), 
                          int(self.size))


class ParticleSystem:
    """Manager for pools of particles.

    Handles creation, updating, and batch rendering of particles.
    """
    
    def __init__(self):
        """Initializes an empty particle system."""
        self.particles = []
    
    def emit(self, x, y, color, count=8, size=4, lifetime=25):
        """Spawns a standard cluster of particles."""
        for _ in range(count):
            self.particles.append(Particle(x, y, color, size=size, lifetime=lifetime))
    
    def emit_explosion(self, x, y, color, count=30):
        """Spawns a high-velocity radial burst, typically for critical hits."""
        for _ in range(count):
            angle = random.uniform(0, 2 * math.pi)
            speed = random.uniform(5, 15)
            velocity = (math.cos(angle) * speed, math.sin(angle) * speed)
            size = random.uniform(3, 8)
            self.particles.append(Particle(x, y, color, velocity=velocity, size=size, lifetime=40))
    
    def update(self):
        """Updates all active particles and removes dead ones."""
        self.particles = [p for p in self.particles if p.update()]
    
    def draw(self, surface, offset=(0, 0)):
        """Renders all active particles."""
        for p in self.particles:
            p.draw(surface, offset)
    
    def clear(self):
        """Removes all particles from the system."""
        self.particles.clear()

    def emit_parry(self, x, y, color, count=20):
        """Spawns a directional upward fan of sparks.

        Visually distinct from explosions, this effect reads as a 'clash' or 
        deflection rather than a direct impact. Particles move faster and 
        vanish quicker to simulate high-energy friction.
        """
        for _ in range(count):
            # Fan arc: straight up ± ~50 degrees
            angle = random.uniform(-math.pi / 2 - 0.87, -math.pi / 2 + 0.87)
            speed = random.uniform(6, 14)
            velocity = (math.cos(angle) * speed, math.sin(angle) * speed)
            size = random.uniform(2, 5)
            self.particles.append(
                Particle(x, y, color, velocity=velocity, size=size, lifetime=20)
            )


class Shockwave:
    """An expanding ring effect that fades over time.

    Typically used to signal high-impact events like round starts or 
    arena pulses.
    """
    
    def __init__(self, x, y, color, max_radius=150):
        """Initializes the shockwave."""
        self.x = x
        self.y = y
        self.color = color
        self.radius = 10
        self.max_radius = max_radius
        self.lifetime = 15
        self.max_lifetime = 15
    
    def update(self):
        """Expands the radius and reduces thickness/alpha."""
        self.lifetime -= 1
        progress = 1 - (self.lifetime / self.max_lifetime)
        self.radius = 10 + (self.max_radius - 10) * progress
        return self.lifetime > 0
    
    def draw(self, surface, offset=(0, 0)):
        """Renders the expanding ring."""
        if self.lifetime <= 0:
            return
        ox, oy = offset
        thickness = max(2, int(4 * (self.lifetime / self.max_lifetime)))
        pygame.draw.circle(surface, self.color, 
                          (int(self.x + ox), int(self.y + oy)), 
                          int(self.radius), thickness)


class ShockwaveSystem:
    """Manager for active shockwave effects."""
    
    def __init__(self):
        self.shockwaves = []
    
    def add(self, x, y, color, max_radius=150):
        self.shockwaves.append(Shockwave(x, y, color, max_radius))
    
    def update(self):
        self.shockwaves = [s for s in self.shockwaves if s.update()]
    
    def draw(self, surface, offset=(0, 0)):
        for s in self.shockwaves:
            s.draw(surface, offset)
    
    def clear(self):
        self.shockwaves.clear()


class ArenaPulse:
    """Visual wave that collapses from the arena borders toward the center.

    Used as an 'anti-staleness' mechanic to visually signal an impending 
    physics boost when fighters are inactive.
    """
    
    def __init__(self, arena_bounds, color=PURPLE):
        self.ax, self.ay, self.aw, self.ah = arena_bounds
        self.color = color
        self.progress = 0.0  # 0 = at borders, 1 = at center
        self.lifetime = 30
        self.max_lifetime = 30
    
    def update(self):
        """Progresses the pulse toward the center."""
        self.lifetime -= 1
        self.progress = 1 - (self.lifetime / self.max_lifetime)
        return self.lifetime > 0
    
    def draw(self, surface, offset=(0, 0)):
        """Renders the collapsing pulse rectangle with a neon glow."""
        if self.lifetime <= 0:
            return
        
        ox, oy = offset
        alpha = self.lifetime / self.max_lifetime
        
        # Calculate shrinking rectangle representing the pulse wave
        shrink = self.progress * min(self.aw, self.ah) / 2 * 0.8
        pulse_rect = pygame.Rect(
            int(self.ax + shrink + ox),
            int(self.ay + shrink + oy),
            int(self.aw - shrink * 2),
            int(self.ah - shrink * 2)
        )
        
        # Draw pulsing ring
        thickness = max(3, int(8 * alpha))
        r, g, b = self.color
        fade_color = (int(r * alpha), int(g * alpha), int(b * alpha))
        pygame.draw.rect(surface, fade_color, pulse_rect, thickness)
        
        # Inner glow line for 'juice'
        if thickness > 2:
            inner_rect = pulse_rect.inflate(-4, -4)
            glow_color = (min(255, int(r * alpha * 1.5)), 
                         min(255, int(g * alpha * 1.5)), 
                         min(255, int(b * alpha * 1.5)))
            pygame.draw.rect(surface, glow_color, inner_rect, 2)


class ArenaPulseSystem:
    """Manages active arena pulse animations."""
    
    def __init__(self):
        self.pulses = []
    
    def add(self, arena_bounds, color=PURPLE):
        self.pulses.append(ArenaPulse(arena_bounds, color))
    
    def update(self):
        self.pulses = [p for p in self.pulses if p.update()]
    
    def draw(self, surface, offset=(0, 0)):
        for p in self.pulses:
            p.draw(surface, offset)
    
    def clear(self):
        self.pulses.clear()


_OUTLINE_OFFSETS = [
    (-2,  0), ( 2,  0), ( 0, -2), ( 0,  2),
    (-2, -2), ( 2, -2), (-2,  2), ( 2,  2),
]


class DamageNumber:
    """A floating, scaling text element that displays damage dealt.

    Crit numbers are rendered with a white fill and fighter-colored outline 
    to ensure legibility against any background while still communicating 
    attacker identity.
    """
    
    def __init__(self, x: float, y: float, damage: float, color: tuple, is_crit: bool = False):
        self.x = x
        self.y = y
        self.damage = int(damage)
        self.is_crit = is_crit
        # Crits use white fill + colored outline; normal hits use colored fill.
        self.color = WHITE if is_crit else color
        self.outline_color = color if is_crit else None
        self.base_scale = 1.5 if is_crit else 1.0
        self.lifetime = DAMAGE_NUMBER_LIFETIME
        self.max_lifetime = DAMAGE_NUMBER_LIFETIME
        self.scale = self.base_scale
        self.vy = -DAMAGE_NUMBER_SPEED
    
    def update(self) -> bool:
        """Handles the 'pop' animation and upward drift."""
        self.y += self.vy
        self.vy *= 0.95
        self.lifetime -= 1
        
        # Pop animation: scale up rapidly then settle down
        progress = 1 - (self.lifetime / self.max_lifetime)
        if progress < 0.2:
            self.scale = self.base_scale + progress * 2
        else:
            self.scale = (self.base_scale + 0.4) - (progress - 0.2) * 0.5
        
        return self.lifetime > 0
    
    def draw(self, surface: pygame.Surface, offset: tuple, font: pygame.font.Font):
        """Renders the damage number with optional outline and scaling."""
        if self.lifetime <= 0:
            return
        
        ox, oy = offset
        alpha = min(255, int(255 * (self.lifetime / self.max_lifetime) * 1.5))
        text = str(self.damage)
        cx = int(self.x + ox)
        cy = int(self.y + oy)

        def _make_surf(color):
            """Internal helper to render and scale the text surface."""
            surf = font.render(text, True, color)
            if self.scale != 1.0:
                w = int(surf.get_width() * self.scale)
                h = int(surf.get_height() * self.scale)
                if w > 0 and h > 0:
                    surf = pygame.transform.scale(surf, (w, h))
            surf.set_alpha(alpha)
            return surf

        # Draw the outline for critical hits using multiple offset stamps
        if self.outline_color is not None:
            outline_surf = _make_surf(self.outline_color)
            for dx, dy in _OUTLINE_OFFSETS:
                rect = outline_surf.get_rect(center=(cx + dx, cy + dy))
                surface.blit(outline_surf, rect)

        fill_surf = _make_surf(self.color)
        surface.blit(fill_surf, fill_surf.get_rect(center=(cx, cy)))


class DamageNumberSystem:
    """Central manager for floating damage text and hit bursts."""
    
    def __init__(self):
        self.numbers = []
        self.font = None
        self._crit_particles = ParticleSystem()
    
    def init_font(self):
        """Lazy-loads the font to prevent errors during early initialization."""
        if self.font is None:
            try:
                self.font = pygame.font.SysFont("Impact", 28, bold=True)
            except:
                self.font = pygame.font.Font(None, 32)
    
    def spawn(self, x, y, damage, color, is_crit=False):
        """Spawns a damage number and optional critical particle burst."""
        x += random.uniform(-10, 10)
        y += random.uniform(-5, 5)
        self.numbers.append(DamageNumber(x, y, damage, color, is_crit))

        if is_crit:
            # Multi-layered crit burst: dense core + scattered sparks
            self._crit_particles.emit_explosion(x, y, color, count=25)
            bright = tuple(min(255, int(c * 1.4)) for c in color)
            for _ in range(8):
                angle = random.uniform(0, 2 * math.pi)
                speed = random.uniform(2, 6)
                vel = (math.cos(angle) * speed, math.sin(angle) * speed)
                self._crit_particles.particles.append(
                    Particle(x, y, bright, velocity=vel, size=random.uniform(5, 10), lifetime=35)
                )
    
    def update(self):
        self.numbers = [n for n in self.numbers if n.update()]
        self._crit_particles.update()
    
    def draw(self, surface, offset=(0, 0)):
        """Renders all visual feedback elements."""
        self.init_font()
        # Draw particles behind text for clarity
        self._crit_particles.draw(surface, offset)
        for n in self.numbers:
            n.draw(surface, offset, self.font)
    
    def clear(self):
        self.numbers.clear()
        self._crit_particles.clear()
s.clear()