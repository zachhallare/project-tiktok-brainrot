# ==============================================================================
# Physics Battle Animation - Main Entry Point
# 
# A satisfying physics-based "Red vs Blue" battle animation
# optimized for TikTok vertical video format (1080x1920)
#
# Run: python main.py
# ==============================================================================

import pygame
import os
import sys
import time

# Import our modules
import config
from physics.simulation import Simulation
from effects.particles import ParticleSystem
from effects.screen import ScreenEffects
from effects.death import DeathEffectManager
from sound.generator import SoundGenerator
from rendering.camera import Camera
from rendering.renderer import Renderer
from export.video import VideoExporter


def run_simulation(preview_mode=False):
    """
    Run the physics battle simulation.
    
    Args:
        preview_mode: If True, render in real-time window. If False, export video.
    """
    # Initialize Pygame
    pygame.init()
    pygame.font.init()
    
    # Create display/surface
    if preview_mode:
        screen = pygame.display.set_mode((config.WIDTH, config.HEIGHT))
        pygame.display.set_caption("Physics Battle - Preview")
    else:
        # Headless rendering for export
        screen = pygame.Surface((config.WIDTH, config.HEIGHT))
    
    clock = pygame.time.Clock()
    
    # Initialize systems
    simulation = Simulation()
    particle_system = ParticleSystem()
    screen_effects = ScreenEffects()
    death_manager = DeathEffectManager()
    sound_generator = SoundGenerator()
    camera = Camera()
    renderer = Renderer(screen)
    
    # For video export
    exporter = None
    if not preview_mode:
        exporter = VideoExporter()
        exporter.prepare()
    
    # Spawn teams
    simulation.spawn_teams()
    
    # Timing
    dt = 1.0 / config.FPS
    total_time = 0
    battle_over_time = None
    
    # Main loop flags
    running = True
    frame_count = 0
    max_frames = config.FPS * config.DURATION
    
    print(f"Starting battle simulation...")
    print(f"  Resolution: {config.WIDTH}x{config.HEIGHT}")
    print(f"  Duration: {config.DURATION}s")
    print(f"  Teams: Red ({config.TEAM_SIZES['red']}) vs Blue ({config.TEAM_SIZES['blue']})")
    
    start_time = time.time()
    
    while running and frame_count < max_frames:
        # Event handling (for preview mode)
        if preview_mode:
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    running = False
                elif event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_ESCAPE:
                        running = False
        
        # === UPDATE PHASE ===
        
        # Update physics simulation
        actual_dt = simulation.update(dt)
        total_time += actual_dt
        
        # Process collision events for effects
        for collision in simulation.collision_events:
            # Calculate intensity (0-1 based on impact speed)
            intensity = min(1.0, collision['impact'] / 800)
            
            # Spawn particles
            avg_color = tuple(
                (collision['ball_a'].color[i] + collision['ball_b'].color[i]) // 2
                for i in range(3)
            )
            particle_system.emit_sparks(collision['position'], avg_color, intensity=intensity)
            
            if intensity > 0.5:
                particle_system.emit_dust(collision['position'], count=3)
            
            # Screen effects
            screen_effects.trigger_impact(intensity)
            
            # Sound
            sound = sound_generator.generate_impact_sound(intensity, collision['critical'])
            sound_generator.add_sound_event(total_time, sound)
        
        # Process death events
        for death in simulation.death_events:
            # Death effect
            death_manager.create_death_effect(
                death['position'],
                death['velocity'],
                config.COLORS[death['team']],
                death['radius']
            )
            
            # Particles
            particle_system.emit_explosion(
                death['position'],
                config.COLORS[death['team']],
                death['radius']
            )
            
            # Screen flash
            screen_effects.trigger_death_flash(config.COLORS[death['team']])
            
            # Death sound
            sound = sound_generator.generate_death_sound()
            sound_generator.add_sound_event(total_time, sound)
            
            # Camera pulse on death
            camera.trigger_zoom_pulse(0.05)
        
        # Update effects
        particle_system.update(actual_dt)
        screen_effects.update(actual_dt)
        death_manager.update(actual_dt)
        
        # Update camera
        camera.follow(simulation.get_center_of_action(), simulation.get_spread())
        camera.update(actual_dt)
        
        # Check for battle end
        if simulation.is_battle_over():
            if battle_over_time is None:
                battle_over_time = total_time
                print(f"Battle over! Winner: {simulation.get_winner()}")
            
            # End after showing winner for a bit
            if total_time - battle_over_time > 3.0:
                running = False
        
        # === RENDER PHASE ===
        
        shake_offset = screen_effects.get_shake_offset()
        
        # Clear screen
        renderer.clear(camera, screen_effects)
        
        # Render death effects (behind balls)
        renderer.render_death_effects(death_manager, camera, shake_offset)
        
        # Render balls
        for ball in simulation.balls:
            renderer.render_ball(ball, camera, shake_offset)
        
        # Render particles
        renderer.render_particles(particle_system, camera, shake_offset)
        
        # Render screen effects (flash, vignette)
        renderer.render_screen_flash(screen_effects)
        renderer.render_vignette(screen_effects.get_vignette_intensity())
        
        # Render UI
        team_counts = simulation.get_alive_by_team()
        renderer.render_score(team_counts, total_time)
        
        # Slow-mo indicator
        if simulation.slowmo_active:
            renderer.render_slowmo_indicator()
        
        # Winner text
        winner = simulation.get_winner()
        if winner:
            renderer.render_winner(winner)
        
        # === OUTPUT PHASE ===
        
        if preview_mode:
            pygame.display.flip()
            clock.tick(config.FPS)
        else:
            exporter.capture_frame(screen)
            
            # Progress update every 60 frames
            if frame_count % 60 == 0:
                progress = (frame_count / max_frames) * 100
                elapsed = time.time() - start_time
                eta = (elapsed / max(1, frame_count)) * (max_frames - frame_count)
                print(f"  Progress: {progress:.1f}% | Frame {frame_count}/{max_frames} | ETA: {eta:.1f}s")
        
        frame_count += 1
    
    # Finalize
    print(f"\nSimulation complete!")
    print(f"  Total frames: {frame_count}")
    print(f"  Simulation time: {total_time:.2f}s")
    print(f"  Real time: {time.time() - start_time:.2f}s")
    
    if not preview_mode and exporter:
        # Save audio
        audio_path = "temp_audio.wav"
        print(f"\nGenerating audio track...")
        sound_generator.save_audio(audio_path, total_time)
        
        # Encode video
        print(f"\nEncoding video...")
        success = exporter.encode_video(audio_path)
        
        # Cleanup
        exporter.cleanup()
        if os.path.exists(audio_path):
            os.remove(audio_path)
        
        if success:
            print(f"\n✓ Video exported successfully: {config.OUTPUT_FILE}")
        else:
            print(f"\n✗ Video export failed!")
            print("  Make sure FFmpeg is installed and in your PATH")
    
    pygame.quit()
    return True


def main():
    """Main entry point."""
    # Check for preview mode flag
    preview_mode = '--preview' in sys.argv or '-p' in sys.argv
    
    if preview_mode:
        print("Running in PREVIEW mode (real-time window)")
        print("Press ESC to exit")
    else:
        print("Running in EXPORT mode (will create video file)")
        print("Use --preview or -p for real-time preview")
    
    print("-" * 50)
    
    run_simulation(preview_mode=preview_mode)


if __name__ == "__main__":
    main()
