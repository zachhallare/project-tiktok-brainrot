"""
Modular skill system for Red vs Blue Battle.
Exports skill types, base classes, and skill orb.
"""

from skills.base import BaseSkill
from skills.registry import SkillRegistry, get_skill

# Skill type constants (for backward compatibility)
class SkillType:
    """Skill move types."""
    DASH_SLASH = 0
    SPIN_PARRY = 1
    GROUND_SLAM = 2
    SHIELD = 3
    PHANTOM_CROSS = 4
    BLADE_CYCLONE = 5
    FINAL_FLASH_DRAW = 6
    
    NAMES = {
        0: "Dash Slash",
        1: "Spin Parry",
        2: "Ground Slam",
        3: "Shield",
        4: "Phantom Cross",
        5: "Blade Cyclone",
        6: "Final Flash Draw"
    }
    
    # Import colors from config
    @staticmethod
    def get_colors():
        from config import CYAN, ORANGE, PURPLE, GREEN, PINK, YELLOW, GOLD
        return {
            0: CYAN,
            1: ORANGE,
            2: PURPLE,
            3: GREEN,
            4: PINK,
            5: YELLOW,
            6: GOLD
        }


# Re-export SkillOrb for backward compatibility
from skills.orb import SkillOrb

__all__ = ['SkillType', 'SkillOrb', 'BaseSkill', 'SkillRegistry', 'get_skill']
