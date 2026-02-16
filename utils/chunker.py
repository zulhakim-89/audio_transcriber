"""
Audio chunking utilities for large files.
Splits audio into smaller chunks for processing.
"""

import subprocess
from pathlib import Path
from typing import List
import math


def split_audio_file(input_path: Path, chunk_duration_seconds: int = 600) -> List[Path]:
    """
    Split audio file into chunks of specified duration.
    
    Args:
        input_path: Path to input audio file
        chunk_duration_seconds: Duration of each chunk in seconds (default 10 minutes)
    
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
        # No need to split
        return [input_path]
    
    # Create chunks
    chunk_files = []
    output_dir = input_path.parent / "chunks"
    output_dir.mkdir(exist_ok=True)
    
    for i in range(num_chunks):
        start_time = i * chunk_duration_seconds
        chunk_path = output_dir / f"{input_path.stem}_chunk_{i:03d}.wav"
        
        cmd = [
            "ffmpeg",
            "-y",
            "-i", str(input_path),
            "-ss", str(start_time),
            "-t", str(chunk_duration_seconds),
            "-acodec", "pcm_s16le",
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
        
        chunk_files.append(chunk_path)
    
    return chunk_files


def merge_transcription_results(results: List[dict], time_offsets: List[float]) -> dict:
    """
    Merge multiple transcription results into one.
    
    Args:
        results: List of transcription result dicts
        time_offsets: Time offset in seconds for each chunk
    
    Returns:
        Combined transcription result
    """
    merged_text = []
    merged_segments = []
    
    for result, offset in zip(results, time_offsets):
        merged_text.append(result['text'])
        
        # Adjust segment timestamps with offset
        for seg in result['segments']:
            merged_segments.append({
                'start': seg['start'] + offset,
                'end': seg['end'] + offset,
                'text': seg['text']
            })
    
    return {
        'text': ' '.join(merged_text),
        'language': results[0].get('language', 'unknown') if results else 'unknown',
        'segments': merged_segments
    }
