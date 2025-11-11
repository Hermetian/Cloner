# Meeting Capture Module - User Guide

## Overview

The meeting capture module automates joining Google Meet (and Zoom) meetings to capture audio, video, and participant information for voice cloning purposes.

## ⚠️ Important Legal Notice

**ALWAYS obtain explicit consent before recording any meeting participants.**

This tool is designed for:
- ✅ Meetings where you have permission to record
- ✅ Personal meetings with consenting participants
- ✅ Testing/demonstration purposes
- ✅ Educational use cases

**DO NOT use for:**
- ❌ Recording without consent
- ❌ Privacy violations
- ❌ Unauthorized surveillance

## Quick Start

### Prerequisites
- Playwright browsers installed ✓
- Valid Google Meet URL
- Consent from all participants

### Test Browser Automation
```bash
python scripts/capture_meeting.py test
```

This opens a browser to verify Playwright is working.

---

## Commands

### 1. `google-meet` - Join Google Meet

Join a Google Meet meeting and optionally capture screenshots.

**Options:**
- `--url` (required): Google Meet URL
- `--duration`: How long to stay in meeting (seconds)
- `--name`: Display name (default: "Recorder Bot")
- `--headless/--no-headless`: Run browser hidden (default: visible)
- `--mute-audio/--no-mute-audio`: Mute microphone (default: muted)
- `--disable-video/--enable-video`: Disable camera (default: disabled)
- `--output-dir`: Where to save files (default: data/video)
- `--screenshots`: Number of screenshots to capture

**Example:**
```bash
python scripts/capture_meeting.py google-meet \
  --url "https://meet.google.com/abc-defg-hij" \
  --duration 300 \
  --name "Bot" \
  --screenshots 5
```

**What it does:**
1. Opens browser
2. Navigates to meeting
3. Joins with specified settings
4. Takes screenshots if requested
5. Waits for duration (or until Ctrl+C)
6. Leaves and closes browser

---

### 2. `screenshot` - Quick Screenshot

Take a single screenshot of a meeting.

**Options:**
- `--url` (required): Meeting URL
- `--output` / `-o` (required): Output file path
- `--headless/--no-headless`: Run hidden

**Example:**
```bash
python scripts/capture_meeting.py screenshot \
  --url "https://meet.google.com/abc-defg-hij" \
  -o meeting_snapshot.png
```

---

### 3. `observe` - Silent Observation

Observe a meeting without joining (for testing).

**Options:**
- `--url` (required): Meeting URL
- `--duration`: Observation duration (default: 60s)
- `--headless/--no-headless`: Run hidden

**Example:**
```bash
python scripts/capture_meeting.py observe \
  --url "https://meet.google.com/abc-defg-hij" \
  --duration 120
```

---

### 4. `test` - Test Setup

Test that browser automation is working.

**Example:**
```bash
python scripts/capture_meeting.py test
```

---

## Recording Audio/Video

### Current Implementation

The current version focuses on **joining meetings** and **taking screenshots**. For full audio/video recording, you have two options:

### Option 1: Use External Recording Software (Recommended)

1. **Start the meeting capture:**
   ```bash
   python scripts/capture_meeting.py google-meet \
     --url "..." \
     --duration 600 \
     --no-headless
   ```

2. **Start your recording software:**
   - **OBS Studio** (free, recommended)
   - **ShareX** (Windows)
   - **SimpleScreenRecorder** (Linux)
   - **QuickTime** (Mac)

3. **Record the browser window** showing the meeting

4. **Stop both** when done

### Option 2: FFmpeg Integration (Advanced)

For automated recording, you can extend the `MeetingRecorder` class with platform-specific FFmpeg commands:

**Linux (X11):**
```bash
ffmpeg -video_size 1920x1080 \
  -framerate 30 \
  -f x11grab -i :0.0 \
  -f pulse -i default \
  -c:v libx264 -preset ultrafast \
  -c:a aac output.mp4
```

**macOS:**
```bash
ffmpeg -f avfoundation \
  -i "1:0" \
  -c:v libx264 -preset ultrafast \
  -c:a aac output.mp4
```

**Windows:**
```bash
ffmpeg -f gdigrab \
  -framerate 30 -i desktop \
  -f dshow -i audio="Stereo Mix" \
  -c:v libx264 -preset ultrafast \
  -c:a aac output.mp4
```

---

## Workflow Examples

### Example 1: Quick Screenshot for Testing

```bash
# Take a screenshot to verify meeting access
python scripts/capture_meeting.py screenshot \
  --url "https://meet.google.com/xxx-yyyy-zzz" \
  -o test_meeting.png
```

### Example 2: Join and Observe

```bash
# Join meeting for 5 minutes, take 10 screenshots
python scripts/capture_meeting.py google-meet \
  --url "https://meet.google.com/xxx-yyyy-zzz" \
  --duration 300 \
  --screenshots 10 \
  --name "Recorder"
```

### Example 3: Record with OBS

```bash
# Terminal 1: Start meeting capture
python scripts/capture_meeting.py google-meet \
  --url "https://meet.google.com/xxx-yyyy-zzz" \
  --no-headless

# Terminal 2: Start OBS recording targeting the browser window
# (Configure OBS to record specific window)
```

### Example 4: Long Meeting Capture

