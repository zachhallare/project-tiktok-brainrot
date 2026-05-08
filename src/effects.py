"""
Simplified particle and visual effects for performance.
Enhanced with skill-specific effects and damage numbers.
"""

import pygame
import math
import random

from config import WHITE, YELLOW, PURPLE, GOLD, DAMAGE_NUMBER_LIFETIME, DAMAGE_NUMBER_SPEED


class Particle:
    """Simple particle with physics."""
    
    def __init__(self, x, y, color, velocity=None, size=4, lifetime=25):
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
    
    def update(self):
        self.x += self.vx
        self.y += self.vy
        self.vy += 0.2  # Gravity
        self.vx *= 0.98
        self.lifetime -= 1
        self.size = max(1, self.size * 0.95)
        return self.lifetime > 0
    
    def draw(self, surface, offset=(0, 0)):
        if self.lifetime <= 0:
            return
        ox, oy = offset
        pygame.draw.circle(surface, self.color, 
                          (int(self.x + ox), int(self.y + oy)), 
                          int(self.size))


class ParticleSystem:
    """Simple particle manager."""
    
    def __init__(self):
        self.particles = []
    
    def emit(self, x, y, color, count=8, size=4, lifetime=25):
        for _ in range(count):
            self.particles.append(Particle(x, y, color, size=size, lifetime=lifetime))
    
    def emit_explosion(self, x, y, color, count=30):
        for _ in range(count):
            angle = random.uniform(0, 2 * math.pi)
            speed = random.uniform(5, 15)
            velocity = (math.cos(angle) * speed, math.sin(angle) * speed)
            size = random.uniform(3, 8)
            self.particles.append(Particle(x, y, color, velocity=velocity, size=size, lifetime=40))
    
    def update(self):
        self.particles = [p for p in self.particles if p.update()]
    
    def draw(self, surface, offset=(0, 0)):
        for p in self.particles:
            p.draw(surface, offset)
    
    def clear(self):
        self.particles.clear()

    def emit_parry(self, x, y, color, count=20):
        """Directional upward fan — clash sparks that read as deflection,
        not impact. Visually opposite to emit_explosion's radial burst."""
        for _ in range(count):
            # Fan arc: straight up ± ~50 degrees
            angle = random.uniform(-math.pi / 2 - 0.87, -math.pi / 2 + 0.87)
            speed = random.uniform(6, 14)
            velocity = (math.cos(angle) * speed, math.sin(angle) * speed)
            size = random.uniform(2, 5)      # smaller than crit sparks
            self.particles.append(
                Particle(x, y, color, velocity=velocity, size=size, lifetime=20)
            )                                # lifetime 20 vs crit's 40 — vanish fast
            


class Shockwave:
    """Simple expanding ring."""
    
    def __init__(self, x, y, color, max_radius=150):
        self.x = x
        self.y = y
        self.color = color
        self.radius = 10
        self.max_radius = max_radius
        self.lifetime = 15
        self.max_lifetime = 15
    
    def update(self):
        self.lifetime -= 1
        progress = 1 - (self.lifetime / self.max_lifetime)
        self.radius = 10 + (self.max_radius - 10) * progress
        return self.lifetime > 0
    
    def draw(self, surface, offset=(0, 0)):
        if self.lifetime <= 0:
            return
        ox, oy = offset
        thickness = max(2, int(4 * (self.lifetime / self.max_lifetime)))
        pygame.draw.circle(surface, self.color, 
                          (int(self.x + ox), int(self.y + oy)), 
                          int(self.radius), thickness)


class ShockwaveSystem:
    """Simple shockwave manager."""
    
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
    """Visual pulse wave from arena borders toward center."""
    
    def __init__(self, arena_bounds, color=PURPLE):
        self.ax, self.ay, self.aw, self.ah = arena_bounds
        self.color = color
        self.progress = 0.0  # 0 = at borders, 1 = at center
        self.lifetime = 30  # frames
        self.max_lifetime = 30
    
    def update(self):
        self.lifetime -= 1
        self.progress = 1 - (self.lifetime / self.max_lifetime)
        return self.lifetime > 0
    
    def draw(self, surface, offset=(0, 0)):
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
        
        # Inner glow line
        if thickness > 2:
            inner_rect = pulse_rect.inflate(-4, -4)
            glow_color = (min(255, int(r * alpha * 1.5)), 
                         min(255, int(g * alpha * 1.5)), 
                         min(255, int(b * alpha * 1.5)))
            pygame.draw.rect(surface, glow_color, inner_rect, 2)


