"""
Base skill class for the modular skill system.
All skills should inherit from BaseSkill.
"""

from abc import ABC, abstractmethod


class BaseSkill(ABC):
    """Abstract base class for all skills."""
    
    # Skill metadata (override in subclasses)
    name: str = "Unknown Skill"
    skill_id: int = -1
    color: tuple = (255, 255, 255)
    duration: int = 30  # Default duration in frames
    
    def __init__(self):
        self.timer = 0
        self.data = {}
        self.active = False
    
    @abstractmethod
    def activate(self, fighter, opponent, particles, shockwaves):
        """
        Called when the skill is activated.
        Set up initial state, modify fighter velocity, emit particles, etc.
        """
        pass
    
    @abstractmethod
    def update(self, fighter, opponent, particles, shockwaves):
        """
        Called every frame while skill is active.
        Update skill state, check for hits, emit effects, etc.
        Returns True if skill should continue, False if complete.
        """
        pass
    
    def on_hit(self, fighter, target, particles):
        """
        Called when this skill successfully hits a target.
        Override for special hit effects.
        """
        pass
    
    def on_fail(self, fighter, particles):
        """
        Called when the skill fails (e.g., parry misses).
        Override for failure effects.
        """
        pass
    
    def is_complete(self, fighter) -> bool:
        """Check if the skill has finished."""
        return self.timer >= self.duration
    
    def get_damage_multiplier(self) -> float:
        """Get damage multiplier for this skill."""
        return 1.0
    
    def get_knockback_multiplier(self) -> float:
        """Get knockback multiplier for this skill."""
        return 1.0
