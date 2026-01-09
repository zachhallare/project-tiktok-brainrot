"""
Skill registry for dynamic skill registration and lookup.
Allows adding new skills without modifying core engine code.
"""

from typing import Dict, Type, Optional
from skills.base import BaseSkill


class SkillRegistry:
    """Central registry for all game skills."""
    
    _skills: Dict[int, Type[BaseSkill]] = {}
    _instances: Dict[int, BaseSkill] = {}
    
    @classmethod
    def register(cls, skill_id: int, skill_class: Type[BaseSkill]):
        """Register a skill class with a given ID."""
        cls._skills[skill_id] = skill_class
    
    @classmethod
    def get_class(cls, skill_id: int) -> Optional[Type[BaseSkill]]:
        """Get skill class by ID."""
        return cls._skills.get(skill_id)
    
    @classmethod
    def get_instance(cls, skill_id: int) -> Optional[BaseSkill]:
        """Get or create a skill instance by ID."""
        if skill_id not in cls._instances:
            skill_class = cls._skills.get(skill_id)
            if skill_class:
                cls._instances[skill_id] = skill_class()
        return cls._instances.get(skill_id)
    
    @classmethod
    def get_all_ids(cls) -> list:
        """Get all registered skill IDs."""
        return list(cls._skills.keys())
    
    @classmethod
    def clear(cls):
        """Clear all registered skills (for testing)."""
        cls._skills.clear()
        cls._instances.clear()


def get_skill(skill_id: int) -> Optional[BaseSkill]:
    """Convenience function to get a skill instance."""
    return SkillRegistry.get_instance(skill_id)


def register_skill(skill_id: int):
    """Decorator to register a skill class."""
    def decorator(skill_class: Type[BaseSkill]):
        SkillRegistry.register(skill_id, skill_class)
        return skill_class
    return decorator
