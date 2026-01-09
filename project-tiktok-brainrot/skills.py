"""
Skill system with 7 skill-based power-ups.
Each skill focuses on animation timing, hit-stop, and visual feedback.
Spin Parry is a high-risk, high-reward reactive parry skill.
"""

import pygame
import math
import random

from config import WHITE, CYAN, ORANGE, PURPLE, GREEN, YELLOW, GOLD, PINK


class SkillType:
    """Skill move types."""
    DASH_SLASH = 0      # Short high-speed burst with trail
    SPIN_PARRY = 1      # Reactive parry with spin stance
    GROUND_SLAM = 2     # Jump + plunge with shockwave
    SHIELD = 3          # Parry stance with barrier
    PHANTOM_CROSS = 4   # Blink behind + X-slash
    BLADE_CYCLONE = 5   # Spinning vortex multi-hit
    FINAL_FLASH_DRAW = 6  # Iaido-style instant slash
    
    NAMES = {
        0: "Dash Slash",
        1: "Spin Parry",
        2: "Ground Slam",
        3: "Shield",
        4: "Phantom Cross",
        5: "Blade Cyclone",
        6: "Final Flash Draw"
    }
    
    COLORS = {
        0: CYAN,        # Dash Slash - cyan
        1: ORANGE,      # Spin Parry - orange
        2: PURPLE,      # Ground Slam - purple
        3: GREEN,       # Shield - green
        4: PINK,        # Phantom Cross - pink
        5: YELLOW,      # Blade Cyclone - yellow
        6: GOLD         # Final Flash Draw - gold
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
