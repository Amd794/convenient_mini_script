#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
字幕生成器 (Subtitle Generator)

这个脚本使用OpenAI的Whisper模型从视频或音频文件中生成高质量字幕。
支持多种字幕格式，包括SRT、VTT、TXT等。可以处理多种语言，并支持翻译功能。
"""

import os
import sys
import argparse
import logging
import subprocess
import tempfile
import datetime
import time
from pathlib import Path
from typing import List, Optional, Tuple, Dict, Union, Any

try:
    import whisper
    import torch
    import pysrt
    from tqdm import tqdm
except ImportError:
    print("缺少必要的依赖库。请运行: pip install openai-whisper pysrt tqdm")
    sys.exit(1)

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)
logger = logging.getLogger(__name__)

# 支持的字幕格式
SUBTITLE_FORMATS = ["srt", "vtt", "txt", "json", "tsv"]

class SubtitleGenerator:
    """字幕生成器类，封装了从音频/视频生成字幕的所有功能"""
    
    def __init__(self, model_name: str = "medium", device: Optional[str] = None, 
                 language: Optional[str] = None, task: str = "transcribe", 
                 verbose: bool = False):
        """
        初始化字幕生成器
        
        参数:
            model_name (str): Whisper模型名称 (tiny, base, small, medium, large, turbo)
            device (str): 设备选择 ('cuda', 'cpu', None=自动检测)
            language (str): 源语言代码 (例如 'zh', 'en', 'ja', None=自动检测)
            task (str): 任务类型 ('transcribe' 或 'translate')
            verbose (bool): 是否显示详细日志
        """
        self.model_name = model_name
        self.language = language
        self.task = task
        self.verbose = verbose
        
        # 设备检测
        if device is None:
            self.device = "cuda" if torch.cuda.is_available() else "cpu"
        else:
            self.device = device
        
        logger.info(f"正在加载 Whisper {model_name} 模型...")
        self.model = whisper.load_model(model_name, device=self.device)
        logger.info(f"模型加载完成。使用设备: {self.device}")
    
    def check_file_exists(self, file_path: str) -> bool:
        """检查文件是否存在"""
        if not os.path.exists(file_path):
            logger.error(f"文件不存在: {file_path}")
            return False
        return True
    
    def extract_audio(self, video_path: str) -> Tuple[str, bool]:
        """
        从视频文件中提取音频
        
        参数:
            video_path (str): 视频文件路径
            
        返回:
            Tuple[str, bool]: (音频文件路径, 是否为临时文件)
        """
        if not self.check_file_exists(video_path):
            return None, False
            
        file_ext = os.path.splitext(video_path)[1].lower()
        
        # 如果已经是音频文件，直接返回
        if file_ext in ['.mp3', '.wav', '.flac', '.ogg', '.aac']:
            logger.info(f"输入已经是音频文件: {video_path}")
            return video_path, False
        
        # 提取音频到临时文件
        temp_audio = tempfile.NamedTemporaryFile(suffix='.wav', delete=False)
        temp_audio.close()
        
        logger.info(f"正在从视频中提取音频...")
        try:
            command = ["ffmpeg", "-i", video_path, "-q:a", "0", "-map", "a", "-c:a", "pcm_s16le", temp_audio.name, "-y"]
            if not self.verbose:
                command.extend(["-hide_banner", "-loglevel", "error"])
                
            subprocess.run(command, check=True)
            logger.info(f"音频提取完成: {temp_audio.name}")
            return temp_audio.name, True
        except subprocess.CalledProcessError as e:
            logger.error(f"音频提取失败: {e}")
            os.unlink(temp_audio.name)
            return None, False
    
    def transcribe(self, audio_path: str) -> Dict[str, Any]:
        """
        使用Whisper模型转录音频
        
        参数:
            audio_path (str): 音频文件路径
            
        返回:
            Dict: 包含转录结果的字典
        """
        if not self.check_file_exists(audio_path):
            return None
            
        logger.info(f"正在转录音频: {audio_path}")
        
        # 准备转录选项
        transcribe_options = {
            "task": self.task,
            "verbose": self.verbose,
        }
        
        if self.language:
            transcribe_options["language"] = self.language
            
        # 执行转录
        try:
            result = self.model.transcribe(audio_path, **transcribe_options)
            if self.language is None:
                detected_lang = result.get("language", "未知")
                logger.info(f"检测到语言: {detected_lang}")
            return result
        except Exception as e:
            logger.error(f"转录过程中出错: {e}")
            return None
    
    def format_timestamp(self, seconds: float) -> str:
        """将秒数转换为SRT时间戳格式 (HH:MM:SS,mmm)"""
        milliseconds = int(seconds * 1000) % 1000
        seconds = int(seconds)
        minutes = seconds // 60
        seconds = seconds % 60
        hours = minutes // 60
        minutes = minutes % 60
        return f"{hours:02d}:{minutes:02d}:{seconds:02d},{milliseconds:03d}"
    
    def save_subtitles(self, result: Dict[str, Any], output_path: str, format: str = "srt") -> bool:
        """
        将转录结果保存为指定格式的字幕文件
        
        参数:
            result (Dict): Whisper转录结果
            output_path (str): 输出文件路径
            format (str): 字幕格式 (srt, vtt, txt, json, tsv)
            
        返回:
            bool: 是否成功
        """
        if result is None or "segments" not in result:
            logger.error("转录结果无效，无法生成字幕")
            return False
            
        format = format.lower()
        if format not in SUBTITLE_FORMATS:
            logger.error(f"不支持的字幕格式: {format}，支持的格式: {', '.join(SUBTITLE_FORMATS)}")
            return False
        
        # 确保输出目录存在
        os.makedirs(os.path.dirname(os.path.abspath(output_path)), exist_ok=True)
        
        try:
            # JSON格式直接使用whisper内置方法
            if format == "json":
                with open(output_path, "w", encoding="utf-8") as f:
                    import json
                    json.dump(result, f, ensure_ascii=False, indent=2)
                logger.info(f"已保存JSON格式字幕: {output_path}")
                return True
                
            # TSV格式也使用whisper内置方法
            elif format == "tsv":
                with open(output_path, "w", encoding="utf-8") as f:
                    print("start", "end", "text", sep="\t", file=f)
                    for segment in result["segments"]:
                        print(segment["start"], segment["end"], segment["text"], sep="\t", file=f)
                logger.info(f"已保存TSV格式字幕: {output_path}")
                return True
                
            # 纯文本格式
            elif format == "txt":
                with open(output_path, "w", encoding="utf-8") as f:
                    for segment in result["segments"]:
                        print(segment["text"].strip(), file=f)
                logger.info(f"已保存TXT格式字幕: {output_path}")
                return True
                
            # SRT格式
            elif format == "srt":
                with open(output_path, "w", encoding="utf-8") as f:
                    for i, segment in enumerate(result["segments"], start=1):
                        start = self.format_timestamp(segment["start"])
                        end = self.format_timestamp(segment["end"])
                        text = segment["text"].strip()
                        print(f"{i}\n{start} --> {end}\n{text}\n", file=f)
                logger.info(f"已保存SRT格式字幕: {output_path}")
                return True
                
            # VTT格式
            elif format == "vtt":
                with open(output_path, "w", encoding="utf-8") as f:
                    print("WEBVTT\n", file=f)
                    for segment in result["segments"]:
                        start = self.format_timestamp(segment["start"]).replace(",", ".")
                        end = self.format_timestamp(segment["end"]).replace(",", ".")
                        text = segment["text"].strip()
                        print(f"{start} --> {end}\n{text}\n", file=f)
                logger.info(f"已保存VTT格式字幕: {output_path}")
                return True
                
        except Exception as e:
            logger.error(f"保存字幕时出错: {e}")
            return False
            
        return False
    
    def generate_subtitles(self, input_path: str, output_path: Optional[str] = None, 
                          formats: List[str] = ["srt"]) -> bool:
        """
        主要处理函数：从视频/音频生成字幕
        
        参数:
            input_path (str): 输入视频/音频文件路径
            output_path (str): 输出字幕文件路径(不含扩展名)，None=使用输入路径
            formats (List[str]): 要生成的字幕格式列表
            
        返回:
            bool: 是否成功
        """
        # 提取音频（如果是视频文件）
        audio_path, is_temp = self.extract_audio(input_path)
        if not audio_path:
            return False
            
        try:
            # 转录
            start_time = time.time()
            result = self.transcribe(audio_path)
            if not result:
                return False
                
            # 如果是临时音频文件，处理完成后删除
            if is_temp:
                os.unlink(audio_path)
                
            # 计算转录时间
            elapsed = time.time() - start_time
            audio_duration = result.get("segments", [{}])[-1].get("end", 0) if result.get("segments") else 0
            logger.info(f"转录完成！处理 {audio_duration:.2f} 秒的音频用时 {elapsed:.2f} 秒 "
                       f"(处理速度: {audio_duration/elapsed:.2f}x)")
            
            # 确定输出路径
            if output_path is None:
                output_base = os.path.splitext(input_path)[0]
            else:
                output_base = output_path
                
            # 保存各种格式
            success = False
            for fmt in formats:
                fmt_output = f"{output_base}.{fmt}"
                if self.save_subtitles(result, fmt_output, fmt):
                    success = True
                    
            return success
            
        except Exception as e:
            logger.error(f"生成字幕过程中出错: {e}")
            # 如果是临时音频文件，确保清理
            if is_temp and audio_path and os.path.exists(audio_path):
                os.unlink(audio_path)
            return False


def parse_arguments():
    """解析命令行参数"""
    parser = argparse.ArgumentParser(
        description="使用OpenAI的Whisper模型从视频或音频文件中生成字幕",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter
    )
    
    parser.add_argument(
        "input",
        help="输入视频或音频文件路径"
    )
    
    parser.add_argument(
        "-o", "--output",
        help="输出字幕文件路径(不含扩展名)，默认使用输入文件路径",
        default=None
    )
    
    parser.add_argument(
        "-m", "--model",
        help="Whisper模型大小",
        choices=["tiny", "base", "small", "medium", "large", "turbo"],
        default="medium"
    )
    
    parser.add_argument(
        "-l", "--language",
        help="音频语言(如zh，en，ja)，默认自动检测",
        default=None
    )
    
    parser.add_argument(
        "-t", "--task",
        help="任务类型",
        choices=["transcribe", "translate"],
        default="transcribe"
    )
    
    parser.add_argument(
        "-d", "--device",
        help="计算设备",
        choices=["cpu", "cuda"],
        default=None
    )
    
    parser.add_argument(
        "-f", "--formats",
        help="要生成的字幕格式，可指定多个",
        nargs="+",
        choices=SUBTITLE_FORMATS,
        default=["srt"]
    )
    
    parser.add_argument(
        "-v", "--verbose",
        help="显示详细日志",
        action="store_true"
    )
    
    return parser.parse_args()


def main():
    """主函数"""
    args = parse_arguments()
    
    start_time = time.time()
    
    # 检查FFMPEG是否安装
    try:
        subprocess.run(["ffmpeg", "-version"], stdout=subprocess.PIPE, stderr=subprocess.PIPE, check=True)
    except (subprocess.SubprocessError, FileNotFoundError):
        logger.error("未检测到FFMPEG。请先安装FFMPEG: https://ffmpeg.org/download.html")
        return 1
    
    # 创建字幕生成器实例
    subtitle_generator = SubtitleGenerator(
        model_name=args.model,
        device=args.device,
        language=args.language, 
        task=args.task,
        verbose=args.verbose
    )
    
    # 生成字幕
    success = subtitle_generator.generate_subtitles(
        input_path=args.input,
        output_path=args.output,
        formats=args.formats
    )
    
    if success:
        elapsed = time.time() - start_time
        logger.info(f"字幕生成完成！总耗时: {elapsed:.2f} 秒")
        return 0
    else:
        logger.error("字幕生成失败")
        return 1


if __name__ == "__main__":
    sys.exit(main()) 