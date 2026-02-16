"""
Transcription utilities using OpenAI Whisper API.
Handles transcription with timestamps for multiple languages.
"""

from pathlib import Path
from typing import List, Dict, Optional
import math
import time
from openai import OpenAI, APIStatusError


class WhisperTranscriber:
    """Transcriber using OpenAI Whisper API."""
    
    def __init__(self, api_key: str):
        """
        Initialize transcriber with API key.
        
        Args:
            api_key: OpenAI API key
        """
        self.client = OpenAI(
            api_key=api_key,
            timeout=600.0,  # 10-minute timeout for very large files
            max_retries=3   # Retry up to 3 times on failure
        )
    
    def __del__(self):
        """Cleanup when transcriber is destroyed."""
        try:
            if hasattr(self, 'client'):
                self.client.close()
        except:
            pass
    
    def transcribe(
        self, 
        audio_path: Path, 
        language: Optional[str] = None,
        prompt: Optional[str] = None
    ) -> Dict:
        """
        Transcribe audio file using Whisper API.
        
        Args:
            audio_path: Path to audio file
            language: Language code (e.g., 'en', 'ms', 'zh') or None for auto-detection
            prompt: Optional prompt to guide transcription style (e.g., for mixed languages)
        
        Returns:
            Dict with 'text' and 'segments' containing transcription and timestamps
        
        Raises:
            ValueError: If file is too large (>25MB)
        """
        # Check file size (Whisper API limit is 25MB)
        file_size_mb = audio_path.stat().st_size / (1024 * 1024)
        if file_size_mb > 24:  # Strict limit
            raise ValueError(
                f"Audio file is {file_size_mb:.1f}MB. "
                f"Whisper API has a 25MB limit. "
                f"The file will need to be chunked into smaller segments."
            )
        
        if file_size_mb > 20:
            print(f"⚠️ Large file: {file_size_mb:.1f}MB - upload may take several minutes...")
        
        start_time = time.time()
        print(f"📤 [Start] Uploading {file_size_mb:.1f}MB to Whisper API at {time.strftime('%H:%M:%S')}...")
        
        with open(audio_path, "rb") as audio_file:
            # Use verbose_json to get detailed timestamps
            # Build API call parameters
            api_params = {
                "model": "whisper-1",
                "file": audio_file,
                "response_format": "verbose_json"
            }
            
            # Add optional parameters
            if language:
                api_params["language"] = language
            if prompt:
                api_params["prompt"] = prompt
            
            try:
                response = self.client.audio.transcriptions.create(**api_params)
            except APIStatusError as e:
                print(f"❌ API Error {e.status_code}: {e.message}")
                print(f"   File: {audio_path.name} ({file_size_mb:.1f}MB)")
                raise
        
        elapsed = time.time() - start_time
        print(f"✅ [Complete] Transcription received from API in {elapsed:.1f}s")
        
        # Extract segments with timestamps and confidence
        segments = []
        total_logprob = 0.0
        count_segments = 0
        
        if hasattr(response, 'segments') and response.segments:
            for seg in response.segments:
                # Segments are objects, not dicts - use attribute access
                avg_logprob = getattr(seg, 'avg_logprob', -1.0)
                confidence = math.exp(avg_logprob) if avg_logprob != -1.0 else 0.0
                
                # track for average
                if avg_logprob != -1.0:
                    total_logprob += avg_logprob
                    count_segments += 1

                segments.append({
                    'start': getattr(seg, 'start', 0.0),
                    'end': getattr(seg, 'end', 0.0),
                    'text': getattr(seg, 'text', '').strip(),
                    'confidence': confidence
                })
        else:
            # Fallback: create single segment if no segments returned
            segments = [{
                'start': 0.0,
                'end': 0.0,
                'text': response.text,
                'confidence': 0.0
            }]
        
        # Calculate overall confidence
        avg_confidence = 0.0
        if count_segments > 0:
            avg_confidence = math.exp(total_logprob / count_segments)

        return {
            'text': response.text,
            'language': getattr(response, 'language', language or 'unknown'),
            'confidence': avg_confidence,
            'segments': segments
        }
    
    def transcribe_chunked(
        self,
        audio_path: Path,
        chunk_paths: List[Path],
        chunk_durations: List[float],
        language: Optional[str] = None,
        prompt: Optional[str] = None,
        progress_callback=None
    ) -> Dict:
        """
        Transcribe multiple audio chunks and merge results.
        
        Args:
            audio_path: Original audio file path (for reference)
            chunk_paths: List of chunk file paths
            chunk_durations: Duration of each chunk for time offset calculation
            language: Language code or None for auto-detect
            prompt: Optional prompt to guide transcription style
            progress_callback: Optional callback function for progress updates
        
        Returns:
            Combined transcription result
        """
        results = []
        time_offset = 0.0
        
        for i, chunk_path in enumerate(chunk_paths, 1):
            if progress_callback:
                progress_callback(f"📝 Transcribing chunk {i}/{len(chunk_paths)}...")
            
            print(f"Transcribing chunk {i}/{len(chunk_paths)}: {chunk_path.name}")
            
            # Transcribe this chunk with retry logic for transient API errors
            max_retries = 5
            chunk_result = None
            for attempt in range(1, max_retries + 1):
                try:
                    chunk_result = self.transcribe(chunk_path, language=language, prompt=prompt)
                    break  # Success, exit retry loop
                except APIStatusError as e:
                    if e.status_code >= 500 and attempt < max_retries:
                        wait_time = 2 ** attempt  # 2, 4, 8, 16, 32 seconds
                        print(f"⚠️ Server error on chunk {i} (attempt {attempt}/{max_retries}). "
                              f"Retrying in {wait_time}s...")
                        if progress_callback:
                            progress_callback(
                                f"⚠️ API error on chunk {i}, retrying in {wait_time}s "
                                f"(attempt {attempt}/{max_retries})..."
                            )
                        time.sleep(wait_time)
                    else:
                        raise  # Re-raise for non-500 errors or final attempt
            
            if chunk_result is None:
                raise RuntimeError(f"Failed to transcribe chunk {i} after {max_retries} attempts")
            
            # Adjust timestamps with cumulative offset
            for seg in chunk_result['segments']:
                seg['start'] += time_offset
                seg['end'] += time_offset
            
            results.append(chunk_result)
            
            # Update time offset for next chunk
            if i < len(chunk_durations):
                time_offset += chunk_durations[i-1]
        
        # Merge all results
        all_segments = []
        all_text_parts = []
        total_confidence = 0.0
        
        for result in results:
            all_segments.extend(result['segments'])
            all_text_parts.append(result['text'])
            total_confidence += result.get('confidence', 0.0)
        
        # Average confidence across chunks
        avg_confidence = total_confidence / len(results) if results else 0.0
        
        return {
            'text': ' '.join(all_text_parts),
            'language': results[0]['language'] if results else 'unknown',
            'confidence': avg_confidence,
            'segments': all_segments
        }


# Language mapping for dropdown
SUPPORTED_LANGUAGES = {
    'Auto-detect': None,
    'English': 'en',
    'Malay': 'ms',
    'Chinese (Mandarin)': 'zh',
    'Tamil': 'ta',
    'Spanish': 'es',
    'French': 'fr',
    'German': 'de',
    'Italian': 'it',
    'Portuguese': 'pt',
    'Russian': 'ru',
    'Japanese': 'ja',
    'Korean': 'ko',
    'Arabic': 'ar',
    'Hindi': 'hi',
    'Bengali': 'bn',
    'Turkish': 'tr',
    'Vietnamese': 'vi',
    'Thai': 'th',
    'Indonesian': 'id',
    'Dutch': 'nl',
    'Polish': 'pl',
    'Swedish': 'sv',
    'Norwegian': 'no',
    'Danish': 'da',
    'Finnish': 'fi',
    'Greek': 'el',
    'Hebrew': 'he',
    'Romanian': 'ro',
    'Hungarian': 'hu',
    'Czech': 'cs',
    'Ukrainian': 'uk',
}
