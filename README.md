# Cloner - AI Video Clone Generator

Create AI-generated video clones of meeting participants with synchronized voice and animated entrance/exit effects.

## Overview

Cloner captures audio and video from Google Meet and Zoom meetings, creates AI clones of participants using voice cloning and deepfake technology, and composites them into animated videos where they appear to walk into your office, deliver a message, and leave.

## Features

- **Meeting Capture**: Automated audio/video capture from Google Meet and Zoom using headless browser automation
- **Voice Cloning**: Generate realistic voice clones using ElevenLabs API
- **Deepfake Video**: Create video clones using DeepFaceLab, FaceFusion, or Deep Live Cam
- **Video Compositing**: Green screen effects and animations with FFmpeg
- **Automation**: End-to-end pipeline from meeting URL to final video

## Project Structure

```
Cloner/
├── src/
│   ├── capture/       # Meeting capture modules
│   ├── voice/         # Voice cloning modules
│   ├── video/         # Video generation/deepfake modules
│   ├── compositing/   # Video compositing and effects
│   └── utils/         # Shared utilities
├── data/
│   ├── audio/         # Captured and generated audio
│   ├── video/         # Captured and generated video
│   ├── models/        # Trained AI models
│   └── output/        # Final output videos
├── config/
│   ├── config.yaml    # Main configuration
│   └── templates/     # Script templates
├── scripts/           # CLI scripts and tools
├── tests/             # Unit tests
├── requirements.txt   # Python dependencies
└── README.md

```

## Setup

### Prerequisites

- Python 3.12+
- FFmpeg 6.1+
- Ubuntu/WSL2 (or Linux)

### Installation

1. Clone or navigate to the project directory:
   ```bash
   cd /path/to/Cloner
   ```

2. Create and activate virtual environment:
   ```bash
   python3 -m venv venv
   source venv/bin/activate
   ```

3. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

4. Install Playwright browsers:
   ```bash
   playwright install
   ```

5. Copy environment template and add your API keys:
   ```bash
   cp .env.example .env
   # Edit .env and add your API keys
   ```

## Configuration

Edit `config/config.yaml` to customize:
- Meeting capture settings
- Voice cloning provider and settings
- Video generation quality
- Compositing effects and animations

## Usage

### Basic Workflow

1. **Capture Meeting** (with consent):
   ```bash
   python scripts/capture.py --url "https://meet.google.com/xxx" --output data/video/meeting.mp4
   ```

2. **Generate Voice Clone**:
   ```bash
   python scripts/clone_voice.py --input data/audio/speaker.mp3 --text "Your message here"
   ```

3. **Generate Video Clone**:
   ```bash
   python scripts/clone_video.py --source data/video/speaker.mp4 --audio data/audio/cloned_voice.mp3
   ```

4. **Composite Final Video**:
   ```bash
   python scripts/composite.py --background office.mp4 --clone cloned_video.mp4 --output final.mp4
   ```

### Automated Pipeline

Run the entire pipeline with one command:
```bash
python scripts/run_pipeline.py --meeting-url "URL" --text "Message" --output final.mp4
```

## Technology Stack

- **Browser Automation**: Playwright
- **Voice Cloning**: ElevenLabs API
- **Video Processing**: FFmpeg, OpenCV, MoviePy
- **Face Detection**: MediaPipe, InsightFace
- **Deep Learning**: PyTorch
- **Deepfake Tools**: DeepFaceLab, FaceFusion, Deep Live Cam

## Legal & Ethical Considerations

⚠️ **IMPORTANT**: This tool is for **legitimate, consensual use only**.

- Always obtain explicit consent from participants before recording
- Comply with local recording laws (two-party consent where applicable)
- Respect platform Terms of Service
- Only use for authorized purposes (creative projects, demonstrations with consent)
- Never use for impersonation, fraud, or malicious purposes

## Development Status

🚧 **Work in Progress** - Initial setup complete, modules under development

## License

MIT License - See LICENSE file for details

## Contributing

This is a personal project. For questions or suggestions, please open an issue.

## Acknowledgments

- Coqui TTS community
- ElevenLabs for voice cloning API
- DeepFaceLab team
- Playwright and FFmpeg communities
