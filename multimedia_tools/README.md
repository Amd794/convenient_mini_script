# 多媒体工具 (Multimedia Tools)

本目录包含各种用于处理多媒体文件（视频、音频、图片等）的实用工具脚本。

## 字幕生成器 (subtitle_generator.py)

`subtitle_generator.py` 是一个强大的工具，可以使用OpenAI的Whisper模型从视频或音频文件中自动生成高质量字幕。支持多种语言的转录和翻译功能，并可输出多种常见的字幕格式。

### 功能特点

- 从视频文件中提取音频并转录为文字
- 支持多种字幕格式: SRT, VTT, TXT, JSON, TSV
- 支持多语言识别和翻译
- 可选择不同大小的Whisper模型以平衡精度和速度
- 自动检测语言或手动指定语言
- 支持使用GPU加速转录过程（需要兼容的CUDA设备）

### 安装依赖

在使用之前，需要安装以下依赖:

```bash
# 安装Python依赖
pip install openai-whisper pysrt tqdm

# 安装FFmpeg(Windows)
# 使用Chocolatey
choco install ffmpeg

# 或使用Scoop
scoop install ffmpeg
```

### 基本用法

```bash
# 使用默认设置转录视频文件(medium模型，自动检测语言，SRT格式)
python subtitle_generator.py video.mp4

# 指定输出字幕文件路径
python subtitle_generator.py video.mp4 -o my_subtitles

# 使用小型模型(更快但精度较低)
python subtitle_generator.py video.mp4 -m tiny

# 指定语言(提高识别准确率)
python subtitle_generator.py video.mp4 -l zh

# 将音频翻译为英文(而非转录原语言)
python subtitle_generator.py chinese_audio.mp3 -t translate

# 同时输出多种格式的字幕
python subtitle_generator.py video.mp4 -f srt vtt txt

# 使用大型模型并启用详细日志
python subtitle_generator.py video.mp4 -m large -v
```

### 命令行参数

| 参数 | 简写 | 描述 | 默认值 |
|------|-----|------|--------|
| `input` | - | 输入视频或音频文件路径 | (必需) |
| `--output` | `-o` | 输出字幕文件路径(不含扩展名) | 与输入文件相同 |
| `--model` | `-m` | Whisper模型大小 (tiny/base/small/medium/large/turbo) | medium |
| `--language` | `-l` | 音频语言代码 (如zh/en/ja) | 自动检测 |
| `--task` | `-t` | 任务类型 (transcribe/translate) | transcribe |
| `--device` | `-d` | 计算设备 (cpu/cuda) | 自动检测 |
| `--formats` | `-f` | 要生成的字幕格式 | srt |
| `--verbose` | `-v` | 显示详细日志 | False |

### 支持的模型大小

| 模型大小 | 参数数量 | 内存需求 | 相对速度 | 准确率 |
|---------|---------|---------|---------|--------|
| tiny    | 39 M    | ~1 GB   | ~10x    | 较低   |
| base    | 74 M    | ~1 GB   | ~7x     | 低     |
| small   | 244 M   | ~2 GB   | ~4x     | 中等   |
| medium  | 769 M   | ~5 GB   | ~2x     | 高     |
| large   | 1550 M  | ~10 GB  | 1x      | 最高   |
| turbo   | 809 M   | ~6 GB   | ~8x     | 高     |

### 注意事项

1. 首次运行时，脚本会自动下载指定的Whisper模型（需要网络连接）。
2. 处理长视频可能需要较长时间，特别是使用较大的模型时。
3. 使用GPU可以显著提升处理速度。
4. 对于低质量或含有背景噪音的音频，可能会影响转录准确率。
5. 指定正确的语言可以提高识别精度。

### 示例输出

成功运行后，脚本将生成如下输出：

```
2025-06-05 15:30:12 - INFO - 正在加载 Whisper medium 模型...
2025-06-05 15:30:20 - INFO - 模型加载完成。使用设备: cuda
2025-06-05 15:30:20 - INFO - 正在从视频中提取音频...
2025-06-05 15:30:25 - INFO - 音频提取完成: C:\Users\user\AppData\Local\Temp\tmp5hd7f8k9.wav
2025-06-05 15:30:25 - INFO - 正在转录音频: C:\Users\user\AppData\Local\Temp\tmp5hd7f8k9.wav
2025-06-05 15:30:30 - INFO - 检测到语言: zh
2025-06-05 15:31:15 - INFO - 转录完成！处理 125.80 秒的音频用时 50.23 秒 (处理速度: 2.50x)
2025-06-05 15:31:16 - INFO - 已保存SRT格式字幕: video.srt
2025-06-05 15:31:16 - INFO - 字幕生成完成！总耗时: 64.12 秒
```

### 典型字幕工作流程

1. 使用小模型快速生成初稿：`python subtitle_generator.py video.mp4 -m tiny`
2. 如果质量不满意，使用中型或大型模型并指定语言：`python subtitle_generator.py video.mp4 -m medium -l zh`
3. 如需翻译，添加translate参数：`python subtitle_generator.py video.mp4 -t translate`
4. 同时导出多种格式以满足不同需求：`python subtitle_generator.py video.mp4 -f srt vtt txt` 