class ArenaPulseSystem:
    """Manages arena pulse visual effects."""
    
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


# Outline offset directions: 4 cardinal + 4 diagonal for a solid ring.
_OUTLINE_OFFSETS = [
    (-2,  0), ( 2,  0), ( 0, -2), ( 0,  2),
    (-2, -2), ( 2, -2), (-2,  2), ( 2,  2),
]


class DamageNumber:
    """Floating damage number that rises and fades."""
    
    def __init__(self, x, y, damage, color, is_crit=False):
        self.x = x
        self.y = y
        self.damage = int(damage)
        self.is_crit = is_crit
        # Normal hits: fighter's color fill, no outline.
        # Critical hits: white fill (readable on any background color or arena
        # tile) with the attacker's fighter color as an outline ring, so you
        # instantly know who landed the crit even when both fire at once.
        self.color = WHITE if is_crit else color
        self.outline_color = color if is_crit else None
        self.base_scale = 1.5 if is_crit else 1.0
        self.lifetime = DAMAGE_NUMBER_LIFETIME
        self.max_lifetime = DAMAGE_NUMBER_LIFETIME
        self.scale = self.base_scale
        self.vy = -DAMAGE_NUMBER_SPEED
    
    def update(self):
        self.y += self.vy
        self.vy *= 0.95  # Slow down over time
        self.lifetime -= 1
        
        # Scale up then down (crits start at 1.5x base)
        progress = 1 - (self.lifetime / self.max_lifetime)
        if progress < 0.2:
            self.scale = self.base_scale + progress * 2  # Scale up
        else:
            self.scale = (self.base_scale + 0.4) - (progress - 0.2) * 0.5  # Scale back down
        
        return self.lifetime > 0
    
    def draw(self, surface, offset, font):
        if self.lifetime <= 0:
            return
        
        ox, oy = offset
        alpha = min(255, int(255 * (self.lifetime / self.max_lifetime) * 1.5))
        text = str(self.damage)
        cx = int(self.x + ox)
        cy = int(self.y + oy)

        def _make_surf(color):
            """Render, scale, and alpha-set a text surface."""
            surf = font.render(text, True, color)
            if self.scale != 1.0:
                w = int(surf.get_width() * self.scale)
                h = int(surf.get_height() * self.scale)
                if w > 0 and h > 0:
                    surf = pygame.transform.scale(surf, (w, h))
            surf.set_alpha(alpha)
            return surf

        # Crit: stamp fighter-colored outline at each offset, then white fill.
        if self.outline_color is not None:
            outline_surf = _make_surf(self.outline_color)
            for dx, dy in _OUTLINE_OFFSETS:
                rect = outline_surf.get_rect(center=(cx + dx, cy + dy))
                surface.blit(outline_surf, rect)

        fill_surf = _make_surf(self.color)
        surface.blit(fill_surf, fill_surf.get_rect(center=(cx, cy)))


class DamageNumberSystem:
    """Manages floating damage numbers."""
    
    def __init__(self):
        self.numbers = []
        self.font = None
        # Private particle system exclusively for crit burst effects.
        # Kept internal so no other file needs to be changed — crits
        # self-contain their own explosion when spawned.
        self._crit_particles = ParticleSystem()
    
    def init_font(self):
        """Initialize font for damage numbers."""
        if self.font is None:
            try:
                self.font = pygame.font.SysFont("Impact", 28, bold=True)
            except:
                self.font = pygame.font.Font(None, 32)
    
    def spawn(self, x, y, damage, color, is_crit=False):
        """Spawn a new damage number.
        
        Crits also fire a particle explosion at the impact point in the
        attacker's color — no external call needed.
        """
        # Add random offset to prevent stacking
        x += random.uniform(-10, 10)
        y += random.uniform(-5, 5)
        self.numbers.append(DamageNumber(x, y, damage, color, is_crit))

        if is_crit:
            # Two layers: a dense core burst + a few larger sparks for spread.
            self._crit_particles.emit_explosion(x, y, color, count=25)
            # Slower, bigger sparks in a brighter tint of the fighter color
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
        self.init_font()
        # Particles draw under the number so the text stays legible
        self._crit_particles.draw(surface, offset)
        for n in self.numbers:
            n.draw(surface, offset, self.font)
    
    def clear(self):
        self.numbers.clear()
        self._crit_particles.clear()