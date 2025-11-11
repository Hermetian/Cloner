# Cloner - Quick Start Guide

## Post-Setup Steps

Once the package installation completes, follow these steps:

### 1. Verify Installation

```bash
# Activate virtual environment
cd /mnt/c/Users/cordw/iCloudDrive/Documents/Projects/Cloner
source venv/bin/activate

# Test Python imports
python -c "import torch; print(f'PyTorch: {torch.__version__}')"
python -c "import cv2; print(f'OpenCV: {cv2.__version__}')"
python -c "import playwright; print('Playwright: OK')"
python -c "import elevenlabs; print('ElevenLabs: OK')"
```

### 2. Install Playwright Browsers

```bash
playwright install
```

This downloads Chromium, Firefox, and WebKit browsers for automation.

### 3. Set Up Environment Variables

```bash
# Copy the template
cp .env.example .env

# Edit with your API keys
nano .env  # or use any text editor
```

Add your keys:
```
ELEVENLABS_API_KEY=your_actual_key_here
```

### 4. Test Configuration

```bash
# Test config loading
python -c "from src.utils.config_loader import ConfigLoader; c = ConfigLoader(); print('Config loaded successfully')"
```

### 5. Initialize Git (Optional)

```bash
git init
git add .
git commit -m "Initial project setup"
```

## Basic Usage Examples

### Example 1: Test Meeting Capture (Future)

```bash
# This will be implemented in Phase 1
python scripts/capture.py --url "meeting_url" --duration 60
```

### Example 2: Test Voice Cloning (Future)

```bash
# This will be implemented in Phase 2
python scripts/clone_voice.py \
  --audio data/audio/sample.mp3 \
  --text "Hello, this is a test of voice cloning!"
```

### Example 3: Run Full Pipeline (Future)

```bash
# This will be implemented after all phases
python scripts/run_pipeline.py \
  --meeting-url "https://meet.google.com/xxx" \
  --text "Your custom message here" \
  --output data/output/final_video.mp4
```

## Development Workflow

1. **Start Development**:
   ```bash
   source venv/bin/activate
   ```

2. **Make Changes**: Edit files in `src/`

3. **Test Changes**:
   ```bash
   python -m pytest tests/
   ```

4. **Deactivate** when done:
   ```bash
   deactivate
   ```

## File Paths Reference

All paths relative to project root:

- **Configurations**: `config/config.yaml`, `.env`
- **Source Code**: `src/{capture,voice,video,compositing,utils}/`
- **Data Storage**:
  - Input audio: `data/audio/`
  - Input video: `data/video/`
  - Trained models: `data/models/`
  - Final outputs: `data/output/`
- **Logs**: `cloner.log` (auto-created)

## Customization

### Change Voice Provider

Edit `config/config.yaml`:
```yaml
voice:
  provider: "resemble"  # or "elevenlabs"
```

### Adjust Video Quality

Edit `config/config.yaml`:
```yaml
video:
  resolution: "4k"  # "720p", "1080p", or "4k"
  fps: 60
```

### Modify Animation Timing

Edit `config/config.yaml`:
```yaml
compositing:
  animation:
    door_enter_duration: 3.0  # seconds
    walk_duration: 2.0
```

## Troubleshooting

### Virtual Environment Not Activating

```bash
# Try full path
source /mnt/c/Users/cordw/iCloudDrive/Documents/Projects/Cloner/venv/bin/activate
```

### Import Errors

```bash
# Reinstall package
pip install --force-reinstall package_name
```

### FFmpeg Not Found

```bash
# Check installation
which ffmpeg
ffmpeg -version

# If missing, reinstall
sudo apt-get install ffmpeg
```

### GPU Not Detected (PyTorch)

```bash
python -c "import torch; print(torch.cuda.is_available())"
```

If False, PyTorch will use CPU (slower but functional).

## Next Development Steps

See `PROJECT_SUMMARY.md` for detailed development phases.

The immediate next task is to build the **Meeting Capture Module** using Playwright.

## Useful Commands

```bash
# Check disk space (models are large!)
df -h

# Monitor package sizes
du -sh data/*

# View logs in real-time
tail -f cloner.log

# List installed packages
pip list

# Update a specific package
pip install --upgrade package_name
```

## Getting Help

- Review `README.md` for full documentation
- Check `PROJECT_SUMMARY.md` for project status
- Review logs in `cloner.log`
- Check config in `config/config.yaml`

## Safety Reminders

- ✅ Always get consent before recording
- ✅ Check local recording laws
- ✅ Respect platform Terms of Service
- ✅ Use ethically and responsibly
- ❌ Never use for impersonation or fraud

---

Ready to start building! 🚀
