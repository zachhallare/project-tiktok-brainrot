"""
Simplified particle and visual effects for performance.
Enhanced with skill-specific effects and damage numbers.
"""

import pygame
import math
import random

from config import WHITE, YELLOW, PURPLE, DAMAGE_NUMBER_LIFETIME, DAMAGE_NUMBER_SPEED


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
        # Blend color with alpha
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


class DamageNumber:
    """Floating damage number that rises and fades."""
    
    def __init__(self, x, y, damage, color):
        self.x = x
        self.y = y
        self.damage = int(damage)
        self.color = color
        self.lifetime = DAMAGE_NUMBER_LIFETIME
        self.max_lifetime = DAMAGE_NUMBER_LIFETIME
        self.scale = 1.0
        self.vy = -DAMAGE_NUMBER_SPEED
    
    def update(self):
        self.y += self.vy
        self.vy *= 0.95  # Slow down over time
        self.lifetime -= 1
        
        # Scale up then down
        progress = 1 - (self.lifetime / self.max_lifetime)
        if progress < 0.2:
            self.scale = 1.0 + progress * 2  # Scale up to 1.4
        else:
            self.scale = 1.4 - (progress - 0.2) * 0.5  # Scale back down
        
        return self.lifetime > 0
    
    def draw(self, surface, offset, font):
        if self.lifetime <= 0:
            return
        
        ox, oy = offset
        alpha = min(255, int(255 * (self.lifetime / self.max_lifetime) * 1.5))
        
        # Render damage text
        text = str(self.damage)
        
        # Create text surface
        text_surface = font.render(text, True, self.color)
        
        # Scale the text
        if self.scale != 1.0:
            new_width = int(text_surface.get_width() * self.scale)
            new_height = int(text_surface.get_height() * self.scale)
            if new_width > 0 and new_height > 0:
                text_surface = pygame.transform.scale(text_surface, (new_width, new_height))
        
        # Apply alpha by blitting to a transparent surface
        text_surface.set_alpha(alpha)
        
        # Center the text at position
        text_rect = text_surface.get_rect(center=(int(self.x + ox), int(self.y + oy)))
        surface.blit(text_surface, text_rect)


class DamageNumberSystem:
    """Manages floating damage numbers."""
    
    def __init__(self):
        self.numbers = []
        self.font = None
    
    def init_font(self):
        """Initialize font for damage numbers."""
        if self.font is None:
            try:
                # Try to use a bold/impact font
                self.font = pygame.font.SysFont("Impact", 28, bold=True)
            except:
                self.font = pygame.font.Font(None, 32)
    
    def spawn(self, x, y, damage, color):
        """Spawn a new damage number."""
        # Add random offset to prevent stacking
        x += random.uniform(-10, 10)
        y += random.uniform(-5, 5)
        self.numbers.append(DamageNumber(x, y, damage, color))
    
    def update(self):
        self.numbers = [n for n in self.numbers if n.update()]
    
    def draw(self, surface, offset=(0, 0)):
        self.init_font()
        for n in self.numbers:
            n.draw(surface, offset, self.font)
    
    def clear(self):
        self.numbers.clear()
