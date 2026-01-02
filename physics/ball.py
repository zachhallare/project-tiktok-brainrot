# ==============================================================================
# Ball Entity - Represents a single ball/particle in the simulation
# ==============================================================================

import pymunk
import random
import config


class Ball:
    """
    A physics-enabled ball with health, team affiliation, and combat properties.
    """
    
    def __init__(self, space, pos, team, radius=None, mass=None):
        """
        Create a new ball in the physics space.
        
        Args:
            space: Pymunk space to add the ball to
            pos: (x, y) initial position
            team: Team name ('red' or 'blue')
            radius: Ball radius (randomized if None)
            mass: Ball mass (randomized if None)
        """
        self.team = team
        self.color = config.COLORS[team]
        
        # Randomize properties if not specified
        self.radius = radius or random.uniform(*config.BALL_RADIUS_RANGE)
        mass = mass or random.uniform(*config.BALL_MASS_RANGE)
        
        # Health system
        self.max_health = config.INITIAL_HEALTH
        self.health = self.max_health
        self.is_dead = False
        self.death_time = None
        
        # Visual state
        self.trail_positions = []
        self.hit_flash = 0  # Flash effect on taking damage
        self.damage_cracks = 0  # Visual damage indicator
        
        # Create physics body
        moment = pymunk.moment_for_circle(mass, 0, self.radius)
        self.body = pymunk.Body(mass, moment)
        self.body.position = pos
        
        # Give initial random velocity for dynamic start
        self.body.velocity = (
            random.uniform(-200, 200),
            random.uniform(-100, 100)
        )
        
        # Create collision shape
        self.shape = pymunk.Circle(self.body, self.radius)
        self.shape.elasticity = config.ELASTICITY
        self.shape.friction = config.FRICTION
        self.shape.collision_type = 1  # Ball collision type
        self.shape.ball = self  # Reference back to this object
        
        # Add to physics space
        space.add(self.body, self.shape)
        self.space = space
    
    def take_damage(self, damage, is_critical=False):
        """
        Apply damage to this ball.
        
        Args:
            damage: Amount of damage to apply
            is_critical: Whether this is a critical hit
            
        Returns:
            bool: True if the ball died from this damage
        """
        if self.is_dead:
            return False
        
        actual_damage = damage * (config.CRITICAL_HIT_MULTIPLIER if is_critical else 1)
        self.health -= actual_damage
        self.hit_flash = 1.0  # Trigger hit flash
        self.damage_cracks = min(1.0, 1.0 - (self.health / self.max_health))
        
        if self.health <= 0:
            self.health = 0
            self.is_dead = True
            return True
        return False
    
    def apply_knockback(self, direction, force):
        """Apply knockback force in a direction."""
        impulse = (direction[0] * force, direction[1] * force)
        self.body.apply_impulse_at_local_point(impulse)
    
    def update(self, dt):
        """Update ball state each frame."""
        # Update trail
        self.trail_positions.append(tuple(self.body.position))
        if len(self.trail_positions) > config.TRAIL_LENGTH:
            self.trail_positions.pop(0)
        
        # Decay hit flash
        if self.hit_flash > 0:
            self.hit_flash = max(0, self.hit_flash - dt * 5)
    
    def remove(self):
        """Remove ball from physics space."""
        if self.body in self.space.bodies:
            self.space.remove(self.body, self.shape)
    
    @property
    def position(self):
        return self.body.position
    
    @property
    def velocity(self):
        return self.body.velocity
    
    @property
    def speed(self):
        return self.body.velocity.length
    
    @property
    def health_percent(self):
        return self.health / self.max_health
    
    def get_glow_intensity(self):
        """Calculate glow intensity based on health and speed."""
        health_glow = self.health_percent * config.GLOW_INTENSITY
        speed_glow = min(0.3, self.speed / 1000)
        return min(1.0, health_glow + speed_glow + self.hit_flash * 0.5)
