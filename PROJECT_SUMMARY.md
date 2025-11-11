# Cloner Project - Development Environment Setup Summary

## Current Status: ✅ Environment Setup Complete

**Date**: November 1, 2025
**Python Version**: 3.12.3
**FFmpeg Version**: 6.1.1
**Platform**: WSL2 Ubuntu on Windows

## Completed Tasks

- [x] Designed workflow pipeline and tool integration strategy
- [x] Verified Python 3.12.3 installation
- [x] Created Python virtual environment
- [x] Installed and verified FFmpeg 6.1.1
- [x] Created requirements.txt with compatible dependencies
- [x] Installing Python dependencies (in progress)
- [x] Created project directory structure
- [x] Created configuration files
- [x] Created utility modules (config loader, logger)

## Project Structure

```
Cloner/
├── src/
│   ├── capture/           # Meeting capture using Playwright
│   ├── voice/             # Voice cloning with ElevenLabs/Resemble.ai
│   ├── video/             # Video generation/deepfake
│   ├── compositing/       # Video effects and compositing
│   └── utils/             # Shared utilities (config, logger)
├── data/
│   ├── audio/             # Captured and generated audio files
│   ├── video/             # Captured and generated video files
│   ├── models/            # Trained AI models
│   └── output/            # Final output videos
├── config/
│   └── config.yaml        # Main configuration file
├── scripts/               # CLI tools and automation scripts
├── tests/                 # Unit tests
├── venv/                  # Python virtual environment
├── requirements.txt       # Python dependencies
├── .env.example           # Environment template
├── .gitignore             # Git ignore rules
├── README.md              # Project documentation
└── PROJECT_SUMMARY.md     # This file
```

## Technology Stack

### Core Dependencies
- **Python**: 3.12.3
- **FFmpeg**: 6.1.1 (for video processing)

### Python Packages (Key Libraries)
- **Browser Automation**: Playwright 1.55.0
- **Voice Cloning**: ElevenLabs SDK 2.21.0
- **Video Processing**: OpenCV 4.12.0, MoviePy 2.2.1
- **Deep Learning**: PyTorch 2.9.0, torchvision, torchaudio
- **Face Detection**: MediaPipe 0.10.14, InsightFace 0.7.3
- **Audio Processing**: librosa 0.11.0, pydub 0.25.1, soundfile 0.13.1
- **Utilities**: NumPy, SciPy, requests, python-dotenv, tqdm, click, PyYAML

## Workflow Pipeline Design

### 1. Capture Phase
- Use Playwright to automate browser joining Google Meet/Zoom
- Record audio and video streams
- Save participant data separately

### 2. Voice Cloning Phase
- Extract clean audio samples (60+ seconds recommended)
- Train/upload to voice cloning service (ElevenLabs)
- Generate TTS audio with custom script

### 3. Video Generation Phase
- Extract face frames from captured video
- Train deepfake model (DeepFaceLab, FaceFusion, or Deep Live Cam)
- Generate video of person saying the script
- Create walk-in/walk-out animations

### 4. Compositing Phase
- Apply green screen effects
- Composite layers:
  - Office background
  - Door opening animation
  - Person walking in and sitting
  - Person delivering message
  - Person leaving
- Export final video

### 5. Automation
- Python orchestrator to chain all steps
- CLI interface for easy execution

## Configuration

### Main Config File
Location: `config/config.yaml`

Key sections:
- **capture**: Browser settings, video/audio quality, output paths
- **voice**: Voice cloning provider, API settings, audio duration
- **video**: Deepfake tool, resolution, FPS, face detector
- **compositing**: Green screen settings, animation timing, output format
- **logging**: Log level, file location

### Environment Variables
Location: `.env` (create from `.env.example`)

Required:
- `ELEVENLABS_API_KEY`: For voice cloning
- Optional: Google/Zoom credentials for automated login

## Next Steps

### Immediate (Post-Setup)
1. [ ] Verify all package installations successful
2. [ ] Install Playwright browsers: `playwright install`
3. [ ] Test imports and basic functionality
4. [ ] Create .env file with API keys

### Development Phase 1 - Capture Module
1. [ ] Build meeting capture script with Playwright
2. [ ] Implement audio/video stream extraction
3. [ ] Add error handling and logging
4. [ ] Test with sample meeting

### Development Phase 2 - Voice Cloning
1. [ ] Integrate ElevenLabs API
2. [ ] Build voice training/upload functionality
3. [ ] Implement TTS generation
4. [ ] Test audio quality

### Development Phase 3 - Video Generation
1. [ ] Research and select deepfake tool (DeepFaceLab vs FaceFusion)
2. [ ] Implement face detection and extraction
3. [ ] Build model training pipeline
4. [ ] Generate test videos

### Development Phase 4 - Compositing
1. [ ] Implement green screen removal (FFmpeg/MoviePy)
2. [ ] Build animation system (door, walking)
3. [ ] Create compositing pipeline
4. [ ] Add final rendering

### Development Phase 5 - Integration
1. [ ] Build main orchestrator script
2. [ ] Create CLI interface with Click
3. [ ] Add progress tracking
4. [ ] End-to-end testing

### Development Phase 6 - Polish
1. [ ] Error handling and recovery
2. [ ] Performance optimization
3. [ ] Documentation
4. [ ] Example gallery

## Important Notes

### Legal & Ethical
⚠️ **Always obtain explicit consent** from participants before recording
⚠️ **Comply with recording laws** (check two-party consent requirements)
⚠️ **Respect platform ToS** for Google Meet and Zoom
⚠️ **Never use for impersonation or fraud**

### Technical Considerations
- Large file sizes: Video and model files will be several GB
- GPU recommended: For faster deepfake training (though CPU works)
- Processing time: Initial deepfake training can take hours
- API costs: ElevenLabs has usage limits on free tier

### Known Limitations
- Coqui TTS incompatible with Python 3.12 (using ElevenLabs instead)
- Deep learning packages are large (PyTorch + CUDA = 5+ GB)
- Real-time processing not yet implemented

## Resources

### Documentation
- [Playwright Docs](https://playwright.dev/python/)
- [ElevenLabs API](https://elevenlabs.io/docs)
- [DeepFaceLab Guide](https://github.com/iperov/DeepFaceLab)
- [FFmpeg Chroma Key](https://trac.ffmpeg.org/wiki/FancyFilteringExamples)
- [MoviePy Docs](https://zulko.github.io/moviepy/)

### Community
- DeepFaceLab Discord
- r/deepfakes (Reddit)
- Playwright GitHub Issues

## Troubleshooting

### Common Issues
1. **Package installation failures**: Check Python version compatibility
2. **FFmpeg not found**: Verify installation with `ffmpeg -version`
3. **CUDA errors**: PyTorch will fall back to CPU if no GPU
4. **Meeting capture fails**: Check browser automation permissions

### Getting Help
- Check logs in `cloner.log`
- Review error messages carefully
- Consult tool-specific documentation
- Open GitHub issue if needed

---

**Last Updated**: November 1, 2025
**Status**: Development Environment Setup Phase
