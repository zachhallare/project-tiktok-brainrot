"""
Simplified skill system - solid colored orbs, no animations.
"""

import pygame
import math
import random

from config import WHITE, CYAN, ORANGE, PURPLE, GREEN


class SkillType:
    """Skill move types."""
    DASH_SLASH = 0
    SPIN_CUTTER = 1
    GROUND_SLAM = 2
    SHIELD = 3
    OVERDRIVE = 4
    
    NAMES = {
        0: "Dash Slash",
        1: "Spin Cutter",
        2: "Ground Slam",
        3: "Shield",
        4: "Overdrive"
    }
    
    COLORS = {
        0: CYAN,
        1: ORANGE,
        2: PURPLE,
        3: GREEN,
        4: (255, 100, 200)  # Pink
    }


class SkillOrb:
    """Simple power-up orb - solid circle, no effects."""
    
    def __init__(self, x, y, skill_type):
        self.x = x
        self.y = y
        self.skill_type = skill_type
        self.color = SkillType.COLORS[skill_type]
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
