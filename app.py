"""
Multilingual Audio Transcription App
A Streamlit application for transcribing audio/video files in 99+ languages using OpenAI Whisper.
"""

import streamlit as st
import os
import tempfile
from pathlib import Path
from dotenv import load_dotenv

from utils.audio_processor import convert_to_wav, get_audio_duration, validate_audio_file
from utils.transcriber import WhisperTranscriber, SUPPORTED_LANGUAGES
from utils.exporter import export_srt, export_txt, export_full_text


# Load environment variables
load_dotenv()

# Page configuration
st.set_page_config(
    page_title="Multilingual Audio Transcriber",
    page_icon="🎙️",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS for modern aesthetics
st.markdown("""
<style>
    /* Global styles */
    .main {
        background: linear-gradient(135deg, #0f172a 0%, #1e293b 100%);
    }
    
    /* Elegant Header */
    .main-header {
        background: rgba(255, 255, 255, 0.05);
        backdrop-filter: blur(20px);
        border: 1px solid rgba(255, 255, 255, 0.1);
        padding: 3rem 2rem;
        border-radius: 1.5rem;
        margin-bottom: 3rem;
        text-align: center;
        box-shadow: 0 20px 40px rgba(0, 0, 0, 0.2);
    }
    
    .main-header h1 {
        background: linear-gradient(135deg, #6366f1 0%, #a855f7 100%);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        font-size: 3.5rem;
        font-weight: 800;
        margin-bottom: 1rem;
        letter-spacing: -0.05em;
    }
    
    .main-header p {
        color: #94a3b8;
        font-size: 1.2rem;
        font-weight: 400;
    }
    
    /* Modern Cards */
    .stat-box {
        background: rgba(30, 41, 59, 0.7);
        backdrop-filter: blur(10px);
        border: 1px solid rgba(148, 163, 184, 0.1);
        border-radius: 1rem;
        padding: 1.5rem;
        text-align: center;
        transition: transform 0.2s ease;
    }
    
    .stat-box:hover {
        transform: translateY(-5px);
        border-color: rgba(99, 102, 241, 0.5);
    }
    
    .stat-value {
        font-size: 1.8rem;
        font-weight: 700;
        color: #f8fafc;
        margin-bottom: 0.25rem;
    }
    
    .stat-label {
        font-size: 0.875rem;
        color: #94a3b8;
        text-transform: uppercase;
        letter-spacing: 0.05em;
    }
    
    /* Upload Area Polish */
    [data-testid="stFileUploader"] {
        background: rgba(30, 41, 59, 0.4);
        border: 2px dashed rgba(99, 102, 241, 0.3);
        border-radius: 1rem;
        padding: 3rem 2rem;
        transition: border-color 0.3s ease;
    }
    
    [data-testid="stFileUploader"]:hover {
        border-color: #6366f1;
        background: rgba(99, 102, 241, 0.05);
    }
    
    /* Primary Button */
    .stButton > button {
        background: linear-gradient(135deg, #4f46e5 0%, #7c3aed 100%);
        color: white;
        border: none;
        padding: 0.75rem 2rem;
        font-weight: 600;
        border-radius: 0.75rem;
        box-shadow: 0 4px 15px rgba(79, 70, 229, 0.4);
        transition: all 0.3s ease;
        text-transform: uppercase;
        letter-spacing: 0.05em;
        font-size: 0.9rem;
    }
    
    .stButton > button:hover {
        transform: translateY(-2px);
        box-shadow: 0 8px 25px rgba(79, 70, 229, 0.5);
    }
    
    /* Tabs Styling */
    .stTabs [data-baseweb="tab-list"] {
        gap: 2rem;
        background-color: transparent;
    }

    .stTabs [data-baseweb="tab"] {
        height: 3rem;
        white-space: pre-wrap;
        background-color: transparent;
        border-radius: 0.5rem;
        color: #94a3b8;
        font-weight: 600;
        padding: 0 1rem;
    }

    .stTabs [aria-selected="true"] {
        color: #6366f1;
        background-color: rgba(99, 102, 241, 0.1);
        border-bottom: 2px solid #6366f1;
    }
    
    /* Download Buttons */
    .stDownloadButton > button {
        background: rgba(16, 185, 129, 0.1);
        color: #10b981;
        border: 1px solid rgba(16, 185, 129, 0.3);
        border-radius: 0.75rem;
        padding: 0.6rem 1.5rem;
        font-weight: 600;
        transition: all 0.3s ease;
    }
    
    .stDownloadButton > button:hover {
        background: #10b981;
        color: white;
        transform: translateY(-2px);
        box-shadow: 0 4px 12px rgba(16, 185, 129, 0.3);
    }

    /* Expander Polish */
    .streamlit-expanderHeader {
        background-color: rgba(30, 41, 59, 0.4);
        border-radius: 0.5rem;
        color: #e2e8f0;
    }
</style>
""", unsafe_allow_html=True)


def main():
    """Main application function."""
    
    # Header
    st.markdown("""
    <div class="main-header">
        <h1>🎙️ Multilingual Audio Transcriber</h1>
        <p>Transform audio and video into text in 99+ languages with AI-powered transcription</p>
    </div>
    """, unsafe_allow_html=True)
    
    # Sidebar
    with st.sidebar:
        st.header("⚙️ Settings")
        
        # Model selection
        model_choice = st.radio(
            "Transcription Model",
            options=["Whisper (OpenAI API)", "Seamless M4T (Local GPU)"],
            index=0,
            help="Whisper: Fast, requires API key. Seamless: Better for mixed languages, runs locally."
        )
        
        # API Key input (only for Whisper)
        if model_choice == "Whisper (OpenAI API)":
            api_key = st.text_input(
                "OpenAI API Key",
                type="password",
                value=os.getenv("OPENAI_API_KEY", ""),
                help="Enter your OpenAI API key. Get one at https://platform.openai.com/api-keys"
            )
        else:
            api_key = None
            st.info("💻 Seamless M4T runs locally on your GPU. No API key needed.")
        
        # Language selection
        language_name = st.selectbox(
            "Language",
            options=list(SUPPORTED_LANGUAGES.keys()),
            help="Select the language or choose Auto-detect"
        )
        language_code = SUPPORTED_LANGUAGES[language_name]
        
        # Advanced Settings
        with st.expander("⚙️ Advanced Settings"):
            # Speaker diarization option
            enable_diarization = st.checkbox(
                "🎭 Enable Speaker Diarization",
                value=False,
                help="Identify different speakers (adds ~30-60s processing time)"
            )
            
            if enable_diarization:
                num_speakers = st.number_input(
                    "Expected number of speakers",
                    min_value=2,
                    max_value=10,
                    value=2,
                    help="Leave at auto to detect automatically"
                )
                st.info("💡 Auto-detection works best for 2-4 speakers")
            else:
                num_speakers = None
            
            st.markdown("---")
            
            # Mixed Language Mode
            enable_mixed_language = st.checkbox(
                "🌐 Mixed Language Mode",
                value=False,
                help="Enable for audio with code-switching (e.g., Malay + English + Chinese)"
            )
            
            # Default multilingual prompt
            default_prompt = "This is a multilingual conversation with frequent code-switching between languages. Transcribe exactly what is spoken in the original languages. Do not translate. Preserve all language switches."
            
            if enable_mixed_language:
                st.info("💡 Mixed language mode enabled.")
                custom_prompt = st.text_area(
                    "Transcription Prompt",
                    value=default_prompt,
                    height=100,
                    help="Guide the transcription style. Customize if needed."
                )
            else:
                custom_prompt = None
        
        st.markdown("---")
        
        # Information
        st.markdown("""
        ### 📋 Supported Formats
        **Audio:** MP3, WAV, M4A, FLAC, OGG, WMA  
        **Video:** MP4, AVI, MOV, MKV, MTS, WEBM
        
        ### 🌍 Languages
        Supports 99+ languages including:
        - English, Malay, Chinese, Tamil
        - Spanish, French, German, Italian
        - Arabic, Hindi, Japanese, Korean
        - And many more...
        
        ### 💡 Tips
        - Max file size: 200 MB
        - Longer files take more time
        - Clear audio = better results
        - **Refresh page** between uploads if processing slows down
        """)
        
        st.markdown("---")
        
        # Add reset button
        if st.button("🔄 Clear Session", help="Reset the app if it's running slow"):
            st.cache_data.clear()
            st.cache_resource.clear()
            import gc
            gc.collect()
            st.success("Session cleared! Page will reload...")
            st.rerun()
    
    # Main content
    if model_choice == "Whisper (OpenAI API)" and not api_key:
        st.warning("⚠️ Please enter your OpenAI API key in the sidebar to get started.")
        st.info("""
        **Don't have an API key?**  
        1. Go to [OpenAI Platform](https://platform.openai.com/api-keys)
        2. Sign up or log in
        3. Create a new API key
        4. Paste it in the sidebar
        """)
        return
    
    # File upload
    st.markdown("### 📤 Upload Audio/Video File")
    uploaded_file = st.file_uploader(
        "Choose a file",
        type=['mp3', 'wav', 'm4a', 'flac', 'ogg', 'wma', 'mp4', 'avi', 'mov', 'mkv', 'mts', 'webm'],
        help="Upload an audio or video file to transcribe"
    )
    
    if uploaded_file:
        # Display file info
        file_size_mb = uploaded_file.size / (1024 * 1024)
        
        col1, col2, col3 = st.columns(3)
        with col1:
            st.markdown(f"""
            <div class="stat-box">
                <div class="stat-value">📄</div>
                <div class="stat-label">{uploaded_file.name}</div>
            </div>
            """, unsafe_allow_html=True)
        
        with col2:
            st.markdown(f"""
            <div class="stat-box">
                <div class="stat-value">{file_size_mb:.1f}</div>
                <div class="stat-label">MB</div>
            </div>
            """, unsafe_allow_html=True)
        
        with col3:
            st.markdown(f"""
            <div class="stat-box">
                <div class="stat-value">🌐</div>
                <div class="stat-label">{language_name}</div>
            </div>
            """, unsafe_allow_html=True)
        
        # Warn about large files
        if file_size_mb > 15:
            st.warning(f"⚠️ Large file detected ({file_size_mb:.1f}MB). Processing may take 5-10 minutes. Please be patient!")
        
        # Transcribe button
        if st.button("🚀 Start Transcription", use_container_width=True):
            process_transcription(
                uploaded_file, 
                api_key, 
                language_code, 
                language_name,
                model_choice=model_choice,
                enable_diarization=enable_diarization,
                num_speakers=num_speakers if enable_diarization else None,
                prompt=custom_prompt
            )


def process_transcription(
    uploaded_file, 
    api_key: str, 
    language_code: str, 
    language_name: str,
    model_choice: str = "Whisper (OpenAI API)",
    enable_diarization: bool = False,
    num_speakers: int = None,
    prompt: str = None
):
    """
    Process the uploaded file and perform transcription.
    
    Args:
        uploaded_file: Streamlit uploaded file object
        api_key: OpenAI API key (only for Whisper)
        language_code: Language code for transcription
        language_name: Human-readable language name
        model_choice: Which transcription model to use
        enable_diarization: Whether to perform speaker diarization
        num_speakers: Expected number of speakers (None for auto-detect)
        prompt: Optional prompt to guide transcription style
    """
    # Force garbage collection to free memory from previous runs
    import gc
    gc.collect()
    
    # Get HuggingFace token if diarization is enabled
    hf_token = None
    if enable_diarization:
        hf_token = os.getenv("HUGGINGFACE_TOKEN", "")
        if not hf_token:
            st.error("❌ HuggingFace token not found! Please add HUGGINGFACE_TOKEN to your .env file")
            return
    
    try:
        with st.spinner("🔄 Processing your file..."):
            # Create temp directory
            with tempfile.TemporaryDirectory() as temp_dir:
                temp_path = Path(temp_dir)
                
                # Save uploaded file
                input_file = temp_path / uploaded_file.name
                input_file.write_bytes(uploaded_file.read())
                
                # Progress tracking
                progress_bar = st.progress(0)
                status_text = st.empty()
                
                # Step 1: Convert to WAV (with normalization)
                status_text.text("🔊 Converting and normalizing audio...")
                progress_bar.progress(30)
                
                wav_file = temp_path / "audio.wav"
                convert_to_wav(input_file, wav_file)
                duration = get_audio_duration(wav_file)
                
                # Step 2: Check file size and decide on chunking
                file_size_mb = wav_file.stat().st_size / (1024 * 1024)
                
                # Use appropriate transcriber based on model choice
                use_seamless = model_choice == "Seamless M4T (Local GPU)"
                
                if use_seamless:
                    status_text.text("🤖 Loading Seamless M4T model (first time may take a few minutes)...")
                    from utils.seamless_transcriber import SeamlessTranscriber
                    transcriber = SeamlessTranscriber()
                else:
                    transcriber = WhisperTranscriber(api_key)
                
                # If file is over 15MB, use chunking
                if file_size_mb > 15:
                    status_text.text(f"⚠️ Large file ({file_size_mb:.1f}MB) - splitting into chunks...")
                    progress_bar.progress(35)
                    
                    from utils.chunker import split_audio_file
                    
                    # Split into 8-minute chunks
                    chunk_paths = split_audio_file(wav_file, chunk_duration_seconds=480)
                    
                    # Get duration of each chunk
                    chunk_durations = [get_audio_duration(chunk) for chunk in chunk_paths]
                    
                    model_name = "Seamless M4T" if use_seamless else "Whisper"
                    status_text.text(f"📝 Transcribing {len(chunk_paths)} chunks with {model_name}...")
                    progress_bar.progress(40)
                    
                    def update_progress(msg):
                        status_text.text(msg)
                    
                    result = transcriber.transcribe_chunked(
                        wav_file,
                        chunk_paths,
                        chunk_durations,
                        language=language_code,
                        prompt=prompt,
                        progress_callback=update_progress
                    )
                    
                    # Clean up chunks
                    import shutil
                    if (wav_file.parent / "chunks").exists():
                        shutil.rmtree(wav_file.parent / "chunks")
                    
                    progress_bar.progress(80)
                else:
                    # Small file - direct transcription
                    model_name = "Seamless M4T" if use_seamless else "Whisper"
                    status_text.text(f"🎯 Transcribing {file_size_mb:.1f}MB file with {model_name}...")
                    progress_bar.progress(40)
                    
                    result = transcriber.transcribe(wav_file, language=language_code, prompt=prompt)
                    
                    progress_bar.progress(80)
                
                # Clean up transcriber
                del transcriber
                
                # Step 3: Speaker Diarization (if enabled)
                if enable_diarization:
                    status_text.text("🎭 Identifying speakers...")
                    progress_bar.progress(82)
                    
                    try:
                        from utils.diarizer import SpeakerDiarizer, align_transcription_with_speakers, format_speaker_label
                        
                        diarizer = SpeakerDiarizer(hf_token)
                        speaker_segments = diarizer.diarize(wav_file, num_speakers=num_speakers)
                        
                        # Align transcription with speaker labels
                        result['segments'] = align_transcription_with_speakers(
                            result['segments'],
                            speaker_segments
                        )
                        
                        # Format speaker labels
                        for seg in result['segments']:
                            if 'speaker' in seg:
                                seg['speaker'] = format_speaker_label(seg['speaker'])
                        
                        del diarizer
                        st.success(f"✅ Detected {len(set(seg.get('speaker', 'Unknown') for seg in result['segments']))} speakers!")
                        
                    except Exception as e:
                        st.warning(f"⚠️ Diarization failed: {str(e)}. Continuing without speaker labels...")
                        # Continue without diarization on error
                    
                    progress_bar.progress(85)
                
                # Step 4: Export files
                status_text.text("💾 Generating output files...")
                progress_bar.progress(90)
                
                # Export SRT
                srt_file = temp_path / "transcript.srt"
                export_srt(result['segments'], srt_file)
                
                # Export TXT
                txt_file = temp_path / "transcript.txt"
                export_txt(result['segments'], txt_file)
                
                # Export full text
                full_txt_file = temp_path / "transcript_full.txt"
                export_full_text(result['text'], full_txt_file)
                
                progress_bar.progress(100)
                status_text.text("✅ Transcription complete!")
                
                # Display results
                st.success("🎉 Transcription completed successfully!")
                
                col1, col2, col3, col4 = st.columns(4)
                with col1:
                    st.markdown(f"""
                    <div class="stat-box">
                        <div class="stat-value">{duration:.1f}s</div>
                        <div class="stat-label">Duration</div>
                    </div>
                    """, unsafe_allow_html=True)
                
                with col2:
                    st.markdown(f"""
                    <div class="stat-box">
                        <div class="stat-value">{len(result['segments'])}</div>
                        <div class="stat-label">Segments</div>
                    </div>
                    """, unsafe_allow_html=True)
                
                with col3:
                    detected_lang = result.get('language', 'unknown').upper()
                    st.markdown(f"""
                    <div class="stat-box">
                        <div class="stat-value">{detected_lang}</div>
                        <div class="stat-label">Language</div>
                    </div>
                    """, unsafe_allow_html=True)
                    
                with col4:
                    confidence = result.get('confidence', 0.0) * 100
                    conf_color = "#10b981" if confidence > 90 else "#f59e0b" if confidence > 80 else "#ef4444"
                    st.markdown(f"""
                    <div class="stat-box" style="border-color: {conf_color};">
                        <div class="stat-value" style="color: {conf_color};">{confidence:.1f}%</div>
                        <div class="stat-label">Confidence</div>
                    </div>
                    """, unsafe_allow_html=True)
                
                # Tabbed Interface
                tab_transcript, tab_segments, tab_verify = st.tabs([
                    "📝 Transcript", 
                    "📊 Segments & Analysis", 
                    "🎯 Verify Accuracy"
                ])
                
                # Tab 1: Transcript
                with tab_transcript:
                    st.markdown("### 📝 Full Transcript")
                    st.text_area(
                        "Transcript",
                        value=result['text'],
                        height=400,
                        label_visibility="collapsed"
                    )
                    
                    # Download buttons
                    st.markdown("### 💾 Download Files")
                    col1, col2, col3 = st.columns(3)
                    
                    with col1:
                        st.download_button(
                            label="📥 Download SRT",
                            data=srt_file.read_bytes(),
                            file_name=f"{Path(uploaded_file.name).stem}.srt",
                            mime="text/plain",
                            use_container_width=True
                        )
                    
                    with col2:
                        st.download_button(
                            label="📥 Download TXT (Segmented)",
                            data=txt_file.read_bytes(),
                            file_name=f"{Path(uploaded_file.name).stem}.txt",
                            mime="text/plain",
                            use_container_width=True
                        )
                    
                    with col3:
                        st.download_button(
                            label="📥 Download TXT (Full)",
                            data=full_txt_file.read_bytes(),
                            file_name=f"{Path(uploaded_file.name).stem}_full.txt",
                            mime="text/plain",
                            use_container_width=True
                        )

                # Tab 2: Segments
                with tab_segments:
                    st.markdown("### 📊 Detailed Segments")
                    st.info("ℹ️ View confidence scores and timestamps for each segment.")
                    
                    # Format segments for dataframe
                    import pandas as pd
                    
                    seg_data = []
                    for seg in result['segments']:
                        conf = seg.get('confidence', 0.0)
                        row = {
                            "Start": f"{seg['start']:.2f}s",
                            "End": f"{seg['end']:.2f}s",
                            "Text": seg['text'],
                            "Confidence": f"{conf*100:.1f}%",
                        }
                        if 'speaker' in seg:
                            row["Speaker"] = seg['speaker']
                        seg_data.append(row)
                    
                    if seg_data:
                        # Configure column configuration
                        column_config = {
                            "Text": st.column_config.TextColumn("Text", width="large"),
                            "Confidence": st.column_config.TextColumn("Confidence", help="Model confidence score")
                        }
                        
                        st.dataframe(
                            pd.DataFrame(seg_data), 
                            hide_index=True,
                            column_config=column_config
                        )

                # Tab 3: Verification
                with tab_verify:
                    st.markdown("### 🎯 Verify Accuracy")
                    st.info("ℹ️ Paste a correct reference text (ground truth) below to calculate the exact accuracy of the transcription.")
                    
                    ground_truth = st.text_area("Reference Text (Ground Truth)", height=300, help="Paste the correct transcript here to compare")
                    
                    if ground_truth and st.button("Calculate Accuracy", type="primary"):
                        import difflib
                        
                        # Normalize texts (simple normalization)
                        ref_text = ground_truth.strip()
                        hyp_text = result['text'].strip()
                        
                        # Calculate similarity ratio
                        matcher = difflib.SequenceMatcher(None, ref_text, hyp_text)
                        ratio = matcher.ratio()
                        accuracy_pct = ratio * 100
                        
                        # Display score
                        score_color = "#10b981" if accuracy_pct > 90 else "#f59e0b" if accuracy_pct > 80 else "#ef4444"
                        
                        col_score, col_diff = st.columns([1, 2])
                        
                        with col_score:
                             st.markdown(f"""
                            <div style="padding: 1rem; border-radius: 0.5rem; background-color: rgba(30, 41, 59, 0.6); border: 2px solid {score_color}; text-align: center; margin: 1rem 0;">
                                <h3 style="margin:0; color: #94a3b8; font-size: 1rem;">Accuracy Score</h3>
                                <h1 style="margin:0; color: {score_color}; font-size: 3rem;">{accuracy_pct:.1f}%</h1>
                            </div>
                            """, unsafe_allow_html=True)
                        
                        with col_diff:
                             # Diff view
                            with st.expander("View Differences", expanded=True):
                                # Generate diff
                                d = difflib.Differ()
                                diff = d.compare(ref_text.splitlines(), hyp_text.splitlines())
                                st.markdown("```diff\n" + '\n'.join(diff) + "\n```")
    
    except Exception as e:
        st.error(f"❌ Error during transcription: {str(e)}")
        st.exception(e)


if __name__ == "__main__":
    main()
