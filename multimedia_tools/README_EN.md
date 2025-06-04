# Multimedia Tools

This directory contains various utility scripts for processing multimedia files (videos, audio, images, etc.).

## Subtitle Generator (subtitle_generator.py)

`subtitle_generator.py` is a powerful tool that uses OpenAI's Whisper model to automatically generate high-quality subtitles from video or audio files. It supports transcription and translation functions for multiple languages and can output various common subtitle formats.

### Features

- Extract audio from video files and transcribe it to text
- Support multiple subtitle formats: SRT, VTT, TXT, JSON, TSV
- Support multilingual recognition and translation
- Choose different sizes of Whisper models to balance accuracy and speed
- Automatically detect language or manually specify language
- Support GPU acceleration for the transcription process (requires a compatible CUDA device)

### Dependencies

Before using, you need to install the following dependencies:

```bash
# Install Python dependencies
pip install openai-whisper pysrt tqdm

# Install FFmpeg (Windows)
# Using Chocolatey
choco install ffmpeg

# Or using Scoop
scoop install ffmpeg
```

### Basic Usage

```bash
# Transcribe a video file with default settings (medium model, auto language detection, SRT format)
python subtitle_generator.py video.mp4

# Specify output subtitle file path
python subtitle_generator.py video.mp4 -o my_subtitles

# Use a smaller model (faster but less accurate)
python subtitle_generator.py video.mp4 -m tiny

# Specify language (improves recognition accuracy)
python subtitle_generator.py video.mp4 -l en

# Translate audio to English (instead of transcribing in original language)
python subtitle_generator.py chinese_audio.mp3 -t translate

# Output subtitles in multiple formats simultaneously
python subtitle_generator.py video.mp4 -f srt vtt txt

# Use large model with verbose logging
python subtitle_generator.py video.mp4 -m large -v
```

### Command Line Arguments

| Parameter | Short | Description | Default |
|-----------|-------|-------------|---------|
| `input` | - | Input video or audio file path | (Required) |
| `--output` | `-o` | Output subtitle file path (without extension) | Same as input file |
| `--model` | `-m` | Whisper model size (tiny/base/small/medium/large/turbo) | medium |
| `--language` | `-l` | Audio language code (e.g., en, zh, ja) | Auto-detect |
| `--task` | `-t` | Task type (transcribe/translate) | transcribe |
| `--device` | `-d` | Computation device (cpu/cuda) | Auto-detect |
| `--formats` | `-f` | Subtitle formats to generate | srt |
| `--verbose` | `-v` | Show detailed logs | False |

### Supported Model Sizes

| Model Size | Parameters | Memory Required | Relative Speed | Accuracy |
|------------|------------|-----------------|----------------|----------|
| tiny       | 39 M       | ~1 GB           | ~10x           | Lower    |
| base       | 74 M       | ~1 GB           | ~7x            | Low      |
| small      | 244 M      | ~2 GB           | ~4x            | Medium   |
| medium     | 769 M      | ~5 GB           | ~2x            | High     |
| large      | 1550 M     | ~10 GB          | 1x             | Highest  |
| turbo      | 809 M      | ~6 GB           | ~8x            | High     |

### Important Notes

1. When running for the first time, the script will automatically download the specified Whisper model (requires internet connection).
2. Processing long videos may take considerable time, especially when using larger models.
3. Using a GPU can significantly improve processing speed.
4. For low-quality audio or audio with background noise, transcription accuracy may be affected.
5. Specifying the correct language can improve recognition accuracy.

### Example Output

After successful execution, the script will generate output like this:

```
2025-06-05 15:30:12 - INFO - Loading Whisper medium model...
2025-06-05 15:30:20 - INFO - Model loading complete. Using device: cuda
2025-06-05 15:30:20 - INFO - Extracting audio from video...
2025-06-05 15:30:25 - INFO - Audio extraction completed: C:\Users\user\AppData\Local\Temp\tmp5hd7f8k9.wav
2025-06-05 15:30:25 - INFO - Transcribing audio: C:\Users\user\AppData\Local\Temp\tmp5hd7f8k9.wav
2025-06-05 15:30:30 - INFO - Detected language: zh
2025-06-05 15:31:15 - INFO - Transcription complete! Processed 125.80 seconds of audio in 50.23 seconds (processing speed: 2.50x)
2025-06-05 15:31:16 - INFO - Saved SRT format subtitles: video.srt
2025-06-05 15:31:16 - INFO - Subtitle generation complete! Total time: 64.12 seconds
```

### Typical Subtitle Workflow

1. Generate a draft quickly using a small model: `python subtitle_generator.py video.mp4 -m tiny`
2. If quality is unsatisfactory, use a medium or large model and specify language: `python subtitle_generator.py video.mp4 -m medium -l en`
3. For translation, add the translate parameter: `python subtitle_generator.py video.mp4 -t translate`
4. Export in multiple formats to meet different needs: `python subtitle_generator.py video.mp4 -f srt vtt txt`
