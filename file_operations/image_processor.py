#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
图像批处理工具

这个脚本提供了批量处理图像的功能，包括调整大小、格式转换、添加水印、
应用滤镜效果等。支持递归处理整个目录结构，并提供多种输出选项。
适用于摄影整理、网站图片优化、社交媒体内容准备等场景。
"""

import argparse
import fnmatch
import logging
import os
import queue
import sys
import threading
import time
from datetime import datetime
from enum import Enum
from typing import List, Dict, Optional, Tuple, Any

try:
    from PIL import Image, ImageDraw, ImageFont, ImageEnhance, ImageFilter, ExifTags
    import PIL
except ImportError:
    print("错误：缺少必要的依赖库。请安装Pillow库：")
    print("pip install Pillow")
    sys.exit(1)

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)
logger = logging.getLogger(__name__)


class ResizeMode(Enum):
    """调整大小模式枚举"""
    PERCENT = "percent"  # 按百分比缩放
    EXACT = "exact"  # 精确尺寸（可能改变纵横比）
    FIT = "fit"  # 适应指定尺寸（保持纵横比，不裁剪）
    FILL = "fill"  # 填充指定尺寸（保持纵横比，可能裁剪）
    WIDTH = "width"  # 指定宽度（保持纵横比）
    HEIGHT = "height"  # 指定高度（保持纵横比）


class WatermarkPosition(Enum):
    """水印位置枚举"""
    TOP_LEFT = "top-left"
    TOP_CENTER = "top-center"
    TOP_RIGHT = "top-right"
    CENTER_LEFT = "center-left"
    CENTER = "center"
    CENTER_RIGHT = "center-right"
    BOTTOM_LEFT = "bottom-left"
    BOTTOM_CENTER = "bottom-center"
    BOTTOM_RIGHT = "bottom-right"
    TILED = "tiled"  # 平铺水印
    CUSTOM = "custom"  # 自定义位置（x,y坐标）


class FilterType(Enum):
    """图像滤镜类型枚举"""
    BLUR = "blur"  # 模糊
    SHARPEN = "sharpen"  # 锐化
    CONTOUR = "contour"  # 轮廓
    DETAIL = "detail"  # 细节增强
    EDGE_ENHANCE = "edge"  # 边缘增强
    EMBOSS = "emboss"  # 浮雕
    SMOOTH = "smooth"  # 平滑
    GRAYSCALE = "grayscale"  # 灰度
    SEPIA = "sepia"  # 棕褐色
    NEGATIVE = "negative"  # 负片


class OutputMode(Enum):
    """输出模式枚举"""
    SAME_DIR = "same"  # 输出到原目录
    SUBFOLDER = "subfolder"  # 输出到子文件夹
    CUSTOM_DIR = "custom"  # 输出到自定义目录
    REPLACE = "replace"  # 替换原文件


class ImageProcessor:
    """图像处理器类，提供批量处理图像的功能"""

    # 支持的图像格式
    SUPPORTED_FORMATS = {'.jpg', '.jpeg', '.png', '.gif', '.bmp', '.tiff', '.webp'}

    def __init__(
            self,
            input_paths: List[str],
            output_mode: OutputMode = OutputMode.SUBFOLDER,
            output_dir: str = "processed_images",
            recursive: bool = False,
            include_patterns: Optional[List[str]] = None,
            exclude_patterns: Optional[List[str]] = None,
            output_format: Optional[str] = None,
            output_quality: int = 85,
            output_pattern: str = "{basename}{suffix}{extension}",
            resize_mode: Optional[ResizeMode] = None,
            resize_params: Optional[Dict[str, Any]] = None,
            watermark_text: Optional[str] = None,
            watermark_image: Optional[str] = None,
            watermark_position: WatermarkPosition = WatermarkPosition.BOTTOM_RIGHT,
            watermark_opacity: int = 50,
            filter_type: Optional[FilterType] = None,
            brightness: Optional[float] = None,
            contrast: Optional[float] = None,
            color: Optional[float] = None,
            sharpness: Optional[float] = None,
            rotate_angle: Optional[float] = None,
            flip_horizontal: bool = False,
            flip_vertical: bool = False,
            keep_exif: bool = True,
            exif_data: Optional[Dict[str, str]] = None,
            threads: int = 1,
            dry_run: bool = False,
            verbose: bool = False
    ):
        """
        初始化图像处理器
        
        Args:
            input_paths: 输入路径列表（文件或目录）
            output_mode: 输出模式
            output_dir: 输出目录（当output_mode为SUBFOLDER或CUSTOM_DIR时使用）
            recursive: 是否递归处理子目录
            include_patterns: 要包含的文件模式列表（如 *.jpg, *.png）
            exclude_patterns: 要排除的文件模式列表
            output_format: 输出格式（如 jpg, png, webp）
            output_quality: 输出质量（1-100，仅对jpg、webp等有效）
            output_pattern: 输出文件名模式
            resize_mode: 调整大小模式
            resize_params: 调整大小参数
            watermark_text: 水印文本
            watermark_image: 水印图像路径
            watermark_position: 水印位置
            watermark_opacity: 水印不透明度（0-100）
            filter_type: 滤镜类型
            brightness: 亮度调整（0.0-2.0，1.0为原始亮度）
            contrast: 对比度调整（0.0-2.0，1.0为原始对比度）
            color: 色彩调整（0.0-2.0，1.0为原始色彩）
            sharpness: 锐度调整（0.0-2.0，1.0为原始锐度）
            rotate_angle: 旋转角度
            flip_horizontal: 是否水平翻转
            flip_vertical: 是否垂直翻转
            keep_exif: 是否保留EXIF数据
            exif_data: 要添加/修改的EXIF数据
            threads: 线程数
            dry_run: 是否模拟运行
            verbose: 是否显示详细信息
        """
        self.input_paths = input_paths
        self.output_mode = output_mode
        self.output_dir = output_dir
        self.recursive = recursive
        self.include_patterns = include_patterns or ["*.*"]
        self.exclude_patterns = exclude_patterns or []
        self.output_format = output_format.lower() if output_format else None
        self.output_quality = output_quality
        self.output_pattern = output_pattern
        self.resize_mode = resize_mode
        self.resize_params = resize_params or {}
        self.watermark_text = watermark_text
        self.watermark_image = watermark_image
        self.watermark_position = watermark_position
        self.watermark_opacity = watermark_opacity
        self.filter_type = filter_type
        self.brightness = brightness
        self.contrast = contrast
        self.color = color
        self.sharpness = sharpness
        self.rotate_angle = rotate_angle
        self.flip_horizontal = flip_horizontal
        self.flip_vertical = flip_vertical
        self.keep_exif = keep_exif
        self.exif_data = exif_data or {}
        self.threads = max(1, min(threads, 16))  # 限制线程数在1-16之间
        self.dry_run = dry_run
        self.verbose = verbose

        # 处理统计信息
        self.processed_files = 0
        self.skipped_files = 0
        self.error_files = 0
        self.start_time = 0
        self.errors = []

        # 确保支持的输出格式
        if self.output_format and not self.output_format.startswith('.'):
            self.output_format = '.' + self.output_format

        # 加载水印图像（如果指定）
        self.watermark_img = None
        if self.watermark_image and os.path.isfile(self.watermark_image):
            try:
                self.watermark_img = Image.open(self.watermark_image).convert("RGBA")
                if self.verbose:
                    logger.info(f"已加载水印图像: {self.watermark_image}")
            except Exception as e:
                logger.error(f"加载水印图像失败: {e}")
                self.errors.append(f"水印图像加载错误: {e}")

    def process_images(self) -> bool:
        """
        处理所有图像
        
        Returns:
            bool: 处理是否成功
        """
        self.processed_files = 0
        self.skipped_files = 0
        self.error_files = 0
        self.errors = []
        self.start_time = time.time()

        # 收集需要处理的文件
        image_files = self._collect_image_files()
        total_files = len(image_files)

        if total_files == 0:
            logger.warning("没有找到匹配的图像文件")
            return False

        logger.info(f"找到 {total_files} 个图像文件需要处理")

        if self.dry_run:
            logger.info("模拟运行模式：不会实际修改文件")
            for file_path in image_files:
                output_path = self._get_output_path(file_path)
                logger.info(f"将处理: {file_path} -> {output_path}")
            return True

        # 单线程处理
        if self.threads == 1:
            for file_path in image_files:
                self._process_single_image(file_path)
        # 多线程处理
        else:
            self._process_images_parallel(image_files)

        # 打印汇总信息
        elapsed_time = time.time() - self.start_time
        logger.info(f"处理完成. 耗时: {elapsed_time:.2f}秒")
        logger.info(f"成功: {self.processed_files}, 跳过: {self.skipped_files}, 错误: {self.error_files}")

        if self.errors:
            logger.warning("处理过程中出现以下错误:")
            for error in self.errors:
                logger.warning(f"  - {error}")

        return self.error_files == 0

    def _collect_image_files(self) -> List[str]:
        """
        收集所有需要处理的图像文件
        
        Returns:
            符合条件的图像文件路径列表
        """
        image_files = []

        for input_path in self.input_paths:
            if os.path.isfile(input_path):
                # 单个文件，检查是否是支持的图像格式
                if self._is_supported_image(input_path):
                    image_files.append(input_path)
            elif os.path.isdir(input_path):
                # 目录，遍历收集图像文件
                for root, dirs, files in os.walk(input_path):
                    # 处理当前目录中的文件
                    for filename in files:
                        file_path = os.path.join(root, filename)
                        if self._should_process_file(file_path):
                            image_files.append(file_path)

                    # 如果不递归处理子目录，跳出循环
                    if not self.recursive:
                        break
            else:
                logger.warning(f"路径不存在或无法访问: {input_path}")

        return image_files

    def _is_supported_image(self, file_path: str) -> bool:
        """
        检查文件是否是支持的图像格式
        
        Args:
            file_path: 文件路径
            
        Returns:
            是否是支持的图像格式
        """
        ext = os.path.splitext(file_path)[1].lower()
        return ext in self.SUPPORTED_FORMATS

    def _should_process_file(self, file_path: str) -> bool:
        """
        检查是否应处理该文件
        
        Args:
            file_path: 文件路径
            
        Returns:
            是否应处理该文件
        """
        # 检查文件是否存在
        if not os.path.isfile(file_path):
            return False

        # 检查是否是支持的图像格式
        if not self._is_supported_image(file_path):
            return False

        # 检查文件名匹配
        filename = os.path.basename(file_path)

        # 检查是否符合包含模式
        included = any(fnmatch.fnmatch(filename, pattern) for pattern in self.include_patterns)
        if not included:
            return False

        # 检查是否符合排除模式
        excluded = any(fnmatch.fnmatch(filename, pattern) for pattern in self.exclude_patterns)
        if excluded:
            return False

        return True

    def _get_output_path(self, input_path: str) -> str:
        """
        获取输出文件路径
        
        Args:
            input_path: 输入文件路径
            
        Returns:
            输出文件路径
        """
        dir_path, filename = os.path.split(input_path)
        basename, extension = os.path.splitext(filename)

        # 如果指定了输出格式，使用新的扩展名
        if self.output_format:
            extension = self.output_format if self.output_format.startswith('.') else '.' + self.output_format

        # 构建输出文件名
        suffix = ""
        if self.resize_mode:
            suffix += "_resized"
        if self.watermark_text or self.watermark_image:
            suffix += "_watermarked"
        if self.filter_type:
            suffix += f"_{self.filter_type.value}"

        # 应用输出文件名模式
        output_filename = self.output_pattern.format(
            basename=basename,
            extension=extension,
            suffix=suffix,
            date=datetime.now().strftime("%Y%m%d"),
            time=datetime.now().strftime("%H%M%S")
        )

        # 确定输出目录
        if self.output_mode == OutputMode.REPLACE:
            output_dir = dir_path
        elif self.output_mode == OutputMode.SAME_DIR:
            output_dir = dir_path
        elif self.output_mode == OutputMode.SUBFOLDER:
            output_dir = os.path.join(dir_path, self.output_dir)
        else:  # OutputMode.CUSTOM_DIR
            output_dir = self.output_dir

        # 确保输出目录存在
        if not self.dry_run and not os.path.exists(output_dir):
            os.makedirs(output_dir, exist_ok=True)

        return os.path.join(output_dir, output_filename)

    def _process_images_parallel(self, image_files: List[str]):
        """
        并行处理多个图像文件
        
        Args:
            image_files: 图像文件路径列表
        """
        file_queue = queue.Queue()
        lock = threading.Lock()

        # 将文件添加到队列
        for file_path in image_files:
            file_queue.put(file_path)

        # 线程处理函数
        def worker():
            while True:
                try:
                    file_path = file_queue.get(block=False)
                except queue.Empty:
                    break

                try:
                    success = self._process_single_image(file_path)
                    with lock:
                        if success:
                            self.processed_files += 1
                        else:
                            self.skipped_files += 1
                except Exception as e:
                    with lock:
                        self.error_files += 1
                        error_msg = f"处理文件 {file_path} 时出错: {str(e)}"
                        self.errors.append(error_msg)
                        if self.verbose:
                            logger.error(error_msg)

                finally:
                    file_queue.task_done()

        # 创建和启动线程
        threads = []
        for _ in range(self.threads):
            thread = threading.Thread(target=worker)
            thread.start()
            threads.append(thread)

        # 等待所有线程完成
        for thread in threads:
            thread.join()

    def _process_single_image(self, input_path: str) -> bool:
        """
        处理单个图像文件
        
        Args:
            input_path: 输入文件路径
            
        Returns:
            处理是否成功
        """
        try:
            if self.verbose:
                logger.info(f"正在处理: {input_path}")

            # 打开图像
            img = Image.open(input_path)

            # 保存原始EXIF数据
            exif_data = None
            if self.keep_exif and 'exif' in img.info:
                exif_data = img.info['exif']

            # 应用各种处理
            if self.resize_mode:
                img = self._resize_image(img)

            if self.rotate_angle is not None:
                img = img.rotate(self.rotate_angle, expand=True)

            if self.flip_horizontal:
                img = img.transpose(Image.FLIP_LEFT_RIGHT)

            if self.flip_vertical:
                img = img.transpose(Image.FLIP_TOP_BOTTOM)

            if self.brightness is not None:
                enhancer = ImageEnhance.Brightness(img)
                img = enhancer.enhance(self.brightness)

            if self.contrast is not None:
                enhancer = ImageEnhance.Contrast(img)
                img = enhancer.enhance(self.contrast)

            if self.color is not None:
                enhancer = ImageEnhance.Color(img)
                img = enhancer.enhance(self.color)

            if self.sharpness is not None:
                enhancer = ImageEnhance.Sharpness(img)
                img = enhancer.enhance(self.sharpness)

            if self.filter_type:
                img = self._apply_filter(img)

            if self.watermark_text:
                img = self._add_text_watermark(img)

            if self.watermark_img:
                img = self._add_image_watermark(img)

            # 获取输出路径
            output_path = self._get_output_path(input_path)

            # 如果是替换模式，并且输出文件名与输入文件相同，生成临时文件再替换
            if self.output_mode == OutputMode.REPLACE and output_path == input_path:
                temp_output = output_path + ".tmp"
                self._save_image(img, temp_output, exif_data)
                os.replace(temp_output, output_path)
            else:
                self._save_image(img, output_path, exif_data)

            if self.verbose:
                logger.info(f"已保存: {output_path}")

            return True

        except Exception as e:
            error_msg = f"处理文件 {input_path} 时出错: {str(e)}"
            self.errors.append(error_msg)
            self.error_files += 1
            logger.error(error_msg)
            return False

    def _resize_image(self, img: Image.Image) -> Image.Image:
        """
        调整图像大小
        
        Args:
            img: 原始图像
            
        Returns:
            调整大小后的图像
        """
        if not self.resize_mode:
            return img

        original_width, original_height = img.size

        if self.resize_mode == ResizeMode.PERCENT:
            percent = self.resize_params.get('percent', 100) / 100
            new_width = int(original_width * percent)
            new_height = int(original_height * percent)
            return img.resize((new_width, new_height), Image.LANCZOS)

        elif self.resize_mode == ResizeMode.EXACT:
            width = self.resize_params.get('width', original_width)
            height = self.resize_params.get('height', original_height)
            return img.resize((width, height), Image.LANCZOS)

        elif self.resize_mode == ResizeMode.FIT:
            max_width = self.resize_params.get('width', original_width)
            max_height = self.resize_params.get('height', original_height)

            # 计算适应尺寸（保持纵横比）
            width_ratio = max_width / original_width
            height_ratio = max_height / original_height
            ratio = min(width_ratio, height_ratio)

            new_width = int(original_width * ratio)
            new_height = int(original_height * ratio)

            return img.resize((new_width, new_height), Image.LANCZOS)

        elif self.resize_mode == ResizeMode.FILL:
            target_width = self.resize_params.get('width', original_width)
            target_height = self.resize_params.get('height', original_height)

            # 计算填充尺寸（保持纵横比，可能需要裁剪）
            width_ratio = target_width / original_width
            height_ratio = target_height / original_height
            ratio = max(width_ratio, height_ratio)

            new_width = int(original_width * ratio)
            new_height = int(original_height * ratio)

            # 调整大小
            resized_img = img.resize((new_width, new_height), Image.LANCZOS)

            # 裁剪到目标尺寸
            left = (new_width - target_width) // 2
            top = (new_height - target_height) // 2
            right = left + target_width
            bottom = top + target_height

            return resized_img.crop((left, top, right, bottom))

        elif self.resize_mode == ResizeMode.WIDTH:
            target_width = self.resize_params.get('width', original_width)
            ratio = target_width / original_width
            new_height = int(original_height * ratio)

            return img.resize((target_width, new_height), Image.LANCZOS)

        elif self.resize_mode == ResizeMode.HEIGHT:
            target_height = self.resize_params.get('height', original_height)
            ratio = target_height / original_height
            new_width = int(original_width * ratio)

            return img.resize((new_width, target_height), Image.LANCZOS)

        return img

    def _add_text_watermark(self, img: Image.Image) -> Image.Image:
        """
        添加文本水印
        
        Args:
            img: 原始图像
            
        Returns:
            添加水印后的图像
        """
        if not self.watermark_text:
            return img

        # 创建透明图层用于绘制水印
        watermark = Image.new('RGBA', img.size, (0, 0, 0, 0))
        draw = ImageDraw.Draw(watermark)

        # 尝试加载字体，如果失败则使用默认字体
        font_size = self.resize_params.get('font_size', 36)
        font_path = self.resize_params.get('font_path', None)
        try:
            if font_path and os.path.exists(font_path):
                font = ImageFont.truetype(font_path, font_size)
            else:
                # 使用PIL默认字体
                font = ImageFont.load_default()
        except Exception:
            font = ImageFont.load_default()

        # 获取水印文本尺寸
        text_width, text_height = draw.textsize(self.watermark_text, font=font)

        # 确定水印位置
        img_width, img_height = img.size
        position = self._get_watermark_position(img_width, img_height, text_width, text_height)

        # 文本颜色和透明度
        text_color = self.resize_params.get('text_color', (255, 255, 255, int(255 * self.watermark_opacity / 100)))

        # 绘制水印文本
        if self.watermark_position == WatermarkPosition.TILED:
            # 平铺水印
            for y in range(0, img_height, text_height + 50):
                for x in range(0, img_width, text_width + 50):
                    draw.text((x, y), self.watermark_text, font=font, fill=text_color)
        else:
            # 单个水印
            draw.text(position, self.watermark_text, font=font, fill=text_color)

        # 合并水印图层和原图
        return Image.alpha_composite(img.convert('RGBA'), watermark).convert('RGB')

    def _add_image_watermark(self, img: Image.Image) -> Image.Image:
        """
        添加图像水印
        
        Args:
            img: 原始图像
            
        Returns:
            添加水印后的图像
        """
        if not self.watermark_img:
            return img

        # 确保原图和水印都是RGBA模式
        img = img.convert('RGBA')
        watermark = self.watermark_img.copy()

        # 调整水印大小
        scale = self.resize_params.get('watermark_scale', 0.2)  # 默认水印为图像的20%
        if scale > 0:
            wm_width = int(img.width * scale)
            wm_height = int(watermark.height * (wm_width / watermark.width))
            watermark = watermark.resize((wm_width, wm_height), Image.LANCZOS)

        # 调整水印透明度
        if self.watermark_opacity < 100:
            watermark.putalpha(int(watermark.getchannel('A') * self.watermark_opacity / 100))

        # 确定水印位置
        img_width, img_height = img.size
        wm_width, wm_height = watermark.size
        position = self._get_watermark_position(img_width, img_height, wm_width, wm_height)

        # 创建新图像用于合成
        result = Image.new('RGBA', img.size, (0, 0, 0, 0))
        result.paste(img, (0, 0))

        if self.watermark_position == WatermarkPosition.TILED:
            # 平铺水印
            for y in range(0, img_height, wm_height + 20):
                for x in range(0, img_width, wm_width + 20):
                    result.paste(watermark, (x, y), watermark)
        else:
            # 单个水印
            result.paste(watermark, position, watermark)

        return result.convert('RGB')

    def _get_watermark_position(self, img_width: int, img_height: int, wm_width: int, wm_height: int) -> Tuple[
        int, int]:
        """
        计算水印位置
        
        Args:
            img_width: 图像宽度
            img_height: 图像高度
            wm_width: 水印宽度
            wm_height: 水印高度
            
        Returns:
            水印位置坐标 (x, y)
        """
        margin = 10  # 水印到边缘的距离

        if self.watermark_position == WatermarkPosition.TOP_LEFT:
            return (margin, margin)
        elif self.watermark_position == WatermarkPosition.TOP_CENTER:
            return ((img_width - wm_width) // 2, margin)
        elif self.watermark_position == WatermarkPosition.TOP_RIGHT:
            return (img_width - wm_width - margin, margin)
        elif self.watermark_position == WatermarkPosition.CENTER_LEFT:
            return (margin, (img_height - wm_height) // 2)
        elif self.watermark_position == WatermarkPosition.CENTER:
            return ((img_width - wm_width) // 2, (img_height - wm_height) // 2)
        elif self.watermark_position == WatermarkPosition.CENTER_RIGHT:
            return (img_width - wm_width - margin, (img_height - wm_height) // 2)
        elif self.watermark_position == WatermarkPosition.BOTTOM_LEFT:
            return (margin, img_height - wm_height - margin)
        elif self.watermark_position == WatermarkPosition.BOTTOM_CENTER:
            return ((img_width - wm_width) // 2, img_height - wm_height - margin)
        elif self.watermark_position == WatermarkPosition.BOTTOM_RIGHT:
            return (img_width - wm_width - margin, img_height - wm_height - margin)
        elif self.watermark_position == WatermarkPosition.CUSTOM:
            custom_x = self.resize_params.get('watermark_x', 0)
            custom_y = self.resize_params.get('watermark_y', 0)
            return (custom_x, custom_y)
        else:
            return (margin, margin)  # 默认左上角

    def _apply_filter(self, img: Image.Image) -> Image.Image:
        """
        应用图像滤镜
        
        Args:
            img: 原始图像
            
        Returns:
            应用滤镜后的图像
        """
        if not self.filter_type:
            return img

        if self.filter_type == FilterType.BLUR:
            return img.filter(ImageFilter.BLUR)
        elif self.filter_type == FilterType.SHARPEN:
            return img.filter(ImageFilter.SHARPEN)
        elif self.filter_type == FilterType.CONTOUR:
            return img.filter(ImageFilter.CONTOUR)
        elif self.filter_type == FilterType.DETAIL:
            return img.filter(ImageFilter.DETAIL)
        elif self.filter_type == FilterType.EDGE_ENHANCE:
            return img.filter(ImageFilter.EDGE_ENHANCE)
        elif self.filter_type == FilterType.EMBOSS:
            return img.filter(ImageFilter.EMBOSS)
        elif self.filter_type == FilterType.SMOOTH:
            return img.filter(ImageFilter.SMOOTH)
        elif self.filter_type == FilterType.GRAYSCALE:
            return img.convert('L').convert('RGB')
        elif self.filter_type == FilterType.SEPIA:
            # 创建棕褐色滤镜
            sepia_data = []
            for i in range(256):
                r = min(255, int(i * 0.393 + 0.769 * i + 0.189 * i))
                g = min(255, int(i * 0.349 + 0.686 * i + 0.168 * i))
                b = min(255, int(i * 0.272 + 0.534 * i + 0.131 * i))
                sepia_data.append((r, g, b))
            grayscale = img.convert('L')
            return grayscale.point(lambda i: sepia_data[i][0], 'L').convert('RGB')
        elif self.filter_type == FilterType.NEGATIVE:
            return PIL.ImageOps.invert(img)
        else:
            return img

    def _save_image(self, img: Image.Image, output_path: str, exif_data: Optional[bytes] = None):
        """
        保存图像
        
        Args:
            img: 图像对象
            output_path: 输出路径
            exif_data: EXIF数据
        """
        # 确保输出目录存在
        output_dir = os.path.dirname(output_path)
        if not os.path.exists(output_dir):
            os.makedirs(output_dir, exist_ok=True)

        # 确定保存格式
        format_name = os.path.splitext(output_path)[1][1:].upper()
        if format_name == 'JPG':
            format_name = 'JPEG'

        # 构建保存参数
        save_args = {}

        # 添加质量参数
        if format_name in ['JPEG', 'WEBP']:
            save_args['quality'] = self.output_quality

        # 添加EXIF数据
        if exif_data and self.keep_exif and format_name == 'JPEG':
            save_args['exif'] = exif_data

        # 添加额外的自定义EXIF数据
        if self.exif_data and format_name == 'JPEG':
            # TODO: 处理自定义EXIF数据
            pass

        # 保存图像
        img.save(output_path, format=format_name, **save_args)


def parse_arguments():
    """解析命令行参数"""
    parser = argparse.ArgumentParser(description="图像批处理工具 - 批量调整图像大小、格式转换、添加水印等")

    # 基本参数
    parser.add_argument('input_paths', nargs='+', help='输入图像或目录路径列表')
    parser.add_argument('-r', '--recursive', action='store_true', help='递归处理子目录')
    parser.add_argument('-v', '--verbose', action='store_true', help='显示详细信息')
    parser.add_argument('-n', '--dry-run', action='store_true', help='模拟运行，不实际修改文件')
    parser.add_argument('-t', '--threads', type=int, default=1, help='处理线程数（默认: 1）')

    # 输出选项
    output_group = parser.add_argument_group('输出选项')
    output_mode = output_group.add_mutually_exclusive_group()
    output_mode.add_argument('--same-dir', action='store_true', help='输出到原目录')
    output_mode.add_argument('--subfolder', dest='output_subfolder', help='输出到子文件夹（默认: processed_images）')
    output_mode.add_argument('--output-dir', dest='output_dir', help='输出到自定义目录')
    output_mode.add_argument('--replace', action='store_true', help='替换原始文件')
    output_group.add_argument('--output-format', help='输出格式（如 jpg, png, webp）')
    output_group.add_argument('--quality', type=int, default=85, help='输出质量 1-100（默认: 85）')
    output_group.add_argument('--output-pattern', default="{basename}{suffix}{extension}",
                              help='输出文件名模式（默认: "{basename}{suffix}{extension}"）')

    # 文件过滤选项
    filter_group = parser.add_argument_group('文件过滤选项')
    filter_group.add_argument('-i', '--include', nargs='+', metavar='PATTERN', help='要包含的文件模式列表（如 *.jpg）')
    filter_group.add_argument('-e', '--exclude', nargs='+', metavar='PATTERN', help='要排除的文件模式列表')

    # 调整大小选项
    resize_group = parser.add_argument_group('调整大小选项')
    resize_mode = resize_group.add_mutually_exclusive_group()
    resize_mode.add_argument('--resize-percent', type=float, help='按百分比调整大小（如50表示缩小一半）')
    resize_mode.add_argument('--resize-exact', nargs=2, type=int, metavar=('WIDTH', 'HEIGHT'),
                             help='调整为精确尺寸（可能改变纵横比）')
    resize_mode.add_argument('--resize-fit', nargs=2, type=int, metavar=('WIDTH', 'HEIGHT'),
                             help='适应指定尺寸（保持纵横比，不裁剪）')
    resize_mode.add_argument('--resize-fill', nargs=2, type=int, metavar=('WIDTH', 'HEIGHT'),
                             help='填充指定尺寸（保持纵横比，可能裁剪）')
    resize_mode.add_argument('--resize-width', type=int, help='指定宽度（保持纵横比）')
    resize_mode.add_argument('--resize-height', type=int, help='指定高度（保持纵横比）')

    # 水印选项
    watermark_group = parser.add_argument_group('水印选项')
    watermark_type = watermark_group.add_mutually_exclusive_group()
    watermark_type.add_argument('--text-watermark', help='文本水印内容')
    watermark_type.add_argument('--image-watermark', help='图像水印文件路径')
    watermark_group.add_argument('--watermark-position',
                                 choices=[pos.value for pos in WatermarkPosition],
                                 default=WatermarkPosition.BOTTOM_RIGHT.value,
                                 help=f'水印位置（默认: {WatermarkPosition.BOTTOM_RIGHT.value}）')
    watermark_group.add_argument('--watermark-opacity', type=int, default=50,
                                 help='水印不透明度 0-100（默认: 50）')
    watermark_group.add_argument('--font-size', type=int, default=36,
                                 help='文本水印字体大小（默认: 36）')
    watermark_group.add_argument('--font-path', help='文本水印字体文件路径')
    watermark_group.add_argument('--text-color', default='white',
                                 help='文本水印颜色（默认: white）')

    # 图像处理选项
    process_group = parser.add_argument_group('图像处理选项')
    process_group.add_argument('--filter', choices=[f.value for f in FilterType],
                               help='应用滤镜效果')
    process_group.add_argument('--brightness', type=float,
                               help='调整亮度（0.0-2.0，1.0为原始亮度）')
    process_group.add_argument('--contrast', type=float,
                               help='调整对比度（0.0-2.0，1.0为原始对比度）')
    process_group.add_argument('--color', type=float,
                               help='调整色彩（0.0-2.0，1.0为原始色彩）')
    process_group.add_argument('--sharpness', type=float,
                               help='调整锐度（0.0-2.0，1.0为原始锐度）')
    process_group.add_argument('--rotate', type=float,
                               help='旋转角度（度，顺时针）')
    process_group.add_argument('--flip-horizontal', action='store_true',
                               help='水平翻转')
    process_group.add_argument('--flip-vertical', action='store_true',
                               help='垂直翻转')

    # EXIF选项
    exif_group = parser.add_argument_group('EXIF选项')
    exif_group.add_argument('--strip-exif', dest='keep_exif', action='store_false',
                            help='移除EXIF元数据')
    exif_group.add_argument('--exif-author', help='设置作者信息')
    exif_group.add_argument('--exif-copyright', help='设置版权信息')

    args = parser.parse_args()
    return args


def main():
    """主函数"""
    args = parse_arguments()

    try:
        # 确定输出模式
        if args.replace:
            output_mode = OutputMode.REPLACE
            output_dir = None
        elif args.output_dir:
            output_mode = OutputMode.CUSTOM_DIR
            output_dir = args.output_dir
        elif args.output_subfolder:
            output_mode = OutputMode.SUBFOLDER
            output_dir = args.output_subfolder
        else:
            output_mode = OutputMode.SAME_DIR
            output_dir = None

        # 确定调整大小模式和参数
        resize_mode = None
        resize_params = {}

        if args.resize_percent is not None:
            resize_mode = ResizeMode.PERCENT
            resize_params['percent'] = args.resize_percent
        elif args.resize_exact:
            resize_mode = ResizeMode.EXACT
            resize_params['width'] = args.resize_exact[0]
            resize_params['height'] = args.resize_exact[1]
        elif args.resize_fit:
            resize_mode = ResizeMode.FIT
            resize_params['width'] = args.resize_fit[0]
            resize_params['height'] = args.resize_fit[1]
        elif args.resize_fill:
            resize_mode = ResizeMode.FILL
            resize_params['width'] = args.resize_fill[0]
            resize_params['height'] = args.resize_fill[1]
        elif args.resize_width:
            resize_mode = ResizeMode.WIDTH
            resize_params['width'] = args.resize_width
        elif args.resize_height:
            resize_mode = ResizeMode.HEIGHT
            resize_params['height'] = args.resize_height

        # 添加字体设置到调整参数中
        if args.font_size:
            resize_params['font_size'] = args.font_size
        if args.font_path:
            resize_params['font_path'] = args.font_path
        if args.text_color:
            # 将颜色名称转换为RGBA
            text_color = args.text_color
            if text_color == 'white':
                resize_params['text_color'] = (255, 255, 255, 255)
            elif text_color == 'black':
                resize_params['text_color'] = (0, 0, 0, 255)
            elif text_color == 'red':
                resize_params['text_color'] = (255, 0, 0, 255)
            elif text_color == 'green':
                resize_params['text_color'] = (0, 255, 0, 255)
            elif text_color == 'blue':
                resize_params['text_color'] = (0, 0, 255, 255)
            elif text_color == 'yellow':
                resize_params['text_color'] = (255, 255, 0, 255)
            else:
                # 尝试解析十六进制颜色
                try:
                    if text_color.startswith('#'):
                        color = text_color[1:]
                        r = int(color[0:2], 16)
                        g = int(color[2:4], 16)
                        b = int(color[4:6], 16)
                        resize_params['text_color'] = (r, g, b, 255)
                except:
                    logger.warning(f"无法解析颜色值: {text_color}，使用白色")
                    resize_params['text_color'] = (255, 255, 255, 255)

        # 确定滤镜类型
        filter_type = None
        if args.filter:
            for f in FilterType:
                if f.value == args.filter:
                    filter_type = f
                    break

        # 确定水印位置
        watermark_position = WatermarkPosition.BOTTOM_RIGHT
        if args.watermark_position:
            for pos in WatermarkPosition:
                if pos.value == args.watermark_position:
                    watermark_position = pos
                    break

        # 构建EXIF数据
        exif_data = {}
        if args.exif_author:
            exif_data['Author'] = args.exif_author
        if args.exif_copyright:
            exif_data['Copyright'] = args.exif_copyright

        # 创建图像处理器
        processor = ImageProcessor(
            input_paths=args.input_paths,
            output_mode=output_mode,
            output_dir=output_dir or "processed_images",
            recursive=args.recursive,
            include_patterns=args.include,
            exclude_patterns=args.exclude,
            output_format=args.output_format,
            output_quality=args.quality,
            output_pattern=args.output_pattern,
            resize_mode=resize_mode,
            resize_params=resize_params,
            watermark_text=args.text_watermark,
            watermark_image=args.image_watermark,
            watermark_position=watermark_position,
            watermark_opacity=args.watermark_opacity,
            filter_type=filter_type,
            brightness=args.brightness,
            contrast=args.contrast,
            color=args.color,
            sharpness=args.sharpness,
            rotate_angle=args.rotate,
            flip_horizontal=args.flip_horizontal,
            flip_vertical=args.flip_vertical,
            keep_exif=args.keep_exif,
            exif_data=exif_data,
            threads=args.threads,
            dry_run=args.dry_run,
            verbose=args.verbose
        )

        # 处理图像
        success = processor.process_images()

        return 0 if success else 1

    except KeyboardInterrupt:
        logger.info("处理已被用户中断")
        return 1
    except Exception as e:
        logger.error(f"执行过程中出错: {e}")
        if args.verbose:
            import traceback
            traceback.print_exc()
        return 1


if __name__ == "__main__":
    sys.exit(main())
