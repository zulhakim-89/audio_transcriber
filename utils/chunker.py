"""
Audio chunking utilities for large files.
Splits audio into smaller chunks for processing.
"""

import subprocess
from pathlib import Path
from typing import List
import math


def split_audio_file(input_path: Path, chunk_duration_seconds: int = 300) -> List[Path]:
    """
    Split audio file into chunks of specified duration.
    Outputs MP3 files to keep size well under the 25MB Whisper API limit.
    
    Args:
        input_path: Path to input audio file
        chunk_duration_seconds: Duration of each chunk in seconds (default 5 minutes)
    
    Returns:
        List of paths to chunk files
    """
    # Get audio duration using ffprobe
    cmd = [
        "ffprobe",
        "-v", "quiet",
        "-print_format", "json",
        "-show_format",
        str(input_path)
    ]
    
    import json
    result = subprocess.run(
        cmd,
        capture_output=True,
        text=True,
        creationflags=subprocess.CREATE_NO_WINDOW if hasattr(subprocess, 'CREATE_NO_WINDOW') else 0
    )
    
    if result.returncode == 0:
        data = json.loads(result.stdout)
        total_duration = float(data['format']['duration'])
    else:
        raise RuntimeError("Could not determine audio duration")
    
    # Calculate number of chunks needed
    num_chunks = math.ceil(total_duration / chunk_duration_seconds)
    
    if num_chunks == 1:
        # No need to split, but still convert to MP3 if file is large
        file_size_mb = input_path.stat().st_size / (1024 * 1024)
        if file_size_mb > 20:
            # Re-encode as MP3 to reduce size
            output_dir = input_path.parent / "chunks"
            output_dir.mkdir(exist_ok=True)
            mp3_path = output_dir / f"{input_path.stem}_full.mp3"
            cmd = [
                "ffmpeg", "-y",
                "-i", str(input_path),
                "-acodec", "libmp3lame",
                "-ab", "64k",
                "-ar", "16000",
                "-ac", "1",
                str(mp3_path)
            ]
            subprocess.run(
                cmd, check=True,
                stdout=subprocess.PIPE, stderr=subprocess.PIPE,
                creationflags=subprocess.CREATE_NO_WINDOW if hasattr(subprocess, 'CREATE_NO_WINDOW') else 0
            )
            return [mp3_path]
        return [input_path]
    
    # Create chunks as MP3 (much smaller than WAV)
    chunk_files = []
    output_dir = input_path.parent / "chunks"
    output_dir.mkdir(exist_ok=True)
    
    for i in range(num_chunks):
        start_time = i * chunk_duration_seconds
        chunk_path = output_dir / f"{input_path.stem}_chunk_{i:03d}.mp3"
        
        cmd = [
            "ffmpeg",
            "-y",
            "-i", str(input_path),
            "-ss", str(start_time),
            "-t", str(chunk_duration_seconds),
            "-acodec", "libmp3lame",
            "-ab", "64k",
            "-ar", "16000",
            "-ac", "1",
            str(chunk_path)
        ]
        
        subprocess.run(
            cmd,
            check=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            creationflags=subprocess.CREATE_NO_WINDOW if hasattr(subprocess, 'CREATE_NO_WINDOW') else 0
        )
        
        # Validate chunk - skip if empty or corrupted
        chunk_size = chunk_path.stat().st_size
        if chunk_size < 1024:  # Less than 1KB = likely empty/corrupt
            print(f"⚠️ Skipping chunk {i}: file too small ({chunk_size} bytes)")
            chunk_path.unlink()
            continue
        if chunk_size > 24 * 1024 * 1024:  # Over 24MB
            print(f"⚠️ Chunk {i} is too large ({chunk_size / 1024 / 1024:.1f}MB), this shouldn't happen with MP3")
        
        chunk_files.append(chunk_path)
    
    if not chunk_files:
        raise RuntimeError("All audio chunks were empty or corrupted. The source audio may be invalid.")
    
    return chunk_files

