# ==============================================================================
# Physics Simulation Engine - Core physics and collision handling
# ==============================================================================

import pymunk
import random
import math
import config
from physics.ball import Ball


class Simulation:
    """
    Manages the physics simulation including space, balls, and collisions.
    """
    
    def __init__(self):
        """Initialize the physics simulation."""
        # Create physics space
        self.space = pymunk.Space()
        self.space.gravity = (0, config.GRAVITY)
        self.space.damping = config.DAMPING
        
        # Storage
        self.balls = []
        self.dead_balls = []  # Recently dead for death animations
        self.collision_events = []  # For sound/effects
        self.death_events = []  # For death effects
        
        # Time tracking
        self.time = 0
        self.slowmo_active = False
        self.slowmo_timer = 0
        
        # Set up collision handler
        self.space.on_collision(1, 1, post_solve=self._handle_collision)
        
        # Create walls
        self._create_walls()
    
    def _create_walls(self):
        """Create boundary walls for the arena."""
        wall_thickness = 50
        walls = [
            # Bottom
            [(0, config.HEIGHT), (config.WIDTH, config.HEIGHT)],
            # Left
            [(0, 0), (0, config.HEIGHT)],
            # Right
            [(config.WIDTH, 0), (config.WIDTH, config.HEIGHT)],
            # Top (optional - can remove for balls to fall in from top)
            [(0, 0), (config.WIDTH, 0)],
        ]
        
        for wall in walls:
            body = pymunk.Body(body_type=pymunk.Body.STATIC)
            shape = pymunk.Segment(body, wall[0], wall[1], wall_thickness)
            shape.elasticity = 0.8
            shape.friction = 0.5
            shape.collision_type = 2  # Wall collision type
            self.space.add(body, shape)
    
    def _handle_collision(self, arbiter, space, data):
        """
        Handle collision between two balls.
        Calculate damage and apply knockback based on impact force.
        """
        if len(arbiter.shapes) != 2:
            return True
        
        shape_a, shape_b = arbiter.shapes
        
        # Only handle ball-ball collisions
        if not (hasattr(shape_a, 'ball') and hasattr(shape_b, 'ball')):
            return True
        
        ball_a = shape_a.ball
        ball_b = shape_b.ball
        
        # Skip if same team or either is dead
        if ball_a.team == ball_b.team or ball_a.is_dead or ball_b.is_dead:
            return True
        
        # Calculate impact force from relative velocity
        relative_velocity = ball_a.velocity - ball_b.velocity
        impact_speed = relative_velocity.length
        
        # Total impulse from collision
        total_impulse = sum(point.total_impulse.length for point in arbiter.contact_point_set.points)
        
        if impact_speed < 50:  # Minimum threshold
            return True
        
        # Calculate damage for each ball
        damage_to_a = impact_speed * ball_b.body.mass * config.DAMAGE_MULTIPLIER
        damage_to_b = impact_speed * ball_a.body.mass * config.DAMAGE_MULTIPLIER
        
        # Check for critical hits
        crit_a = random.random() < config.CRITICAL_HIT_CHANCE
        crit_b = random.random() < config.CRITICAL_HIT_CHANCE
        
        # Apply damage
        death_a = ball_a.take_damage(damage_to_a, crit_a)
        death_b = ball_b.take_damage(damage_to_b, crit_b)
        
        # Apply knockback
        if arbiter.contact_point_set.points:
            contact = arbiter.contact_point_set.points[0]
            normal = arbiter.contact_point_set.normal
            
            ball_a.apply_knockback((-normal.x, -normal.y), config.KNOCKBACK_FORCE * ball_b.body.mass)
            ball_b.apply_knockback((normal.x, normal.y), config.KNOCKBACK_FORCE * ball_a.body.mass)
        
        # Record collision event for effects/sound
        collision_pos = arbiter.contact_point_set.points[0].point_a if arbiter.contact_point_set.points else ball_a.position
        self.collision_events.append({
            'position': collision_pos,
            'impact': impact_speed,
            'impulse': total_impulse,
            'ball_a': ball_a,
            'ball_b': ball_b,
            'critical': crit_a or crit_b,
        })
        
        # Handle deaths
        for ball, died in [(ball_a, death_a), (ball_b, death_b)]:
            if died:
                self.death_events.append({
                    'ball': ball,
                    'position': tuple(ball.position),
                    'velocity': tuple(ball.velocity),
                    'team': ball.team,
                    'radius': ball.radius,
                })
        
        return True
    
    def spawn_teams(self):
        """Spawn all team balls in initial positions."""
        margin = 100
        
        for team, count in config.TEAM_SIZES.items():
            # Position teams on opposite sides
            if team == 'red':
                x_range = (margin, config.WIDTH * 0.35)
            else:
                x_range = (config.WIDTH * 0.65, config.WIDTH - margin)
            
            for _ in range(count):
                x = random.uniform(*x_range)
                y = random.uniform(margin, config.HEIGHT * 0.4)
                ball = Ball(self.space, (x, y), team)
                self.balls.append(ball)
    
    def update(self, dt):
        """
        Update the simulation by one time step.
        
        Args:
            dt: Delta time in seconds
            
        Returns:
            float: The actual dt used (may be modified for slow-mo)
        """
        # Clear events from previous frame
        self.collision_events = []
        self.death_events = []
        
        # Check for slow-mo trigger
        alive_count = sum(1 for b in self.balls if not b.is_dead)
        if alive_count <= config.SLOWMO_THRESHOLD and not self.slowmo_active:
            self.slowmo_active = True
            self.slowmo_timer = config.SLOWMO_DURATION
        
        # Apply slow-mo
        actual_dt = dt
        if self.slowmo_active:
            actual_dt = dt * config.SLOWMO_FACTOR
            self.slowmo_timer -= dt
            if self.slowmo_timer <= 0:
                self.slowmo_active = False
        
        # Step physics
        self.space.step(actual_dt)
        self.time += actual_dt
        
        # Update all balls
        for ball in self.balls:
            ball.update(actual_dt)
        
        # Process deaths
        for ball in self.balls[:]:
            if ball.is_dead:
                ball.death_time = self.time
                self.dead_balls.append(ball)
                self.balls.remove(ball)
                ball.remove()
        
        # Clean up old dead balls
        self.dead_balls = [b for b in self.dead_balls if self.time - b.death_time < 1.0]
        
        return actual_dt
    
    def get_alive_by_team(self):
        """Get count of alive balls per team."""
        counts = {}
        for ball in self.balls:
            if not ball.is_dead:
                counts[ball.team] = counts.get(ball.team, 0) + 1
        return counts
    
    def is_battle_over(self):
        """Check if the battle has ended (one team eliminated)."""
        counts = self.get_alive_by_team()
        return len(counts) <= 1
    
    def get_winner(self):
        """Get the winning team, or None if battle ongoing."""
        if not self.is_battle_over():
            return None
        counts = self.get_alive_by_team()
        return list(counts.keys())[0] if counts else None
    
    def get_center_of_action(self):
        """Get the center position of all alive balls."""
        if not self.balls:
            return (config.WIDTH / 2, config.HEIGHT / 2)
        
        x = sum(b.position.x for b in self.balls) / len(self.balls)
        y = sum(b.position.y for b in self.balls) / len(self.balls)
        return (x, y)
    
    def get_spread(self):
        """Get the spread (max distance from center) of balls."""
        if len(self.balls) < 2:
            return config.WIDTH / 2
        
        center = self.get_center_of_action()
        max_dist = 0
        for ball in self.balls:
            dx = ball.position.x - center[0]
            dy = ball.position.y - center[1]
            dist = math.sqrt(dx*dx + dy*dy) + ball.radius
            max_dist = max(max_dist, dist)
        
        return max_dist
