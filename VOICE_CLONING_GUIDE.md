# Voice Cloning Module - User Guide

## Overview

The voice cloning module allows you to clone voices from audio samples and generate speech using those cloned voices.

## Quick Start

### Prerequisites
- ElevenLabs API key (added to `.env` file) ✓
- Audio samples (1-5 minutes of clear speech)
- Python virtual environment activated

### Basic Usage

#### 1. List Available Voices
```bash
python scripts/clone_voice.py list-voices
```

#### 2. Clone a Voice
```bash
python scripts/clone_voice.py clone \
  --name "John" \
  --audio sample1.mp3 \
  --audio sample2.mp3 \
  --description "John's voice clone"
```

#### 3. Generate Speech
```bash
python scripts/clone_voice.py speak \
  --text "Hello, this is my cloned voice!" \
  --voice-id <voice_id_from_step_2> \
  --output output.mp3
```

#### 4. Quick Workflow (Clone + Speak)
```bash
python scripts/clone_voice.py quick \
  --name "John" \
  --audio sample.mp3 \
  --text "Hello world!" \
  --output result.mp3
```

## Detailed Commands

### `clone` - Clone a Voice

Clone a voice from audio samples.

**Options:**
- `--name` (required): Name for the cloned voice
- `--audio` / `-a` (required, multiple): Audio file(s) to use for cloning
- `--description` / `-d`: Optional description
- `--no-validate`: Skip audio quality validation
- `--auto-process`: Automatically remove silence and normalize

**Example:**
```bash
python scripts/clone_voice.py clone \
  --name "Sarah" \
  -a recordings/sarah_1.mp3 \
  -a recordings/sarah_2.wav \
  -a recordings/sarah_3.mp3 \
  --description "Professional narrator voice" \
  --auto-process
```

**Tips:**
- Use 1-5 minutes of clear audio total
- Multiple short clips often work better than one long clip
- Remove background noise before cloning
- Use `--auto-process` to automatically clean audio

---

### `speak` - Generate Speech

Generate speech from text using a cloned voice.

**Options:**
- `--text` / `-t` (required): Text to convert to speech
- `--voice-id` (required): Voice ID to use
- `--output` / `-o` (required): Output audio file path
- `--stability`: Voice stability (0.0-1.0, default: 0.5)
- `--similarity`: Similarity boost (0.0-1.0, default: 0.75)

**Example:**
```bash
python scripts/clone_voice.py speak \
  -t "The quick brown fox jumps over the lazy dog." \
  --voice-id "abc123xyz" \
  -o output/test.mp3 \
  --stability 0.7 \
  --similarity 0.8
```

**Parameter Guide:**
- **Stability (0.0-1.0):**
  - Lower = More expressive, variable
  - Higher = More stable, consistent
  - Default 0.5 works for most cases

- **Similarity (0.0-1.0):**
  - Controls how closely speech matches original voice
  - Higher = More similar to original
  - Default 0.75 recommended

---

### `quick` - Clone and Speak in One Command

Quick workflow that clones a voice and generates speech immediately.

**Options:**
- `--name` (required): Name for the cloned voice
- `--audio` / `-a` (required, multiple): Audio files for cloning
- `--text` / `-t` (required): Text to speak
- `--output` / `-o` (required): Output audio file
- `--description` / `-d`: Voice description
- `--stability`: Voice stability (default: 0.5)
- `--similarity`: Similarity boost (default: 0.75)

**Example:**
```bash
python scripts/clone_voice.py quick \
  --name "Demo Voice" \
  -a recording.mp3 \
  -t "This is a test of the voice cloning system." \
  -o demo_output.mp3
```

---

### `list-voices` - List All Voices

List all available voices (both preset and your cloned voices).

**Example:**
```bash
python scripts/clone_voice.py list-voices
```

---

### `delete` - Delete a Cloned Voice

Delete a cloned voice by ID.

**Options:**
- `--voice-id` (required): ID of voice to delete

**Example:**
```bash
python scripts/clone_voice.py delete --voice-id "abc123xyz"
```

**Note:** This will ask for confirmation before deleting.

---

### `prepare` - Prepare Audio for Cloning

Optimize audio file for voice cloning (remove silence, split long files, etc.).

**Options:**
- `--input` / `-i` (required): Input audio file
- `--output-dir` / `-o` (required): Output directory
- `--remove-silence`: Remove silent sections (default: true)
- `--split`: Split long audio into chunks (default: true)
- `--max-duration`: Max duration per chunk in seconds (default: 300)

**Example:**
```bash
python scripts/clone_voice.py prepare \
  -i raw_recording.mp3 \
  -o prepared_audio/ \
  --remove-silence \
  --split \
  --max-duration 180
```

**Use case:** Clean up a long, messy recording before cloning.

