import os
import subprocess
from typing import Optional, Dict, Any
import json

class VideoProcessor:
    """Service for processing video files"""
    
    def __init__(self):
        self.temp_dir = "temp"
        os.makedirs(self.temp_dir, exist_ok=True)
    
    def extract_audio(self, video_path: str, output_path: str) -> bool:
        """Extract audio from video file using ffmpeg"""
        try:
            command = [
                "ffmpeg",
                "-i", video_path,
                "-vn",  # No video
                "-acodec", "pcm_s16le",  # PCM 16-bit
                "-ar", "16000",  # Sample rate 16kHz
                "-ac", "1",  # Mono
                "-y",  # Overwrite output file
                output_path
            ]
            
            result = subprocess.run(command, capture_output=True, text=True)
            return result.returncode == 0
            
        except Exception as e:
            print(f"Error extracting audio: {e}")
            return False
    
    def get_video_metadata(self, video_path: str) -> Optional[Dict[str, Any]]:
        """Get video metadata using ffprobe"""
        try:
            command = [
                "ffprobe",
                "-v", "quiet",
                "-print_format", "json",
                "-show_format",
                "-show_streams",
                video_path
            ]
            
            result = subprocess.run(command, capture_output=True, text=True)
            if result.returncode == 0:
                return json.loads(result.stdout)
            else:
                return None
                
        except Exception as e:
            print(f"Error getting video metadata: {e}")
            return None
    
    def get_video_duration(self, video_path: str) -> Optional[float]:
        """Get video duration in seconds"""
        metadata = self.get_video_metadata(video_path)
        if metadata and "format" in metadata:
            duration = metadata["format"].get("duration")
            if duration:
                return float(duration)
        return None
    
    def create_thumbnail(self, video_path: str, output_path: str, timestamp: float = 10.0) -> bool:
        """Create a thumbnail from video at specified timestamp"""
        try:
            command = [
                "ffmpeg",
                "-i", video_path,
                "-ss", str(timestamp),
                "-vframes", "1",
                "-y",  # Overwrite output file
                output_path
            ]
            
            result = subprocess.run(command, capture_output=True, text=True)
            return result.returncode == 0
            
        except Exception as e:
            print(f"Error creating thumbnail: {e}")
            return False
    
    def cleanup_temp_files(self):
        """Clean up temporary files"""
        try:
            for file in os.listdir(self.temp_dir):
                file_path = os.path.join(self.temp_dir, file)
                if os.path.isfile(file_path):
                    os.remove(file_path)
        except Exception as e:
            print(f"Error cleaning up temp files: {e}") 