```bash
# Join for 1 hour, capture screenshots every 2 minutes
python scripts/capture_meeting.py google-meet \
  --url "https://meet.google.com/xxx-yyyy-zzz" \
  --duration 3600 \
  --screenshots 30
```

---

## Configuration

### Environment Variables

Add to your `.env` file (optional):

```bash
# Google Account (for auto-login, if needed)
GOOGLE_MEET_EMAIL=your_email@gmail.com
GOOGLE_MEET_PASSWORD=your_password

# Default settings
DEFAULT_DISPLAY_NAME="Recorder Bot"
DEFAULT_OUTPUT_DIR="data/video"
```

### Browser Settings

The module configures the browser to:
- Auto-grant camera/microphone permissions
- Use fake devices (no actual camera/mic needed)
- Hide automation indicators
- Run in full HD (1920x1080)

---

## Troubleshooting

### "Browser won't start"
- Run: `python scripts/capture_meeting.py test`
- Check Playwright installation: `playwright install`
- Try: `playwright install chromium --force`

### "Can't join meeting"
- Verify the meeting URL is valid
- Try with `--no-headless` to see what's happening
- Check if meeting requires login (add credentials to `.env`)
- Some meetings may block bots - join manually first

### "Meeting requires login"
- Add credentials to `.env` file
- Or join manually in the opened browser

### "Screenshots are black"
- Use `--no-headless` mode
- Some video elements don't capture in headless mode
- Consider using external recording instead

### "Permission denied" errors
- Meeting may require host approval
- Wait for host to admit you
- Or test with your own meeting first

---

## Best Practices

### 1. Test First
Always test with your own meeting before real capture:
```bash
# Create a test meeting
# Run: python scripts/capture_meeting.py google-meet --url "..." --duration 30
# Verify it joins successfully
```

### 2. Get Consent
- Inform all participants you're recording
- Get explicit verbal/written consent
- Follow local recording laws

### 3. Use Visible Mode for Debugging
Start with `--no-headless` to see what's happening:
```bash
python scripts/capture_meeting.py google-meet \
  --url "..." \
  --no-headless
```

### 4. Capture Multiple Angles
Take screenshots at intervals to get variety:
```bash
--screenshots 20  # For a 10-minute meeting
```

### 5. External Recording is Reliable
For important meetings, use OBS Studio alongside:
- More reliable
- Better quality
- Easier to verify

---

## Integration with Voice Cloning

### Workflow: Meeting → Voice Clone

1. **Capture meeting:**
   ```bash
   python scripts/capture_meeting.py google-meet \
     --url "..." \
     --duration 600
   ```

2. **Extract audio** from recording (using FFmpeg):
   ```bash
   ffmpeg -i meeting_recording.mp4 \
     -vn -acodec mp3 \
     meeting_audio.mp3
   ```

3. **Clone voice:**
   ```bash
   python scripts/clone_voice.py clone \
     --name "Participant Name" \
     -a meeting_audio.mp3 \
     --auto-process
   ```

4. **Generate speech:**
   ```bash
   python scripts/clone_voice.py speak \
     -t "Your custom message" \
     --voice-id <id> \
     -o cloned_speech.mp3
   ```

---

## Limitations & Future Improvements

### Current Limitations
- ✓ Joins meetings successfully
- ✓ Takes screenshots
- ⚠️ Full recording requires external tools
- ⚠️ Participant isolation not yet implemented
- ⚠️ Zoom support basic/untested

### Planned Improvements
- [ ] Integrated FFmpeg recording
- [ ] Automatic participant detection
- [ ] Audio stream isolation per participant
- [ ] Full Zoom support
- [ ] Microsoft Teams support
- [ ] Automatic consent verification

---

## Security & Privacy

### Data Storage
- Screenshots: `data/video/screenshots/`
- Recordings: `data/video/`
- Temporary files: Cleaned automatically

### Credentials
- Store in `.env` (never commit!)
- Use application-specific passwords
- Consider OAuth instead of passwords

### Network Security
- Uses HTTPS for all connections
- No data sent to third parties
- All processing local

---

## Advanced Usage

### Custom Browser Settings

Modify `src/capture/browser_automation.py` to customize:
- User agent
- Window size
- Extensions
- Proxy settings

### Headless Recording

For server/automated recording:
```bash
python scripts/capture_meeting.py google-meet \
  --url "..." \
  --headless \
  --screenshots 50
```

### Multiple Meetings

Use a script to process multiple meetings:
```bash
#!/bin/bash
for meeting in meeting1.txt meeting2.txt; do
    URL=$(cat $meeting)
    python scripts/capture_meeting.py google-meet \
      --url "$URL" \
      --duration 600
done
```

---

## Next Steps

Once you've captured meeting data:
1. **Extract audio** for voice cloning
2. **Extract video** frames for deepfake training
3. **Use Phase 1** (Voice Cloning) with captured audio
4. **Move to Phase 3** (Video Compositing) for final output

---

## Support

For issues:
1. Check logs in `cloner.log`
2. Run with `--no-headless` to debug visually
3. Test with `python scripts/capture_meeting.py test`
4. Review Playwright docs: https://playwright.dev/python/

---

**Ready to capture meetings! Remember: Always get consent first!** 🎥
