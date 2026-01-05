"""
Export utilities for transcription formats.
Handles SRT and TXT file generation.
"""

from pathlib import Path
from typing import List, Dict
from datetime import timedelta


def format_timestamp_srt(seconds: float) -> str:
    """
    Format seconds to SRT timestamp format (HH:MM:SS,mmm).
    
    Args:
        seconds: Time in seconds
    
    Returns:
        Formatted timestamp string
    """
    td = timedelta(seconds=seconds)
    total_ms = int(td.total_seconds() * 1000)
    hours = total_ms // 3_600_000
    minutes = (total_ms % 3_600_000) // 60_000
    secs = (total_ms % 60_000) // 1000
    milliseconds = total_ms % 1000
    
    return f"{hours:02}:{minutes:02}:{secs:02},{milliseconds:03}"


def export_srt(segments: List[Dict], output_path: Path) -> Path:
    """
    Export segments to SRT subtitle format.
    
    Args:
        segments: List of dicts with 'start', 'end', 'text' keys
        output_path: Path to save SRT file
    
    Returns:
        Path to saved SRT file
    """
    lines = []
    
    for idx, segment in enumerate(segments, start=1):
        start_time = format_timestamp_srt(segment['start'])
        end_time = format_timestamp_srt(segment['end'])
        text = segment['text'].strip()
        
        if not text:
            continue
        
        lines.append(str(idx))
        lines.append(f"{start_time} --> {end_time}")
        lines.append(text)
        lines.append("")  # Empty line between subtitles
    
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text("\n".join(lines), encoding="utf-8")
    
    return output_path


def export_txt(segments: List[Dict], output_path: Path, include_timestamps: bool = False) -> Path:
    """
    Export segments to plain text format.
    
    Args:
        segments: List of dicts with 'start', 'end', 'text' keys
        output_path: Path to save TXT file
        include_timestamps: Whether to include timestamps in output
    
    Returns:
        Path to saved TXT file
    """
    lines = []
    
    for segment in segments:
        text = segment['text'].strip()
        if not text:
            continue
        
        if include_timestamps:
            start_time = format_timestamp_srt(segment['start'])
            lines.append(f"[{start_time}] {text}")
        else:
            lines.append(text)
    
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text("\n".join(lines), encoding="utf-8")
    
    return output_path


def export_full_text(text: str, output_path: Path) -> Path:
    """
    Export full transcription text without segmentation.
    
    Args:
        text: Full transcription text
        output_path: Path to save TXT file
    
    Returns:
        Path to saved TXT file
    """
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(text, encoding="utf-8")
    
    return output_path
