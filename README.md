# 🎙️ Multilingual Audio Transcriber

A beautiful Streamlit application for transcribing audio and video files in 99+ languages using OpenAI's Whisper AI.

![License](https://img.shields.io/badge/license-MIT-blue.svg)
![Python](https://img.shields.io/badge/python-3.8%2B-blue)
![Streamlit](https://img.shields.io/badge/streamlit-1.28%2B-red)

## ✨ Features

- 🌍 **99+ Languages**: Supports English, Malay, Chinese, Tamil, Spanish, French, German, Arabic, Hindi, and many more
- 🎯 **Accurate Transcription**: Powered by OpenAI's Whisper AI
- 📁 **Multiple Formats**: Supports MP3, WAV, M4A, MP4, MTS, and more
- ⏱️ **Timestamped Output**: Generate SRT subtitles with precise timestamps
- 🎨 **Modern UI**: Beautiful glassmorphism design with dark theme
- 💾 **Export Options**: Download as SRT, segmented TXT, or full text
- ⚡ **Fast Processing**: Optimized audio preprocessing and API calls
- 🔒 **Secure**: API keys stored securely in environment variables

## 🚀 Quick Start

### Prerequisites

- Python 3.8 or higher
- FFmpeg installed ([Download here](https://ffmpeg.org/download.html))
- OpenAI API key ([Get one here](https://platform.openai.com/api-keys))

### Installation

1. **Clone the repository**
   ```bash
   git clone <your-repo-url>
   cd iptk_transcriber
   ```

2. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

3. **Set up environment variables**
   ```bash
   cp .env.example .env
   ```
   
   Edit `.env` and add your OpenAI API key:
   ```
   OPENAI_API_KEY=your-api-key-here
   ```

4. **Run the application**
   ```bash
   streamlit run app.py
   ```

5. **Open your browser**
   
   The app will automatically open at `http://localhost:8501`

## 📖 Usage

1. **Enter API Key**: Paste your OpenAI API key in the sidebar (or set it in `.env`)
2. **Select Language**: Choose the language or use auto-detect
3. **Upload File**: Drag and drop or browse for an audio/video file
4. **Transcribe**: Click "Start Transcription" and wait for processing
5. **Download**: Get your transcripts in SRT, TXT, or full text format

## 🌐 Deploy to Streamlit Cloud

### Step-by-Step Deployment

1. **Push to GitHub**
   ```bash
   git init
   git add .
   git commit -m "Initial commit"
   git remote add origin <your-github-repo-url>
   git push -u origin main
   ```

2. **Deploy on Streamlit Cloud**
   - Go to [share.streamlit.io](https://share.streamlit.io)
   - Click "New app"
   - Connect your GitHub repository
   - Select `app.py` as the main file
   - Click "Deploy"

3. **Add API Key Secret**
   - In Streamlit Cloud dashboard, go to your app settings
   - Click "Secrets"
   - Add your OpenAI API key:
     ```toml
     OPENAI_API_KEY = "your-api-key-here"
     ```

4. **Share Your App**
   - Your app will be live at `https://your-app-name.streamlit.app`
   - Anyone with the URL can use it!

## 📁 Supported Formats

### Audio Files
- MP3, WAV, M4A, FLAC, OGG, WMA

### Video Files
- MP4, AVI, MOV, MKV, MTS, WEBM

## 🌍 Supported Languages

The app supports 99+ languages including:

- **Asian**: Chinese, Japanese, Korean, Thai, Vietnamese, Indonesian, Malay, Tamil, Hindi, Bengali
- **European**: English, Spanish, French, German, Italian, Portuguese, Russian, Polish, Dutch, Swedish, Norwegian, Danish, Finnish
- **Middle Eastern**: Arabic, Hebrew, Turkish
- **And many more...**

Use "Auto-detect" if you're not sure of the language!

## 💰 Cost Considerations

### API Usage
- Uses **Whisper API only** (no GPT-4 calls)
- **One API call per file**
- Whisper pricing: ~$0.006 per minute of audio
- Example: 10-minute audio ≈ $0.06

### Tips to Minimize Costs
- Use shorter audio clips for testing
- Process files in batches when needed
- Monitor your OpenAI usage dashboard

## 🛠️ Project Structure

```
iptk_transcriber/
├── app.py                      # Main Streamlit application
├── utils/
│   ├── __init__.py
│   ├── audio_processor.py      # Audio conversion & normalization
│   ├── transcriber.py          # Whisper API integration
│   └── exporter.py             # SRT/TXT export utilities
├── .streamlit/
│   └── config.toml             # Streamlit theme configuration
├── requirements.txt            # Python dependencies
├── .env.example                # Environment variables template
└── README.md                   # This file
```

## 🔧 Configuration

### Streamlit Theme
Customize the theme in `.streamlit/config.toml`:
- Primary color: Indigo (#6366f1)
- Background: Dark slate (#0f172a)
- Upload size limit: 200 MB

### Audio Processing
Default settings in `utils/audio_processor.py`:
- Sample rate: 16 kHz
- Channels: Mono
- Normalization: -20 dBFS

## ❓ Troubleshooting

### FFmpeg Not Found
**Error**: `FileNotFoundError: [WinError 2] The system cannot find the file specified`

**Solution**: Install FFmpeg:
- **Windows**: Download from [ffmpeg.org](https://ffmpeg.org/download.html) and add to PATH
- **Mac**: `brew install ffmpeg`
- **Linux**: `sudo apt-get install ffmpeg`

### API Key Issues
**Error**: Authentication error or invalid API key

**Solution**:
1. Verify your API key is correct
2. Check you have credits in your OpenAI account
3. Ensure the key has permissions for Whisper API

### Large File Upload
**Error**: File upload fails for large files

**Solution**:
- Increase the limit in `.streamlit/config.toml` under `[server]`
- Consider compressing audio before upload
- Split very long recordings into segments

## 🤝 Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

## 📄 License

This project is licensed under the MIT License.

## 🙏 Acknowledgments

- [OpenAI Whisper](https://openai.com/research/whisper) for the amazing transcription API
- [Streamlit](https://streamlit.io/) for the awesome web framework
- [FFmpeg](https://ffmpeg.org/) for audio/video processing

## 📧 Support

For issues or questions:
- Open an issue on GitHub
- Check the [Streamlit documentation](https://docs.streamlit.io/)
- Review [OpenAI API docs](https://platform.openai.com/docs)

---

Made with ❤️ using Streamlit and Whisper AI
