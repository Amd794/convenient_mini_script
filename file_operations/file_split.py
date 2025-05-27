#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
文件分割工具

这个脚本用于将大型文件分割成多个较小的文件，支持多种分割方式，
包括按行数、大小、内容分割等。适用于处理大型日志、数据集和二进制文件。
"""

import argparse
import datetime
import logging
import math
import os
import re
import sys
from enum import Enum
from typing import List, Optional, Union, Iterator, BinaryIO

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)
logger = logging.getLogger(__name__)


class SplitMode(Enum):
    """文件分割模式枚举"""
    LINES = "lines"  # 按行数分割
    SIZE = "size"  # 按大小分割
    NUMBER = "number"  # 按文件数量平均分割
    PATTERN = "pattern"  # 按正则表达式模式分割
    DELIMITER = "delimiter"  # 按分隔符分割
    BYTE_POSITION = "bytes"  # 按字节位置分割
    CONTENT = "content"  # 按文件内容特征分割


class FileType(Enum):
    """文件类型枚举"""
    TEXT = "text"  # 文本文件
    BINARY = "binary"  # 二进制文件
    AUTO = "auto"  # 自动检测


class FileSplitter:
    """文件分割器类，提供多种文件分割功能"""

    def __init__(
            self,
            source_file: str,
            output_pattern: str = "{basename}_{num:03d}{extension}",
            output_dir: Optional[str] = None,
            mode: SplitMode = SplitMode.SIZE,
            lines: int = 1000,
            size: Union[int, str] = "1MB",
            num_parts: int = 2,
            delimiter: Optional[str] = None,
            pattern: Optional[str] = None,
            file_type: FileType = FileType.AUTO,
            encoding: str = 'utf-8',
            include_header: bool = False,
            include_footer: bool = False,
            custom_header: Optional[str] = None,
            custom_footer: Optional[str] = None,
            byte_positions: Optional[List[int]] = None,
            preserve_headers: bool = False,
            header_lines: int = 1,
            compress_output: bool = False,
            verbose: bool = False
    ):
        """
        初始化文件分割器

        Args:
            source_file: 源文件路径
            output_pattern: 输出文件名模式，例如 "{basename}_{num:03d}{extension}"
            output_dir: 输出目录，如果为None，则使用源文件所在目录
            mode: 分割模式，如 lines, size, number
            lines: 每个文件的行数（使用LINES模式时）
            size: 每个文件的大小，可以是整数字节或字符串 (如 "1MB")
            num_parts: 分割成的文件数量（使用NUMBER模式时）
            delimiter: 分隔符字符串（使用DELIMITER模式时）
            pattern: 正则表达式模式（使用PATTERN模式时）
            file_type: 文件类型（文本或二进制）
            encoding: 文本文件编码
            include_header: 是否在每个分割文件中包含源文件的头部
            include_footer: 是否在每个分割文件中包含源文件的尾部
            custom_header: 自定义头部文本
            custom_footer: 自定义尾部文本
            byte_positions: 按字节位置分割
            preserve_headers: 是否在每个分割文件中保留表头(仅用于文本文件)
            header_lines: 表头的行数
            compress_output: 是否压缩输出文件
            verbose: 是否显示详细信息
        """
        self.source_file = source_file
        self.output_pattern = output_pattern

        # 设置输出目录
        if output_dir:
            self.output_dir = output_dir
            # 确保输出目录存在
            os.makedirs(output_dir, exist_ok=True)
        else:
            self.output_dir = os.path.dirname(os.path.abspath(source_file)) or '.'

        self.mode = mode
        self.lines = lines
        self.num_parts = num_parts
        self.delimiter = delimiter
        self.pattern = pattern
        self.file_type = file_type
        self.encoding = encoding
        self.include_header = include_header
        self.include_footer = include_footer
        self.custom_header = custom_header
        self.custom_footer = custom_footer
        self.byte_positions = byte_positions or []
        self.preserve_headers = preserve_headers
        self.header_lines = header_lines
        self.compress_output = compress_output
        self.verbose = verbose

        # 解析大小字符串
        if isinstance(size, str):
            self.size = self._parse_size(size)
        else:
            self.size = size

        self._compiled_pattern = None
        if self.pattern:
            try:
                self._compiled_pattern = re.compile(self.pattern)
            except re.error as e:
                logger.error(f"正则表达式编译错误: {e}")
                raise ValueError(f"无效的正则表达式模式: {self.pattern}")

        # 设置压缩扩展名
        self.compress_ext = '.gz' if self.compress_output else ''

        # 确保源文件存在
        if not os.path.exists(self.source_file):
            raise FileNotFoundError(f"找不到源文件: {self.source_file}")

        # 检测文件类型
        if self.file_type == FileType.AUTO:
            self.file_type = self._detect_file_type()

        # 得到源文件基本信息
        self.source_size = os.path.getsize(self.source_file)
        self.source_basename = os.path.basename(self.source_file)
        self.source_name, self.source_ext = os.path.splitext(self.source_basename)

    def _detect_file_type(self) -> FileType:
        """
        自动检测文件类型
        
        Returns:
            检测到的文件类型（文本或二进制）
        """
        try:
            # 尝试以文本模式读取文件前几千个字节
            with open(self.source_file, 'r', encoding=self.encoding) as f:
                f.read(4096)
            return FileType.TEXT
        except UnicodeDecodeError:
            return FileType.BINARY

    def _parse_size(self, size_str: str) -> int:
        """
        解析大小字符串（如 '1KB', '5MB'）
        
        Args:
            size_str: 大小字符串
            
        Returns:
            字节数
        """
        size_str = size_str.strip().upper()
        units = {
            'B': 1,
            'KB': 1024,
            'MB': 1024 * 1024,
            'GB': 1024 * 1024 * 1024,
            'TB': 1024 * 1024 * 1024 * 1024
        }

        pattern = r'^(\d+\.?\d*)([KMGT]?B)$'
        match = re.match(pattern, size_str)

        if not match:
            try:
                return int(size_str)  # 尝试直接解析为整数字节
            except ValueError:
                raise ValueError(f"无法解析大小字符串: {size_str}")

        value, unit = match.groups()
        value = float(value)
        multiplier = units.get(unit, 1)

        return int(value * multiplier)

    def _get_output_filename(self, part_num: int) -> str:
        """
        根据输出模式生成分割后的文件名
        
        Args:
            part_num: 文件部分编号
            
        Returns:
            生成的文件名
        """
        filename = self.output_pattern.format(
            basename=self.source_name,
            num=part_num,
            extension=self.source_ext,
            date=datetime.datetime.now().strftime('%Y%m%d'),
            time=datetime.datetime.now().strftime('%H%M%S')
        )

        if self.compress_output and not filename.endswith(('.gz', '.zip', '.bz2')):
            filename += '.gz'

        return os.path.join(self.output_dir, filename)

    def _open_output_file(self, filename: str, mode: str = 'w') -> Union[BinaryIO, Iterator]:
        """
        打开输出文件，根据情况使用压缩
        
        Args:
            filename: 文件名
            mode: 打开模式 ('w' 或 'wb')
            
        Returns:
            文件对象
        """
        if self.compress_output:
            import gzip
            if 'b' in mode:
                return gzip.open(filename, mode)
            else:
                return gzip.open(filename, mode + 't', encoding=self.encoding)
        else:
            if 'b' in mode:
                return open(filename, mode)
            else:
                return open(filename, mode, encoding=self.encoding)

    def _get_header(self, is_first_file: bool = False) -> Optional[str]:
        """
        获取要添加到分割文件的头部内容
        
        Args:
            is_first_file: 是否为第一个分割文件
            
        Returns:
            头部内容，如果不需要则为None
        """
        if self.custom_header is not None:
            return self.custom_header

        if self.include_header and is_first_file:
            if self.file_type == FileType.TEXT:
                with open(self.source_file, 'r', encoding=self.encoding) as f:
                    return ''.join(f.readline() for _ in range(self.header_lines))
            else:
                # 二进制文件不支持此选项
                return None

        return None

    def _get_footer(self, is_last_file: bool = False) -> Optional[str]:
        """
        获取要添加到分割文件的尾部内容
        
        Args:
            is_last_file: 是否为最后一个分割文件
            
        Returns:
            尾部内容，如果不需要则为None
        """
        if self.custom_footer is not None:
            return self.custom_footer

        if self.include_footer and is_last_file:
            # 这部分实现会更复杂，涉及到读取文件末尾内容
            # 简化起见，仅支持自定义尾部
            pass

        return None

    def _get_headers_from_source(self) -> List[str]:
        """
        从源文件读取表头行
        
        Returns:
            表头行列表
        """
        if self.file_type != FileType.TEXT or not self.preserve_headers:
            return []

        with open(self.source_file, 'r', encoding=self.encoding) as f:
            return [f.readline() for _ in range(self.header_lines)]

    def split_by_lines(self) -> List[str]:
        """
        按行数分割文件
        
        Returns:
            生成的文件列表
        """
        if self.file_type != FileType.TEXT:
            logger.error("按行分割仅支持文本文件")
            return []

        output_files = []
        headers = self._get_headers_from_source()

        try:
            with open(self.source_file, 'r', encoding=self.encoding) as infile:
                # 如果需要保留表头但又要跳过它们的话，需要预先读取
                if self.preserve_headers and headers:
                    # 已经在_get_headers_from_source中读取了表头，所以这里跳过相应的行
                    for _ in range(self.header_lines):
                        next(infile, '')

                file_number = 1
                while True:
                    output_file = self._get_output_filename(file_number)
                    with self._open_output_file(output_file) as outfile:
                        # 写入头部
                        if self.preserve_headers and headers:
                            for header in headers:
                                outfile.write(header)

                        header = self._get_header(file_number == 1)
                        if header:
                            outfile.write(header)

                        # 写入指定行数
                        lines_written = 0
                        for line in infile:
                            outfile.write(line)
                            lines_written += 1
                            if lines_written >= self.lines:
                                break

                        # 写入尾部
                        footer = self._get_footer()
                        if footer:
                            outfile.write(footer)

                    if lines_written == 0:  # 没有更多行可读
                        os.remove(output_file)  # 删除空文件
                        break

                    output_files.append(output_file)
                    file_number += 1

                    if self.verbose:
                        logger.info(f"已创建文件: {output_file} (包含 {lines_written} 行)")

            if self.verbose:
                logger.info(f"文件分割完成。创建了 {len(output_files)} 个文件")

            return output_files

        except Exception as e:
            logger.error(f"按行分割文件时出错: {e}")
            raise

    def split_by_size(self) -> List[str]:
        """
        按大小分割文件
        
        Returns:
            生成的文件列表
        """
        output_files = []

        try:
            mode = 'rb' if self.file_type == FileType.BINARY else 'r'
            output_mode = 'wb' if self.file_type == FileType.BINARY else 'w'
            encoding_args = {} if self.file_type == FileType.BINARY else {'encoding': self.encoding}

            with open(self.source_file, mode, **encoding_args) as infile:
                file_number = 1
                headers = self._get_headers_from_source() if self.file_type == FileType.TEXT else None

                # 如果保留表头且是文本文件，跳过相应行
                if self.file_type == FileType.TEXT and self.preserve_headers and headers:
                    for _ in range(self.header_lines):
                        next(infile, '')

                while True:
                    output_file = self._get_output_filename(file_number)
                    with self._open_output_file(output_file, output_mode) as outfile:
                        # 写入头部（仅文本文件）
                        if self.file_type == FileType.TEXT:
                            if self.preserve_headers and headers:
                                for header in headers:
                                    outfile.write(header)

                            header = self._get_header(file_number == 1)
                            if header:
                                outfile.write(header)

                        # 写入指定大小的数据
                        bytes_written = 0
                        chunk_size = min(8192, self.size)  # 读取块大小，最大8KB

                        while bytes_written < self.size:
                            chunk = infile.read(min(chunk_size, self.size - bytes_written))
                            if not chunk:  # 文件结束
                                break
                            outfile.write(chunk)
                            bytes_written += len(chunk) if self.file_type == FileType.BINARY else len(
                                chunk.encode(self.encoding))

                        # 写入尾部（仅文本文件）
                        if self.file_type == FileType.TEXT:
                            footer = self._get_footer(bytes_written < self.size)  # 如果没写满，说明到了文件末尾
                            if footer:
                                outfile.write(footer)

                    if bytes_written == 0:  # 没有写入任何内容
                        os.remove(output_file)  # 删除空文件
                        break

                    output_files.append(output_file)
                    file_number += 1

                    if self.verbose:
                        size_str = f"{bytes_written} 字节"
                        if bytes_written >= 1024:
                            size_str += f" ({bytes_written / 1024:.1f} KB)"
                        if bytes_written >= 1024 * 1024:
                            size_str += f" ({bytes_written / (1024 * 1024):.2f} MB)"
                        logger.info(f"已创建文件: {output_file} (大小: {size_str})")

            if self.verbose:
                logger.info(f"文件分割完成。创建了 {len(output_files)} 个文件")

            return output_files

        except Exception as e:
            logger.error(f"按大小分割文件时出错: {e}")
            raise

    def split_by_number(self) -> List[str]:
        """
        按指定数量平均分割文件
        
        Returns:
            生成的文件列表
        """
        if self.file_type == FileType.TEXT:
            # 对于文本文件，我们需要先计算总行数，然后平均分配
            try:
                with open(self.source_file, 'r', encoding=self.encoding) as f:
                    total_lines = sum(1 for _ in f)

                lines_per_file = max(1, math.ceil(total_lines / self.num_parts))

                # 使用按行分割的逻辑，但更改行数
                original_lines = self.lines
                self.lines = lines_per_file
                result = self.split_by_lines()
                self.lines = original_lines  # 恢复原始设置

                return result

            except Exception as e:
                logger.error(f"按数量分割文本文件时出错: {e}")
                raise

        else:
            # 对于二进制文件，我们基于文件大小平均分割
            try:
                size_per_file = max(1, math.ceil(self.source_size / self.num_parts))

                # 使用按大小分割的逻辑，但更改大小
                original_size = self.size
                self.size = size_per_file
                result = self.split_by_size()
                self.size = original_size  # 恢复原始设置

                return result

            except Exception as e:
                logger.error(f"按数量分割二进制文件时出错: {e}")
                raise

    def split_by_pattern(self) -> List[str]:
        """
        按正则表达式模式分割文件
        
        Returns:
            生成的文件列表
        """
        if self.file_type != FileType.TEXT or not self._compiled_pattern:
            logger.error("按模式分割仅支持文本文件且需要有效的正则表达式")
            return []

        output_files = []
        headers = self._get_headers_from_source()

        try:
            with open(self.source_file, 'r', encoding=self.encoding) as infile:
                content = infile.read()

                # 找出所有匹配位置
                matches = [m.start() for m in re.finditer(self._compiled_pattern, content)]

                if not matches:
                    logger.warning("未找到匹配的分割模式")
                    return []

                # 添加起始位置
                positions = [0] + matches

                # 如果最后一个匹配不是在文件末尾，添加文件长度
                if matches[-1] < len(content) - 1:
                    positions.append(len(content))

                # 按匹配位置分割
                for i in range(len(positions) - 1):
                    start_pos = positions[i]
                    end_pos = positions[i + 1]
                    part_content = content[start_pos:end_pos]

                    output_file = self._get_output_filename(i + 1)
                    with self._open_output_file(output_file) as outfile:
                        # 写入头部
                        if self.preserve_headers and headers and i > 0:  # 第一个片段中已经包含表头
                            for header in headers:
                                outfile.write(header)

                        header = self._get_header(i == 0)
                        if header:
                            outfile.write(header)

                        # 写入内容
                        outfile.write(part_content)

                        # 写入尾部
                        footer = self._get_footer(i == len(positions) - 2)
                        if footer:
                            outfile.write(footer)

                    output_files.append(output_file)

                    if self.verbose:
                        logger.info(f"已创建文件: {output_file} (大小: {len(part_content)} 字符)")

                if self.verbose:
                    logger.info(f"文件分割完成。创建了 {len(output_files)} 个文件")

                return output_files

        except Exception as e:
            logger.error(f"按模式分割文件时出错: {e}")
            raise

    def split_by_delimiter(self) -> List[str]:
        """
        按分隔符分割文件
        
        Returns:
            生成的文件列表
        """
        if self.file_type != FileType.TEXT or not self.delimiter:
            logger.error("按分隔符分割仅支持文本文件且需要有效的分隔符")
            return []

        output_files = []
        headers = self._get_headers_from_source()

        try:
            with open(self.source_file, 'r', encoding=self.encoding) as infile:
                content = infile.read()

                # 使用分隔符拆分内容
                parts = content.split(self.delimiter)

                for i, part in enumerate(parts):
                    if not part and i > 0:  # 跳过空部分（分割符相邻的情况），但保留第一部分
                        continue

                    output_file = self._get_output_filename(i + 1)
                    with self._open_output_file(output_file) as outfile:
                        # 写入头部
                        if self.preserve_headers and headers and i > 0:  # 第一个片段中已经包含表头
                            for header in headers:
                                outfile.write(header)

                        header = self._get_header(i == 0)
                        if header:
                            outfile.write(header)

                        # 写入内容
                        outfile.write(part)

                        # 如果不是最后一部分，添加分隔符
                        if i < len(parts) - 1:
                            outfile.write(self.delimiter)

                        # 写入尾部
                        footer = self._get_footer(i == len(parts) - 1)
                        if footer:
                            outfile.write(footer)

                    output_files.append(output_file)

                    if self.verbose:
                        logger.info(f"已创建文件: {output_file} (大小: {len(part)} 字符)")

                if self.verbose:
                    logger.info(f"文件分割完成。创建了 {len(output_files)} 个文件")

                return output_files

        except Exception as e:
            logger.error(f"按分隔符分割文件时出错: {e}")
            raise

    def split_by_byte_positions(self) -> List[str]:
        """
        按指定字节位置分割文件
        
        Returns:
            生成的文件列表
        """
        if not self.byte_positions:
            logger.error("未指定字节位置")
            return []

        output_files = []

        try:
            # 确保字节位置排序并且包含文件开头（0）
            positions = sorted(set([0] + self.byte_positions))

            # 如果最后一个位置不是文件末尾，添加文件大小
            if positions[-1] < self.source_size:
                positions.append(self.source_size)

            with open(self.source_file, 'rb') as infile:
                for i in range(len(positions) - 1):
                    start_pos = positions[i]
                    end_pos = positions[i + 1]

                    output_file = self._get_output_filename(i + 1)
                    with self._open_output_file(output_file, 'wb') as outfile:
                        # 定位到起始位置
                        infile.seek(start_pos)

                        # 读取并写入指定范围的数据
                        outfile.write(infile.read(end_pos - start_pos))

                    output_files.append(output_file)

                    if self.verbose:
                        size = end_pos - start_pos
                        size_str = f"{size} 字节"
                        if size >= 1024:
                            size_str += f" ({size / 1024:.1f} KB)"
                        if size >= 1024 * 1024:
                            size_str += f" ({size / (1024 * 1024):.2f} MB)"
                        logger.info(f"已创建文件: {output_file} (大小: {size_str})")

            if self.verbose:
                logger.info(f"文件分割完成。创建了 {len(output_files)} 个文件")

            return output_files

        except Exception as e:
            logger.error(f"按字节位置分割文件时出错: {e}")
            raise

    def split_file(self) -> List[str]:
        """
        根据指定模式分割文件
        
        Returns:
            生成的文件列表
        """
        if self.verbose:
            logger.info(f"开始分割文件: {self.source_file}")
            logger.info(f"分割模式: {self.mode.value}")
            logger.info(f"文件类型: {self.file_type.value}")
            logger.info(f"输出目录: {self.output_dir}")

        try:
            if self.mode == SplitMode.LINES:
                return self.split_by_lines()
            elif self.mode == SplitMode.SIZE:
                return self.split_by_size()
            elif self.mode == SplitMode.NUMBER:
                return self.split_by_number()
            elif self.mode == SplitMode.PATTERN:
                return self.split_by_pattern()
            elif self.mode == SplitMode.DELIMITER:
                return self.split_by_delimiter()
            elif self.mode == SplitMode.BYTE_POSITION:
                return self.split_by_byte_positions()
            else:
                logger.error(f"不支持的分割模式: {self.mode}")
                return []
        except Exception as e:
            logger.error(f"分割文件时出错: {e}")
            raise


def parse_arguments():
    """解析命令行参数"""
    parser = argparse.ArgumentParser(description="文件分割工具")

    # 基本参数
    parser.add_argument('file', help='要分割的文件路径')
    parser.add_argument('-o', '--output-dir', help='输出目录路径（默认为源文件所在目录）')
    parser.add_argument('-p', '--output-pattern', default="{basename}_{num:03d}{extension}",
                        help='输出文件名模式（可用变量：{basename}, {num}, {extension}, {date}, {time}）')

    # 分割模式
    mode_group = parser.add_argument_group('分割模式（选择一种）')
    mode_mutually_exclusive = mode_group.add_mutually_exclusive_group()
    mode_mutually_exclusive.add_argument('-l', '--lines', type=int,
                                         help='按行数分割（每个文件的行数）')
    mode_mutually_exclusive.add_argument('-s', '--size',
                                         help='按大小分割（每个文件的大小，如 1MB）')
    mode_mutually_exclusive.add_argument('-n', '--number', type=int,
                                         help='按数量平均分割（分割成的文件数量）')
    mode_mutually_exclusive.add_argument('-d', '--delimiter',
                                         help='按分隔符分割（如 "---分隔符---"）')
    mode_mutually_exclusive.add_argument('-r', '--regex-pattern',
                                         help='按正则表达式模式分割（在匹配位置拆分）')
    mode_mutually_exclusive.add_argument('-b', '--byte-positions', type=str,
                                         help='按字节位置分割（逗号分隔的位置列表）')

    # 文件类型选项
    type_group = parser.add_argument_group('文件类型选项')
    type_group.add_argument('-t', '--type', choices=['auto', 'text', 'binary'], default='auto',
                            help='指定文件类型（默认: auto）')
    type_group.add_argument('-e', '--encoding', default='utf-8',
                            help='文本文件编码（默认: utf-8）')

    # 输出选项
    output_group = parser.add_argument_group('输出选项')
    output_group.add_argument('--include-header', action='store_true',
                              help='在分割文件中包含源文件头部')
    output_group.add_argument('--include-footer', action='store_true',
                              help='在分割文件中包含源文件尾部')
    output_group.add_argument('--custom-header',
                              help='自定义内容添加到每个分割文件的开头')
    output_group.add_argument('--custom-footer',
                              help='自定义内容添加到每个分割文件的结尾')
    output_group.add_argument('--preserve-headers', action='store_true',
                              help='在每个分割文件中保留表头（仅对文本文件有效）')
    output_group.add_argument('--header-lines', type=int, default=1,
                              help='表头的行数（默认: 1）')
    output_group.add_argument('-c', '--compress', action='store_true',
                              help='压缩输出文件（使用gzip）')

    # 其他选项
    other_group = parser.add_argument_group('其他选项')
    other_group.add_argument('-v', '--verbose', action='store_true',
                             help='显示详细信息')

    args = parser.parse_args()

    # 检查是否指定了分割模式
    if not (args.lines or args.size or args.number or args.delimiter or
            args.regex_pattern or args.byte_positions):
        # 默认使用按大小分割，1MB
        args.size = "1MB"
        if args.verbose:
            logger.info("未指定分割模式，默认使用按大小分割（1MB）")

    return args


def main():
    """主函数"""
    args = parse_arguments()

    try:
        # 设置分割模式和相关参数
        mode = SplitMode.SIZE  # 默认
        mode_params = {}

        if args.lines:
            mode = SplitMode.LINES
            mode_params['lines'] = args.lines
        elif args.size:
            mode = SplitMode.SIZE
            mode_params['size'] = args.size
        elif args.number:
            mode = SplitMode.NUMBER
            mode_params['num_parts'] = args.number
        elif args.delimiter:
            mode = SplitMode.DELIMITER
            mode_params['delimiter'] = args.delimiter
        elif args.regex_pattern:
            mode = SplitMode.PATTERN
            mode_params['pattern'] = args.regex_pattern
        elif args.byte_positions:
            mode = SplitMode.BYTE_POSITION
            try:
                positions = [int(pos.strip()) for pos in args.byte_positions.split(',')]
                mode_params['byte_positions'] = positions
            except ValueError:
                logger.error("无效的字节位置列表。应为逗号分隔的整数列表")
                return 1

        # 设置文件类型
        file_type = FileType.AUTO
        if args.type == 'text':
            file_type = FileType.TEXT
        elif args.type == 'binary':
            file_type = FileType.BINARY

        # 创建分割器
        splitter = FileSplitter(
            source_file=args.file,
            output_pattern=args.output_pattern,
            output_dir=args.output_dir,
            mode=mode,
            file_type=file_type,
            encoding=args.encoding,
            include_header=args.include_header,
            include_footer=args.include_footer,
            custom_header=args.custom_header,
            custom_footer=args.custom_footer,
            preserve_headers=args.preserve_headers,
            header_lines=args.header_lines,
            compress_output=args.compress,
            verbose=args.verbose,
            **mode_params
        )

        # 执行分割
        output_files = splitter.split_file()

        # 输出结果
        if output_files:
            print(f"\n成功将文件 '{args.file}' 分割为 {len(output_files)} 个文件:")
            for file_path in output_files:
                print(f"- {os.path.basename(file_path)}")

            return 0
        else:
            print("文件分割失败，未生成任何输出文件")
            return 1

    except Exception as e:
        logger.error(f"执行文件分割时出错: {e}")
        if args.verbose:
            import traceback
            traceback.print_exc()
        return 1


if __name__ == "__main__":
    sys.exit(main())
