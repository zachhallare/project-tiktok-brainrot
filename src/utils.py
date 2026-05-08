"""
Utility functions for the Anime Sword Battle game.

This module provides common mathematical operations used across the physics
and rendering systems, such as linear interpolation and value clamping.
"""

import math


def lerp(a: float, b: float, t: float) -> float:
    """Linearly interpolates between two values.

    Args:
        a: The starting value.
        b: The ending value.
        t: The interpolation factor (typically 0.0 to 1.0).

    Returns:
        The value between a and b based on t.
    """
    return a + (b - a) * t


def angle_lerp(a: float, b: float, t: float) -> float:
    """Interpolates between two angles, correctly handling the 2π wraparound.

    This ensures that rotation always takes the shortest path between two angles,
    preventing "spinning the long way around" during transitions.

    Args:
        a: Starting angle in radians.
        b: Target angle in radians.
        t: Interpolation factor.

    Returns:
        The interpolated angle in radians.
    """
    diff = ((b - a + math.pi) % (2 * math.pi)) - math.pi
    return a + diff * t


def clamp(val: float, min_val: float, max_val: float) -> float:
    """Clamps a value between a minimum and maximum bound.

    Args:
        val: The value to clamp.
        min_val: The lower bound.
        max_val: The upper bound.

    Returns:
        The clamped value.
    """
    return max(min_val, min(max_val, val))
