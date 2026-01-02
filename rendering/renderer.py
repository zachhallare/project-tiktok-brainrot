# ==============================================================================
# Renderer - Main rendering pipeline for the simulation
# ==============================================================================

import pygame
import math
import config


class Renderer:
    """
    Main rendering system for balls, particles, effects, and UI.
    """
    
    def __init__(self, surface):
        """
        Initialize renderer.
        
        Args:
            surface: Pygame surface to render to
        """
        self.surface = surface
        self.font = None
        
        # Pre-create surfaces for effects
        self._create_glow_surfaces()
    
    def _create_glow_surfaces(self):
        """Pre-create glow effect surfaces for performance."""
        self.glow_surfaces = {}
        
        for team, color in [('red', config.COLORS['red']), ('blue', config.COLORS['blue'])]:
            for size in range(20, 60, 5):
                glow_size = int(size * 3)
                glow_surf = pygame.Surface((glow_size, glow_size), pygame.SRCALPHA)
                
                center = glow_size // 2
                for r in range(size, 0, -2):
                    alpha = int(30 * (r / size))
                    glow_color = (*color, alpha)
                    pygame.draw.circle(glow_surf, glow_color, (center, center), int(r * 1.5))
                
                self.glow_surfaces[(team, size)] = glow_surf
    
    def clear(self, camera, screen_effects):
        """Clear the screen with background color."""
        self.surface.fill(config.COLORS['background'])
    
    def render_ball(self, ball, camera, shake_offset):
        """
        Render a single ball with effects.
        
        Args:
            ball: Ball object to render
            camera: Camera for coordinate conversion
            shake_offset: Screen shake offset
        """
        screen_pos = camera.world_to_screen(ball.position, shake_offset)
        screen_radius = camera.scale_size(ball.radius)
        
        # Skip if off screen
        if (screen_pos[0] < -screen_radius or screen_pos[0] > config.WIDTH + screen_radius or
            screen_pos[1] < -screen_radius or screen_pos[1] > config.HEIGHT + screen_radius):
            return
        
        # Draw trail
        if len(ball.trail_positions) > 1:
            trail_color = tuple(int(c * 0.3) for c in ball.color)
            for i, pos in enumerate(ball.trail_positions[:-1]):
                alpha = (i + 1) / len(ball.trail_positions)
                trail_screen = camera.world_to_screen(pos, shake_offset)
                radius = int(screen_radius * alpha * 0.6)
                if radius > 0:
                    pygame.draw.circle(
                        self.surface,
                        tuple(int(c * alpha) for c in trail_color),
                        (int(trail_screen[0]), int(trail_screen[1])),
                        radius
                    )
        
        # Draw glow
        glow_intensity = ball.get_glow_intensity()
        if glow_intensity > 0.1:
            glow_key = (ball.team, int(ball.radius / 5) * 5)
            if glow_key in self.glow_surfaces:
                glow_surf = self.glow_surfaces[glow_key].copy()
                glow_surf.set_alpha(int(glow_intensity * 100))
                glow_rect = glow_surf.get_rect(center=(int(screen_pos[0]), int(screen_pos[1])))
                self.surface.blit(glow_surf, glow_rect)
        
        # Draw main ball
        # Color intensity based on health
        health_factor = 0.4 + ball.health_percent * 0.6
        ball_color = tuple(int(c * health_factor) for c in ball.color)
        
        # Add hit flash
        if ball.hit_flash > 0:
            flash_add = int(ball.hit_flash * 150)
            ball_color = tuple(min(255, c + flash_add) for c in ball_color)
        
        pygame.draw.circle(
            self.surface,
            ball_color,
            (int(screen_pos[0]), int(screen_pos[1])),
            int(screen_radius)
        )
        
        # Draw highlight (3D effect)
        highlight_offset = screen_radius * 0.3
        highlight_radius = screen_radius * 0.25
        highlight_pos = (
            int(screen_pos[0] - highlight_offset),
            int(screen_pos[1] - highlight_offset)
        )
        highlight_color = tuple(min(255, c + 80) for c in ball_color)
        pygame.draw.circle(
            self.surface,
            highlight_color,
            highlight_pos,
            int(highlight_radius)
        )
        
        # Draw damage cracks if damaged
        if ball.damage_cracks > 0.3:
            crack_color = (30, 30, 35)
            num_cracks = int(ball.damage_cracks * 5)
            for i in range(num_cracks):
                angle = (2 * math.pi / num_cracks) * i + ball.damage_cracks
                inner = screen_radius * 0.3
                outer = screen_radius * (0.6 + ball.damage_cracks * 0.4)
                
                start = (
                    screen_pos[0] + math.cos(angle) * inner,
                    screen_pos[1] + math.sin(angle) * inner
                )
                end = (
                    screen_pos[0] + math.cos(angle) * outer,
                    screen_pos[1] + math.sin(angle) * outer
                )
                
                pygame.draw.line(self.surface, crack_color, start, end, 2)
    
    def render_particles(self, particle_system, camera, shake_offset):
        """Render all particles."""
        for particle in particle_system.particles:
            screen_pos = camera.world_to_screen((particle.x, particle.y), shake_offset)
            size = camera.scale_size(particle.current_size)
            
            if size < 1:
                continue
            
            # Apply alpha to color
            alpha = particle.alpha
            color = tuple(int(c * alpha) for c in particle.color)
            
            if particle.particle_type == 'spark':
                pygame.draw.circle(
                    self.surface,
                    color,
                    (int(screen_pos[0]), int(screen_pos[1])),
                    max(1, int(size))
                )
            elif particle.particle_type == 'debris':
                # Draw as small rectangle
                pygame.draw.rect(
                    self.surface,
                    color,
                    (int(screen_pos[0] - size/2), int(screen_pos[1] - size/2),
                     int(size), int(size))
                )
            elif particle.particle_type == 'flash':
                # Draw as bright circle
                bright_color = tuple(min(255, c + 50) for c in color)
                pygame.draw.circle(
                    self.surface,
                    bright_color,
                    (int(screen_pos[0]), int(screen_pos[1])),
                    max(1, int(size))
                )
            else:  # dust
                # Draw as soft circle with alpha
                dust_surf = pygame.Surface((int(size*2), int(size*2)), pygame.SRCALPHA)
                pygame.draw.circle(
                    dust_surf,
                    (*color, int(alpha * 100)),
                    (int(size), int(size)),
                    int(size)
                )
                self.surface.blit(dust_surf, (int(screen_pos[0] - size), int(screen_pos[1] - size)))
    
    def render_death_effects(self, death_manager, camera, shake_offset):
        """Render death effect animations."""
        for effect in death_manager.effects:
            # Draw shockwave
            if effect.shockwave_alpha > 0.05:
                screen_pos = camera.world_to_screen((effect.x, effect.y), shake_offset)
                radius = camera.scale_size(effect.shockwave_radius)
                alpha = int(effect.shockwave_alpha * 150)
                
                shockwave_surf = pygame.Surface((int(radius * 2 + 4), int(radius * 2 + 4)), pygame.SRCALPHA)
                pygame.draw.circle(
                    shockwave_surf,
                    (*effect.color, alpha),
                    (int(radius + 2), int(radius + 2)),
                    int(radius),
                    max(2, int(5 * effect.shockwave_alpha))
                )
                self.surface.blit(
                    shockwave_surf,
                    (int(screen_pos[0] - radius - 2), int(screen_pos[1] - radius - 2))
                )
            
            # Draw fragments
            for fragment in effect.fragments:
                screen_pos = camera.world_to_screen((fragment.x, fragment.y), shake_offset)
                size = camera.scale_size(fragment.size)
                
                alpha = fragment.alpha
                color = tuple(int(c * alpha) for c in fragment.color)
                
                # Simple fragment as circle
                pygame.draw.circle(
                    self.surface,
                    color,
                    (int(screen_pos[0]), int(screen_pos[1])),
                    max(1, int(size))
                )
    
    def render_screen_flash(self, screen_effects):
        """Render screen flash overlay."""
        color, alpha = screen_effects.get_flash()
        if alpha > 0.01:
            flash_surf = pygame.Surface((config.WIDTH, config.HEIGHT), pygame.SRCALPHA)
            flash_surf.fill((*color, int(alpha * 255)))
            self.surface.blit(flash_surf, (0, 0))
    
    def render_vignette(self, intensity):
        """Render vignette effect for dramatic moments."""
        if intensity < 0.05:
            return
        
        vignette_surf = pygame.Surface((config.WIDTH, config.HEIGHT), pygame.SRCALPHA)
        
        # Create radial gradient
        center_x, center_y = config.WIDTH // 2, config.HEIGHT // 2
        max_dist = math.sqrt(center_x**2 + center_y**2)
        
        for i in range(0, 255, 8):
            radius = max_dist * (1 - i / 255)
            alpha = int(intensity * 150 * (i / 255))
            pygame.draw.circle(
                vignette_surf,
                (0, 0, 0, alpha),
                (center_x, center_y),
                int(radius),
                8
            )
        
        self.surface.blit(vignette_surf, (0, 0))
    
    def render_score(self, team_counts, battle_time):
        """Render team score/count display."""
        if self.font is None:
            self.font = pygame.font.Font(None, 72)
        
        # Red team count (left)
        red_count = team_counts.get('red', 0)
        red_text = self.font.render(str(red_count), True, config.COLORS['red'])
        self.surface.blit(red_text, (50, 50))
        
        # Blue team count (right)
        blue_count = team_counts.get('blue', 0)
        blue_text = self.font.render(str(blue_count), True, config.COLORS['blue'])
        blue_rect = blue_text.get_rect(topright=(config.WIDTH - 50, 50))
        self.surface.blit(blue_text, blue_rect)
        
        # VS in center
        vs_text = self.font.render("VS", True, (150, 150, 150))
        vs_rect = vs_text.get_rect(center=(config.WIDTH // 2, 65))
        self.surface.blit(vs_text, vs_rect)
    
    def render_slowmo_indicator(self):
        """Render slow-motion indicator."""
        if self.font is None:
            self.font = pygame.font.Font(None, 48)
        
        slowmo_text = self.font.render("SLOW MOTION", True, (255, 200, 50))
        slowmo_rect = slowmo_text.get_rect(center=(config.WIDTH // 2, config.HEIGHT - 100))
        
        # Pulsing effect
        pulse_surf = pygame.Surface(slowmo_text.get_size(), pygame.SRCALPHA)
        pulse_surf.fill((255, 200, 50, 50))
        self.surface.blit(pulse_surf, slowmo_rect)
        self.surface.blit(slowmo_text, slowmo_rect)
    
    def render_winner(self, winner):
        """Render winner announcement."""
        if self.font is None:
            self.font = pygame.font.Font(None, 96)
        
        color = config.COLORS.get(winner, (255, 255, 255))
        text = f"{winner.upper()} WINS!"
        winner_text = self.font.render(text, True, color)
        winner_rect = winner_text.get_rect(center=(config.WIDTH // 2, config.HEIGHT // 2))
        
        # Background
        bg_rect = winner_rect.inflate(40, 20)
        bg_surf = pygame.Surface(bg_rect.size, pygame.SRCALPHA)
        pygame.draw.rect(bg_surf, (0, 0, 0, 180), bg_surf.get_rect(), border_radius=10)
        self.surface.blit(bg_surf, bg_rect)
        
        self.surface.blit(winner_text, winner_rect)
