"""
Utility functions for the Anime Sword Battle game.
"""

import math


def lerp(a, b, t):
    """Linear interpolation between a and b."""
    return a + (b - a) * t


def angle_lerp(a, b, t):
    """Interpolate between two angles, handling wraparound."""
    diff = ((b - a + math.pi) % (2 * math.pi)) - math.pi
    return a + diff * t


def clamp(val, min_val, max_val):
    """Clamp value between min and max."""
    return max(min_val, min(max_val, val))
