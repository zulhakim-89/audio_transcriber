"""
Audio processing utilities for transcription app.
Handles audio conversion, normalization, and format validation using FFmpeg.
"""

import subprocess
import json
from pathlib import Path


def convert_to_wav(input_path: Path, output_path: Path, sample_rate: int = 16000) -> Path:
    """
    Convert audio/video file to WAV format using FFmpeg with normalization.
    
    Args:
        input_path: Path to input file
        output_path: Path to output WAV file
        sample_rate: Target sample rate (default 16kHz)
    
    Returns:
        Path to converted WAV file
    """
    output_path.parent.mkdir(parents=True, exist_ok=True)
    
    # Combine conversion and normalization in one FFmpeg pass
    cmd = [
        "ffmpeg",
        "-y",  # Overwrite output file
        "-i", str(input_path),
        "-ac", "1",  # Mono
        "-ar", str(sample_rate),  # Sample rate
        "-af", "loudnorm=I=-20:TP=-1.5:LRA=11",  # Loudness normalization
        "-vn",  # No video
        str(output_path),
    ]
    
    subprocess.run(
        cmd, 
        check=True, 
        stdout=subprocess.PIPE, 
        stderr=subprocess.PIPE,
        creationflags=subprocess.CREATE_NO_WINDOW if hasattr(subprocess, 'CREATE_NO_WINDOW') else 0
    )
    
    return output_path


def get_audio_duration(audio_path: Path) -> float:
    """
    Get duration of audio file in seconds using FFprobe.
    
    Args:
        audio_path: Path to audio file
    
    Returns:
        Duration in seconds
    """
    cmd = [
        "ffprobe",
        "-v", "quiet",
        "-print_format", "json",
        "-show_format",
        "-show_streams",
        str(audio_path)
    ]
    
    result = subprocess.run(
        cmd,
        capture_output=True,
        text=True,
        creationflags=subprocess.CREATE_NO_WINDOW if hasattr(subprocess, 'CREATE_NO_WINDOW') else 0
    )
    
    if result.returncode == 0:
        data = json.loads(result.stdout)
        if 'format' in data and 'duration' in data['format']:
            return float(data['format']['duration'])
    
    return 0.0


def validate_audio_file(file_path: Path) -> bool:
    """
    Validate if file is a supported audio/video format.
    
    Args:
        file_path: Path to file
    
    Returns:
        True if valid, False otherwise
    """
    supported_formats = {
        '.mp3', '.wav', '.m4a', '.flac', '.ogg', '.wma',
        '.mp4', '.avi', '.mov', '.mkv', '.mts', '.webm'
    }
    
    return file_path.suffix.lower() in supported_formats