---

### `validate` - Validate Audio Quality

Check if an audio file is suitable for voice cloning.

**Options:**
- `--input` / `-i` (required): Audio file to validate

**Example:**
```bash
python scripts/clone_voice.py validate -i my_audio.mp3
```

**Output:** Shows duration, sample rate, format, and warnings about quality issues.

---

## Best Practices

### Audio Quality Tips

1. **Duration:** 1-5 minutes of clear speech is ideal
   - Too short (<30s): Poor quality clone
   - Too long (>10m): Diminishing returns, harder to process

2. **Recording Quality:**
   - Use a good microphone
   - Quiet environment (no background noise)
   - Consistent volume level
   - No music or sound effects

3. **Content:**
   - Clear, natural speech
   - Variety of words and phrases
   - Different emotions/tones (if you want versatile clone)
   - Avoid long pauses

4. **Format:**
   - WAV or high-quality MP3 (192kbps+)
   - 44.1kHz or higher sample rate
   - Mono preferred (stereo works but not necessary)

### Workflow Recommendations

**For First-Time Users:**
```bash
# 1. Validate your audio first
python scripts/clone_voice.py validate -i my_audio.mp3

# 2. Prepare if needed
python scripts/clone_voice.py prepare -i my_audio.mp3 -o prepared/

# 3. Use quick command for testing
python scripts/clone_voice.py quick \
  --name "Test Clone" \
  -a prepared/*.mp3 \
  -t "Testing one two three" \
  -o test_output.mp3

# 4. Listen and adjust parameters if needed
```

**For Production:**
```bash
# 1. Clone voice separately (can reuse voice_id)
python scripts/clone_voice.py clone \
  --name "Production Voice" \
  -a audio1.mp3 -a audio2.mp3 \
  --auto-process

# 2. Generate multiple speeches with same voice
python scripts/clone_voice.py speak \
  -t "First message" \
  --voice-id <id> \
  -o message1.mp3

python scripts/clone_voice.py speak \
  -t "Second message" \
  --voice-id <id> \
  -o message2.mp3
```

---

## Troubleshooting

### "API key not found"
- Make sure `.env` file exists in project root
- Check that `ELEVENLABS_API_KEY` is set correctly
- Try: `cat .env | grep ELEVENLABS_API_KEY`

### "Audio file validation warnings"
- Run `validate` command to see specific issues
- Use `prepare` command to automatically fix common issues
- Check audio quality (sample rate, duration, noise)

### "Failed to clone voice"
- Check API quota (free tier: 10,000 chars/month)
- Verify audio files exist and are readable
- Try with `--auto-process` flag
- Ensure audio is clear speech (not music/noise)

### "Low quality output"
- Try adjusting `--stability` and `--similarity` parameters
- Use higher quality input audio
- Ensure sufficient audio duration for cloning
- Try re-cloning with different audio samples

---

## Examples

### Example 1: Clone from Single File
```bash
python scripts/clone_voice.py quick \
  --name "Quick Test" \
  -a recording.mp3 \
  -t "Hello, this is a test." \
  -o output.mp3
```

### Example 2: Clone from Multiple Files
```bash
python scripts/clone_voice.py clone \
  --name "Multi-Sample Clone" \
  -a sample1.mp3 \
  -a sample2.mp3 \
  -a sample3.mp3 \
  --description "Clone from 3 different recordings" \
  --auto-process
```

### Example 3: Generate Long Speech
```bash
python scripts/clone_voice.py speak \
  -t "$(cat long_script.txt)" \
  --voice-id abc123 \
  -o long_speech.mp3 \
  --stability 0.6
```

### Example 4: Batch Processing
```bash
# Clone once
VOICE_ID=$(python scripts/clone_voice.py clone \
  --name "Batch Voice" \
  -a audio.mp3 | grep "Voice ID:" | cut -d: -f2 | tr -d ' ')

# Generate multiple speeches
for text in "Message 1" "Message 2" "Message 3"; do
  python scripts/clone_voice.py speak \
    -t "$text" \
    --voice-id "$VOICE_ID" \
    -o "output_${text// /_}.mp3"
done
```

---

## API Limits

**Free Tier:**
- 10,000 characters per month
- ~30 seconds of generated audio
- Voice cloning: Unlimited clones
- Perfect for testing and development

**Upgrade:** Visit https://elevenlabs.io/pricing for paid plans with higher limits.

---

## Next Steps

Once you've mastered voice cloning:
1. **Meeting Capture:** Capture audio from Google Meet/Zoom
2. **Video Generation:** Create deepfake videos with cloned voices
3. **Full Pipeline:** Automate entire clone creation workflow

See `README.md` and `PROJECT_SUMMARY.md` for full roadmap!
