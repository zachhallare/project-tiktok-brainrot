"""
SkillOrb class - power-up collectible that grants skills.
"""

import pygame
import math

# Import colors directly to avoid circular imports
WHITE = (255, 255, 255)


class SkillOrb:
    """Simple power-up orb - solid circle, no effects."""
    
    # Skill colors (defined here to avoid import issues)
    SKILL_COLORS = {
        0: (100, 255, 255),   # Dash Slash - cyan
        1: (255, 180, 80),    # Spin Parry - orange  
        2: (200, 100, 255),   # Ground Slam - purple
        3: (100, 255, 150),   # Shield - green
        4: (255, 100, 200),   # Phantom Cross - pink
        5: (255, 220, 100),   # Blade Cyclone - yellow
        6: (255, 215, 0)      # Final Flash Draw - gold
    }
    
    def __init__(self, x, y, skill_type):
        self.x = x
        self.y = y
        self.skill_type = skill_type
        self.color = self.SKILL_COLORS.get(skill_type, WHITE)
        self.radius = 15
    
    def update(self):
        pass  # No floating/pulsing
    
    def draw(self, surface, offset=(0, 0)):
        ox, oy = offset
        # Simple solid circle
        pygame.draw.circle(surface, self.color, 
                          (int(self.x + ox), int(self.y + oy)), self.radius)
        # Small white center dot
        pygame.draw.circle(surface, WHITE, 
                          (int(self.x + ox), int(self.y + oy)), 5)
    
    def check_collision(self, fighter):
        dist = math.hypot(self.x - fighter.x, self.y - fighter.y)
        return dist < self.radius + fighter.radius
