"""
Speaker diarization utilities using Pyannote Audio.
Identifies and labels different speakers in audio.
"""

from pathlib import Path
from typing import List, Dict, Optional
import torch


class SpeakerDiarizer:
    """Speaker diarization using Pyannote Audio."""
    
    def __init__(self, hf_token: str):
        """
        Initialize diarizer with HuggingFace token.
        
        Args:
            hf_token: HuggingFace API token
        """
        self.hf_token = hf_token
        self.pipeline = None
    
    def load_model(self):
        """Load the diarization pipeline (lazy loading)."""
        if self.pipeline is None:
            try:
                from pyannote.audio import Pipeline
                
                # Fix for PyTorch 2.6+ weights_only security change
                # Add required classes to safe globals for model loading
                import torch.serialization
                try:
                    from torch.torch_version import TorchVersion
                    torch.serialization.add_safe_globals([TorchVersion])
                except (ImportError, AttributeError):
                    pass  # Older PyTorch versions don't need this
                
                # Load pretrained pipeline
                self.pipeline = Pipeline.from_pretrained(
                    "pyannote/speaker-diarization-3.1",
                    token=self.hf_token
                )
                
                # Use GPU if available
                if torch.cuda.is_available():
                    self.pipeline.to(torch.device("cuda"))
                    
            except Exception as e:
                raise RuntimeError(f"Failed to load diarization model: {str(e)}")
    
    def diarize(self, audio_path: Path, num_speakers: Optional[int] = None) -> List[Dict]:
        """
        Perform speaker diarization on audio file.
        
        Args:
            audio_path: Path to audio file
            num_speakers: Expected number of speakers (None for auto-detect)
        
        Returns:
            List of dicts with 'start', 'end', 'speaker' keys
        """
        self.load_model()
        
        # Run diarization
        if num_speakers:
            diarization = self.pipeline(str(audio_path), num_speakers=num_speakers)
        else:
            diarization = self.pipeline(str(audio_path))
        
        # Convert to list of segments
        segments = []
        for turn, _, speaker in diarization.itertracks(yield_label=True):
            segments.append({
                'start': turn.start,
                'end': turn.end,
                'speaker': speaker
            })
        
        return segments


def align_transcription_with_speakers(
    transcription_segments: List[Dict],
    diarization_segments: List[Dict]
) -> List[Dict]:
    """
    Align transcription segments with speaker labels.
    
    Args:
        transcription_segments: List of transcription segments with 'start', 'end', 'text'
        diarization_segments: List of diarization segments with 'start', 'end', 'speaker'
    
    Returns:
        List of segments with added 'speaker' field
    """
    aligned = []
    
    for trans_seg in transcription_segments:
        trans_start = trans_seg['start']
        trans_end = trans_seg['end']
        trans_mid = (trans_start + trans_end) / 2
        
        # Find overlapping speaker segment (using midpoint for robustness)
        best_speaker = None
        best_overlap = 0
        
        for diar_seg in diarization_segments:
            diar_start = diar_seg['start']
            diar_end = diar_seg['end']
            
            # Calculate overlap
            overlap_start = max(trans_start, diar_start)
            overlap_end = min(trans_end, diar_end)
            overlap = max(0, overlap_end - overlap_start)
            
            if overlap > best_overlap:
                best_overlap = overlap
                best_speaker = diar_seg['speaker']
        
        # Add speaker label to segment
        segment = trans_seg.copy()
        if best_speaker:
            segment['speaker'] = best_speaker
        else:
            segment['speaker'] = 'Unknown'
        
        aligned.append(segment)
    
    return aligned


def format_speaker_label(speaker: str) -> str:
    """
    Format speaker label for display.
    
    Args:
        speaker: Raw speaker label (e.g., 'SPEAKER_00')
    
    Returns:
        Formatted label (e.g., 'Speaker 1')
    """
    if speaker == 'Unknown':
        return speaker
    
    # Extract number from SPEAKER_XX format
    try:
        if speaker.startswith('SPEAKER_'):
            num = int(speaker.split('_')[1]) + 1
            return f"Speaker {num}"
    except:
        pass
    
    return speaker
