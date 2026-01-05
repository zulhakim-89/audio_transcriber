"""
Seamless M4T Transcriber - Meta's multilingual speech-to-text model.
Better at code-switching and mixed-language transcription than Whisper.
"""

import time
from pathlib import Path
from typing import Dict, Optional
import torch


class SeamlessTranscriber:
    """Speech-to-text using Meta's Seamless M4T v2 model."""
    
    # Use medium model for better memory efficiency on CPU
    MODEL_NAME = "facebook/hf-seamless-m4t-medium"
    
    def __init__(self):
        """Initialize the transcriber (lazy loading)."""
        self.pipe = None
        self.device = "cuda" if torch.cuda.is_available() else "cpu"
        print(f"🔧 SeamlessTranscriber will use: {self.device}")
    
    def load_model(self):
        """Load the model pipeline (downloads on first use ~5GB)."""
        if self.pipe is None:
            print(f"📥 Loading Seamless M4T model pipeline... (first time may take a few minutes)")
            start = time.time()
            
            from transformers import pipeline
            
            # Initialize pipeline with chunking enabled
            # chunk_length_s=30 processes 30s at a time to avoid OOM
            self.pipe = pipeline(
                "automatic-speech-recognition",
                model=self.MODEL_NAME,
                device=0 if self.device == "cuda" else -1,
                chunk_length_s=30,
            )
            
            elapsed = time.time() - start
            print(f"✅ Model loaded in {elapsed:.1f}s")
    
    def transcribe(
        self, 
        audio_path: Path, 
        language: Optional[str] = None,
        prompt: Optional[str] = None
    ) -> Dict:
        """
        Transcribe audio file using Seamless M4T pipeline.
        """
        self.load_model()
        
        start_time = time.time()
        print(f"📤 [Start] Processing audio with Seamless M4T at {time.strftime('%H:%M:%S')}...")
        
        # Map common language codes to Seamless format
        lang_map = {
            'en': 'eng', 'ms': 'zsm', 'zh': 'cmn', 'ta': 'tam',
            'id': 'ind', 'th': 'tha', 'vi': 'vie', 'ja': 'jpn',
            'ko': 'kor', 'ar': 'arb', 'hi': 'hin', 'es': 'spa',
            'fr': 'fra', 'de': 'deu', 'it': 'ita', 'pt': 'por',
            None: 'eng'
        }
        tgt_lang = lang_map.get(language, language if language else 'eng')
        
        # Run transcription pipeline
        # return_timestamps=True might not be fully supported by all seq2seq models in pipeline yet,
        # but modern versions often approximate it.
        try:
            result = self.pipe(
                str(audio_path), 
                generate_kwargs={
                    "tgt_lang": tgt_lang,
                    "repetition_penalty": 1.1,  # Discourage repetition
                    "no_repeat_ngram_size": 0   # Don't block n-grams hard, let penalty work
                },
                return_timestamps=True
            )
        except Exception as e:
            print(f"⚠️ Pipeline error: {e}. Retrying without timestamps...")
            result = self.pipe(
                str(audio_path), 
                generate_kwargs={
                    "tgt_lang": tgt_lang,
                    "repetition_penalty": 1.1,
                    "no_repeat_ngram_size": 0
                },
                return_timestamps=False
            )
        
        elapsed = time.time() - start_time
        print(f"✅ [Complete] Transcription received in {elapsed:.1f}s")
        
        text = result.get('text', '')
        
        # Extract chunks if available, otherwise create one big chunk
        raw_chunks = result.get('chunks', [])
        segments = []
        
        if raw_chunks:
            for chunk in raw_chunks:
                # Some pipelines return (start, end) tuple for timestamp
                timestamp = chunk.get('timestamp')
                start, end = (0.0, 0.0)
                if isinstance(timestamp, (list, tuple)) and len(timestamp) == 2:
                    start, end = timestamp
                
                segments.append({
                    'start': start,
                    'end': end,
                    'text': chunk.get('text', '').strip(),
                    'confidence': 0.95
                })
        else:
            # Fallback if no chunks
            segments = [{
                'start': 0.0,
                'end': 0.0, # Unknown
                'text': text.strip(),
                'confidence': 0.95
            }]
        
        return {
            'text': text.strip(),
            'segments': segments,
            'language': tgt_lang,
            'confidence': 0.95
        }
    
    def transcribe_chunked(
        self,
        audio_path: Path,
        chunk_paths: list,
        chunk_durations: list,
        language: Optional[str] = None,
        prompt: Optional[str] = None,
        progress_callback=None
    ) -> Dict:
        """
        Transcribe multiple audio chunks.
        Note: The pipeline already handles chunking effectively, so we could just call transcribe() 
        on the whole file. But app.py splits files > 15MB. 
        We'll respect the external chunking for progress bar updates.
        """
        results = []
        time_offset = 0.0
        
        for i, chunk_path in enumerate(chunk_paths, 1):
            if progress_callback:
                progress_callback(f"📝 Transcribing chunk {i}/{len(chunk_paths)} with Seamless M4T...")
            
            print(f"Transcribing chunk {i}/{len(chunk_paths)}: {chunk_path.name}")
            
            chunk_result = self.transcribe(chunk_path, language=language)
            
            # Adjust timestamps
            for seg in chunk_result['segments']:
                if seg['start'] is not None: seg['start'] += time_offset
                if seg['end'] is not None: seg['end'] += time_offset
            
            results.append(chunk_result)
            
            if i < len(chunk_durations):
                time_offset += chunk_durations[i-1]
        
        # Merge
        all_segments = []
        all_text_parts = []
        
        for result in results:
            all_segments.extend(result['segments'])
            all_text_parts.append(result['text'])
        
        return {
            'text': ' '.join(all_text_parts),
            'segments': all_segments,
            'language': results[0].get('language', 'unknown') if results else 'unknown',
            'confidence': 0.95
        }
