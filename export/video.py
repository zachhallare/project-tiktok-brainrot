# ==============================================================================
# Video Export - Frame capture and FFmpeg encoding
# ==============================================================================

import pygame
import subprocess
import os
import shutil
import config


class VideoExporter:
    """
    Handles frame capture and video encoding using FFmpeg.
    """
    
    def __init__(self, output_path=None):
        """
        Initialize video exporter.
        
        Args:
            output_path: Output MP4 file path
        """
        self.output_path = output_path or config.OUTPUT_FILE
        self.frames_dir = config.TEMP_FRAMES_DIR
        self.frame_count = 0
        
        # Check for FFmpeg
        self.ffmpeg_available = self._check_ffmpeg()
    
    def _check_ffmpeg(self):
        """Check if FFmpeg is available."""
        try:
            subprocess.run(
                ['ffmpeg', '-version'],
                capture_output=True,
                check=True
            )
            return True
        except (subprocess.CalledProcessError, FileNotFoundError):
            return False
    
    def prepare(self):
        """Prepare for frame capture."""
        # Create temp frames directory
        if os.path.exists(self.frames_dir):
            shutil.rmtree(self.frames_dir)
        os.makedirs(self.frames_dir)
        
        self.frame_count = 0
    
    def capture_frame(self, surface):
        """
        Capture a frame from the Pygame surface.
        
        Args:
            surface: Pygame surface to capture
        """
        frame_path = os.path.join(self.frames_dir, f'frame_{self.frame_count:06d}.png')
        pygame.image.save(surface, frame_path)
        self.frame_count += 1
    
    def encode_video(self, audio_path=None, progress_callback=None):
        """
        Encode captured frames to MP4 using FFmpeg.
        
        Args:
            audio_path: Optional path to audio file to include
            progress_callback: Optional callback for progress updates
            
        Returns:
            bool: True if successful
        """
        if not self.ffmpeg_available:
            print("ERROR: FFmpeg not found!")
            print("Please install FFmpeg and add it to your PATH:")
            print("  Windows: https://ffmpeg.org/download.html")
            print("  Or use: winget install ffmpeg")
            return False
        
        if self.frame_count == 0:
            print("ERROR: No frames captured!")
            return False
        
        # Build FFmpeg command
        input_pattern = os.path.join(self.frames_dir, 'frame_%06d.png')
        
        cmd = [
            'ffmpeg',
            '-y',  # Overwrite output
            '-framerate', str(config.FPS),
            '-i', input_pattern,
        ]
        
        # Add audio if provided
        if audio_path and os.path.exists(audio_path):
            cmd.extend(['-i', audio_path])
        
        # Video encoding settings optimized for TikTok
        cmd.extend([
            '-c:v', 'libx264',
            '-preset', 'medium',
            '-crf', '20',  # High quality
            '-pix_fmt', 'yuv420p',  # Compatibility
            '-movflags', '+faststart',  # Web optimization
        ])
        
        # Audio settings
        if audio_path and os.path.exists(audio_path):
            cmd.extend([
                '-c:a', 'aac',
                '-b:a', '192k',
                '-shortest',  # Match video length
            ])
        
        # Output
        cmd.append(self.output_path)
        
        print(f"Encoding video with FFmpeg...")
        print(f"  Frames: {self.frame_count}")
        print(f"  FPS: {config.FPS}")
        print(f"  Output: {self.output_path}")
        
        try:
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True
            )
            
            if result.returncode != 0:
                print(f"FFmpeg error: {result.stderr}")
                return False
            
            print(f"Video saved to: {self.output_path}")
            return True
            
        except Exception as e:
            print(f"Encoding error: {e}")
            return False
    
    def cleanup(self):
        """Clean up temporary frame files."""
        if os.path.exists(self.frames_dir):
            shutil.rmtree(self.frames_dir)
            print("Cleaned up temporary frames.")
    
    def get_stats(self):
        """Get export statistics."""
        return {
            'frames': self.frame_count,
            'duration': self.frame_count / config.FPS,
            'resolution': (config.WIDTH, config.HEIGHT),
            'fps': config.FPS,
        }
