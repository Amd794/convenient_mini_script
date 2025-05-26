#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
文件搜索工具

这个脚本提供了强大的文件搜索功能，支持按文件名、内容、大小、修改日期等条件
搜索文件，并可以对结果进行排序和格式化输出。
"""

import argparse
import datetime
import fnmatch
import logging
import os
import re
import stat
import sys
from typing import List, Dict, Tuple, Optional, Callable

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)
logger = logging.getLogger(__name__)

# 定义文件大小单位常量
SIZE_UNITS = {
    'B': 1,
    'KB': 1024,
    'MB': 1024 * 1024,
    'GB': 1024 * 1024 * 1024,
    'TB': 1024 * 1024 * 1024 * 1024
}


class FileInfo:
    """文件信息类，用于存储和处理文件的各种属性"""

    def __init__(self, path: str):
        """
        初始化文件信息
        
        Args:
            path: 文件路径
        """
        self.path = os.path.abspath(path)
        self.name = os.path.basename(path)
        self.directory = os.path.dirname(path)
        self.extension = os.path.splitext(path)[1].lower()

        # 获取文件状态信息
        stat_info = os.stat(path)

        self.size = stat_info.st_size
        self.created_time = stat_info.st_ctime
        self.modified_time = stat_info.st_mtime
        self.accessed_time = stat_info.st_atime

        # 文件权限和类型
        self.is_file = os.path.isfile(path)
        self.is_dir = os.path.isdir(path)
        self.is_link = os.path.islink(path)
        self.is_hidden = self.name.startswith('.') or bool(
            stat_info.st_file_attributes & stat.FILE_ATTRIBUTE_HIDDEN) if hasattr(stat_info,
                                                                                  'st_file_attributes') else False

        # 用于内容搜索的匹配行
        self.matching_lines = []

    def get_formatted_size(self) -> str:
        """
        获取格式化的文件大小
        
        Returns:
            格式化后的文件大小字符串（如: 1.23 MB）
        """
        if self.size == 0:
            return "0 B"

        for unit in ['B', 'KB', 'MB', 'GB', 'TB']:
            if self.size < 1024.0 or unit == 'TB':
                break
            self.size /= 1024.0

        return f"{self.size:.2f} {unit}"

    def get_formatted_time(self, timestamp: float) -> str:
        """
        获取格式化的时间字符串
        
        Args:
            timestamp: 时间戳
            
        Returns:
            格式化后的时间字符串（YYYY-MM-DD HH:MM:SS）
        """
        return datetime.datetime.fromtimestamp(timestamp).strftime('%Y-%m-%d %H:%M:%S')

    def __str__(self) -> str:
        """
        返回文件信息的字符串表示
        
        Returns:
            文件信息字符串
        """
        return self.path


class FileFinder:
    """文件搜索器，用于按各种条件搜索文件"""

    def __init__(self, search_path: str = '.', recursive: bool = True):
        """
        初始化文件搜索器
        
        Args:
            search_path: 搜索起始路径
            recursive: 是否递归搜索子目录
        """
        self.search_path = os.path.abspath(search_path)
        self.recursive = recursive
        self.results: List[FileInfo] = []
        self.content_matches: Dict[str, List[Tuple[int, str]]] = {}

    def reset(self) -> None:
        """重置搜索结果"""
        self.results = []
        self.content_matches = {}

    def find_by_name(self,
                     pattern: str,
                     case_sensitive: bool = False,
                     use_regex: bool = False) -> List[FileInfo]:
        """
        按文件名搜索文件
        
        Args:
            pattern: 文件名模式（通配符或正则表达式）
            case_sensitive: 是否区分大小写
            use_regex: 是否使用正则表达式而不是通配符
            
        Returns:
            匹配的文件信息列表
        """
        self.reset()

        # 准备模式匹配器
        if use_regex:
            flags = 0 if case_sensitive else re.IGNORECASE
            matcher = re.compile(pattern, flags)
            match_func = lambda name: bool(matcher.search(name))
        else:
            if not case_sensitive:
                pattern = pattern.lower()
                match_func = lambda name: fnmatch.fnmatch(name.lower(), pattern)
            else:
                match_func = lambda name: fnmatch.fnmatch(name, pattern)

        # 遍历文件系统
        for root, dirs, files in os.walk(self.search_path):
            # 如果不递归且不是起始目录，则跳过
            if not self.recursive and root != self.search_path:
                continue

            # 搜索文件
            for file in files:
                if match_func(file):
                    file_path = os.path.join(root, file)
                    try:
                        self.results.append(FileInfo(file_path))
                    except (PermissionError, FileNotFoundError) as e:
                        logger.warning(f"无法访问文件 {file_path}: {e}")

        return self.results

    def find_by_extension(self, extensions: List[str]) -> List[FileInfo]:
        """
        按文件扩展名搜索文件
        
        Args:
            extensions: 扩展名列表（如 ['.txt', '.py']）
            
        Returns:
            匹配的文件信息列表
        """
        self.reset()

        # 确保扩展名以点号开头
        normalized_extensions = [ext if ext.startswith('.') else f'.{ext}' for ext in extensions]
        normalized_extensions = [ext.lower() for ext in normalized_extensions]

        # 遍历文件系统
        for root, dirs, files in os.walk(self.search_path):
            # 如果不递归且不是起始目录，则跳过
            if not self.recursive and root != self.search_path:
                continue

            # 搜索文件
            for file in files:
                ext = os.path.splitext(file)[1].lower()
                if ext in normalized_extensions:
                    file_path = os.path.join(root, file)
                    try:
                        self.results.append(FileInfo(file_path))
                    except (PermissionError, FileNotFoundError) as e:
                        logger.warning(f"无法访问文件 {file_path}: {e}")

        return self.results

    def find_by_size(self,
                     min_size: Optional[str] = None,
                     max_size: Optional[str] = None) -> List[FileInfo]:
        """
        按文件大小搜索文件
        
        Args:
            min_size: 最小文件大小（如 "1MB"）
            max_size: 最大文件大小（如 "10MB"）
            
        Returns:
            匹配的文件信息列表
        """
        self.reset()

        # 解析大小参数
        min_bytes = self._parse_size(min_size) if min_size else None
        max_bytes = self._parse_size(max_size) if max_size else None

        # 遍历文件系统
        for root, dirs, files in os.walk(self.search_path):
            # 如果不递归且不是起始目录，则跳过
            if not self.recursive and root != self.search_path:
                continue

            # 搜索文件
            for file in files:
                file_path = os.path.join(root, file)
                try:
                    size = os.path.getsize(file_path)

                    # 检查大小条件
                    if (min_bytes is None or size >= min_bytes) and (max_bytes is None or size <= max_bytes):
                        self.results.append(FileInfo(file_path))
                except (PermissionError, FileNotFoundError, OSError) as e:
                    logger.warning(f"无法访问文件 {file_path}: {e}")

        return self.results

    def find_by_time(self,
                     min_date: Optional[str] = None,
                     max_date: Optional[str] = None,
                     time_type: str = 'modified') -> List[FileInfo]:
        """
        按文件时间搜索文件
        
        Args:
            min_date: 最早日期（YYYY-MM-DD 或 YYYY-MM-DD HH:MM:SS）
            max_date: 最晚日期（YYYY-MM-DD 或 YYYY-MM-DD HH:MM:SS）
            time_type: 时间类型，可选值: 'modified', 'created', 'accessed'
            
        Returns:
            匹配的文件信息列表
        """
        self.reset()

        # 解析日期参数
        min_timestamp = self._parse_date(min_date) if min_date else None
        max_timestamp = self._parse_date(max_date, end_of_day=True) if max_date else None

        # 确定时间属性
        if time_type == 'modified':
            time_attr = 'modified_time'
        elif time_type == 'created':
            time_attr = 'created_time'
        elif time_type == 'accessed':
            time_attr = 'accessed_time'
        else:
            raise ValueError(f"无效的时间类型: {time_type}")

        # 遍历文件系统
        for root, dirs, files in os.walk(self.search_path):
            # 如果不递归且不是起始目录，则跳过
            if not self.recursive and root != self.search_path:
                continue

            # 搜索文件
            for file in files:
                file_path = os.path.join(root, file)
                try:
                    file_info = FileInfo(file_path)
                    file_time = getattr(file_info, time_attr)

                    # 检查时间条件
                    if (min_timestamp is None or file_time >= min_timestamp) and (
                            max_timestamp is None or file_time <= max_timestamp):
                        self.results.append(file_info)
                except (PermissionError, FileNotFoundError) as e:
                    logger.warning(f"无法访问文件 {file_path}: {e}")

        return self.results

    def find_by_content(self,
                        pattern: str,
                        case_sensitive: bool = False,
                        use_regex: bool = False,
                        max_file_size: str = "10MB",
                        skip_binary: bool = True,
                        context_lines: int = 0) -> List[FileInfo]:
        """
        按文件内容搜索文件
        
        Args:
            pattern: 内容模式（文本或正则表达式）
            case_sensitive: 是否区分大小写
            use_regex: 是否使用正则表达式
            max_file_size: 搜索的最大文件大小
            skip_binary: 是否跳过二进制文件
            context_lines: 匹配行前后显示的上下文行数
            
        Returns:
            匹配的文件信息列表
        """
        self.reset()

        # 解析最大文件大小
        max_bytes = self._parse_size(max_file_size)

        # 准备模式匹配器
        if use_regex:
            flags = 0 if case_sensitive else re.IGNORECASE
            matcher = re.compile(pattern, flags)
            match_func = lambda line: bool(matcher.search(line))
        else:
            if not case_sensitive:
                pattern = pattern.lower()
                match_func = lambda line: pattern in line.lower()
            else:
                match_func = lambda line: pattern in line

        # 遍历文件系统
        for root, dirs, files in os.walk(self.search_path):
            # 如果不递归且不是起始目录，则跳过
            if not self.recursive and root != self.search_path:
                continue

            # 搜索文件
            for file in files:
                file_path = os.path.join(root, file)
                try:
                    # 检查文件大小
                    if os.path.getsize(file_path) > max_bytes:
                        continue

                    # 读取文件内容并搜索
                    if self._search_file_content(file_path, match_func, skip_binary, context_lines):
                        file_info = FileInfo(file_path)
                        file_info.matching_lines = self.content_matches[file_path]
                        self.results.append(file_info)
                except (PermissionError, FileNotFoundError, UnicodeDecodeError) as e:
                    logger.warning(f"无法搜索文件 {file_path}: {e}")

        return self.results

    def _search_file_content(self,
                             file_path: str,
                             match_func: Callable[[str], bool],
                             skip_binary: bool = True,
                             context_lines: int = 0) -> bool:
        """
        搜索文件内容
        
        Args:
            file_path: 文件路径
            match_func: 匹配函数
            skip_binary: 是否跳过二进制文件
            context_lines: 匹配行前后显示的上下文行数
            
        Returns:
            是否找到匹配
        """
        # 检查文件是否可能是二进制
        if skip_binary:
            try:
                with open(file_path, 'rb') as f:
                    chunk = f.read(1024)
                    if b'\0' in chunk:  # 简单检测二进制文件
                        return False
            except (PermissionError, FileNotFoundError):
                return False

        # 读取文件内容并搜索
        matching_lines = []
        line_buffer = []  # 用于存储上下文行

        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                for i, line in enumerate(f, 1):
                    line = line.rstrip('\r\n')

                    # 保存当前行到缓冲区（用于上下文）
                    line_buffer.append((i, line))
                    if len(line_buffer) > context_lines * 2 + 1:
                        line_buffer.pop(0)

                    if match_func(line):
                        # 如果找到匹配，添加上下文行
                        if context_lines > 0:
                            # 添加前面的上下文行
                            start_idx = max(0, len(line_buffer) - context_lines - 1)
                            for idx in range(start_idx, len(line_buffer) - 1):
                                matching_lines.append(line_buffer[idx])

                        # 添加匹配行
                        matching_lines.append((i, line))

                        # 读取后面的上下文行
                        if context_lines > 0:
                            context_count = 0
                            for j, next_line in enumerate(f, i + 1):
                                next_line = next_line.rstrip('\r\n')
                                matching_lines.append((j, next_line))
                                context_count += 1
                                if context_count >= context_lines:
                                    break
        except UnicodeDecodeError:
            # 如果解码失败，尝试以二进制方式处理
            if not skip_binary:
                try:
                    with open(file_path, 'rb') as f:
                        content = f.read()
                        if match_func(str(content)):
                            matching_lines.append((1, "Binary file matches"))
                except Exception:
                    return False

        if matching_lines:
            self.content_matches[file_path] = matching_lines
            return True

        return False

    def sort_results(self,
                     key: str = 'name',
                     reverse: bool = False) -> List[FileInfo]:
        """
        对搜索结果进行排序
        
        Args:
            key: 排序关键字，可选值: 'name', 'size', 'modified', 'created', 'extension', 'path'
            reverse: 是否倒序
            
        Returns:
            排序后的文件信息列表
        """
        if not self.results:
            return []

        # 定义排序键函数
        if key == 'name':
            key_func = lambda x: x.name
        elif key == 'size':
            key_func = lambda x: x.size
        elif key == 'modified':
            key_func = lambda x: x.modified_time
        elif key == 'created':
            key_func = lambda x: x.created_time
        elif key == 'extension':
            key_func = lambda x: x.extension
        elif key == 'path':
            key_func = lambda x: x.path
        else:
            raise ValueError(f"无效的排序关键字: {key}")

        # 排序结果
        self.results.sort(key=key_func, reverse=reverse)
        return self.results

    def filter_results(self,
                       include_hidden: bool = False,
                       only_files: bool = False,
                       only_dirs: bool = False) -> List[FileInfo]:
        """
        过滤搜索结果
        
        Args:
            include_hidden: 是否包含隐藏文件
            only_files: 是否只包含文件
            only_dirs: 是否只包含目录
            
        Returns:
            过滤后的文件信息列表
        """
        if not self.results:
            return []

        filtered_results = []

        for file_info in self.results:
            # 过滤隐藏文件
            if not include_hidden and file_info.is_hidden:
                continue

            # 过滤文件类型
            if only_files and not file_info.is_file:
                continue

            if only_dirs and not file_info.is_dir:
                continue

            filtered_results.append(file_info)

        self.results = filtered_results
        return self.results

    def limit_results(self, limit: int) -> List[FileInfo]:
        """
        限制结果数量
        
        Args:
            limit: 最大结果数
            
        Returns:
            限制后的文件信息列表
        """
        if limit > 0 and len(self.results) > limit:
            self.results = self.results[:limit]

        return self.results

    def _parse_size(self, size_str: str) -> int:
        """
        解析大小字符串为字节数
        
        Args:
            size_str: 大小字符串（如 "1MB"）
            
        Returns:
            字节数
        """
        if not size_str:
            return 0

        # 匹配数字和单位
        match = re.match(r'^([\d.]+)\s*([KMGT]?B)?$', size_str, re.IGNORECASE)
        if not match:
            raise ValueError(f"无效的大小格式: {size_str}")

        value = float(match.group(1))
        unit = match.group(2).upper() if match.group(2) else 'B'

        return int(value * SIZE_UNITS[unit])

    def _parse_date(self, date_str: str, end_of_day: bool = False) -> float:
        """
        解析日期字符串为时间戳
        
        Args:
            date_str: 日期字符串（YYYY-MM-DD 或 YYYY-MM-DD HH:MM:SS）
            end_of_day: 是否设置为一天的结束时间
            
        Returns:
            时间戳
        """
        if not date_str:
            return 0

        try:
            if ' ' in date_str:
                # 完整日期时间格式
                dt = datetime.datetime.strptime(date_str, '%Y-%m-%d %H:%M:%S')
            else:
                # 仅日期格式
                dt = datetime.datetime.strptime(date_str, '%Y-%m-%d')
                if end_of_day:
                    dt = dt.replace(hour=23, minute=59, second=59)

            return dt.timestamp()
        except ValueError:
            raise ValueError(f"无效的日期格式: {date_str}，应为 YYYY-MM-DD 或 YYYY-MM-DD HH:MM:SS")


def format_results(results: List[FileInfo],
                   format_type: str = 'list',
                   show_details: bool = False,
                   show_content_matches: bool = False,
                   output_file: Optional[str] = None) -> None:
    """
    格式化并输出搜索结果
    
    Args:
        results: 文件信息列表
        format_type: 输出格式类型，可选值: 'list', 'table', 'csv'
        show_details: 是否显示详细信息
        show_content_matches: 是否显示内容匹配行
        output_file: 输出文件路径
    """
    if not results:
        print("未找到匹配的文件")
        return

    # 准备输出内容
    output_lines = []

    if format_type == 'list':
        for i, file_info in enumerate(results, 1):
            if show_details:
                size_str = file_info.get_formatted_size()
                modified_str = file_info.get_formatted_time(file_info.modified_time)
                output_lines.append(f"{i}. {file_info.path}")
                output_lines.append(f"   大小: {size_str}, 修改时间: {modified_str}")
                output_lines.append(
                    f"   类型: {'目录' if file_info.is_dir else '文件'}, 扩展名: {file_info.extension or '无'}")

                if show_content_matches and hasattr(file_info, 'matching_lines') and file_info.matching_lines:
                    output_lines.append("   匹配行:")
                    for line_num, line in file_info.matching_lines[:5]:  # 限制显示的行数
                        output_lines.append(f"      {line_num}: {line}")

                    if len(file_info.matching_lines) > 5:
                        output_lines.append(f"      ... 还有 {len(file_info.matching_lines) - 5} 行匹配")

                output_lines.append("")
            else:
                output_lines.append(file_info.path)

    elif format_type == 'table':
        # 表头
        if show_details:
            output_lines.append(f"{'序号':<5} {'文件名':<30} {'大小':<10} {'修改时间':<20} {'类型':<8} {'路径'}")
            output_lines.append("-" * 80)

            for i, file_info in enumerate(results, 1):
                size_str = file_info.get_formatted_size()
                modified_str = file_info.get_formatted_time(file_info.modified_time)
                type_str = '目录' if file_info.is_dir else '文件'
                name = file_info.name[:30]  # 截断过长的文件名
                directory = file_info.directory

                output_lines.append(f"{i:<5} {name:<30} {size_str:<10} {modified_str:<20} {type_str:<8} {directory}")

                if show_content_matches and hasattr(file_info, 'matching_lines') and file_info.matching_lines:
                    for line_num, line in file_info.matching_lines[:3]:  # 限制显示的行数
                        output_lines.append(f"      {line_num}: {line[:70]}")

                    if len(file_info.matching_lines) > 3:
                        output_lines.append(f"      ... 还有 {len(file_info.matching_lines) - 3} 行匹配")
        else:
            output_lines.append(f"{'序号':<5} {'文件名':<40} {'路径'}")
            output_lines.append("-" * 80)

            for i, file_info in enumerate(results, 1):
                name = file_info.name[:40]  # 截断过长的文件名
                output_lines.append(f"{i:<5} {name:<40} {file_info.directory}")

    elif format_type == 'csv':
        if show_details:
            output_lines.append("路径,名称,大小,修改时间,创建时间,类型,扩展名")

            for file_info in results:
                size_str = file_info.get_formatted_size()
                modified_str = file_info.get_formatted_time(file_info.modified_time)
                created_str = file_info.get_formatted_time(file_info.created_time)
                type_str = '目录' if file_info.is_dir else '文件'

                # 转义CSV中的逗号
                path = f'"{file_info.path}"'
                name = f'"{file_info.name}"'

                output_lines.append(
                    f"{path},{name},{size_str},{modified_str},{created_str},{type_str},{file_info.extension}")
        else:
            output_lines.append("路径,名称")

            for file_info in results:
                # 转义CSV中的逗号
                path = f'"{file_info.path}"'
                name = f'"{file_info.name}"'

                output_lines.append(f"{path},{name}")

    else:
        print(f"不支持的输出格式: {format_type}")
        return

    # 添加摘要信息
    summary = f"\n找到 {len(results)} 个匹配项"
    output_lines.append(summary)

    # 输出结果
    output_text = "\n".join(output_lines)

    if output_file:
        try:
            with open(output_file, 'w', encoding='utf-8') as f:
                f.write(output_text)
            print(f"搜索结果已保存到: {output_file}")
        except Exception as e:
            logger.error(f"保存结果失败: {e}")
            print(output_text)  # 如果保存失败，输出到控制台
    else:
        print(output_text)


def parse_arguments():
    """解析命令行参数"""
    parser = argparse.ArgumentParser(description="文件搜索工具 - 按各种条件搜索文件")

    # 基本参数
    parser.add_argument("search_path", nargs="?", default=".",
                        help="搜索起始路径，默认为当前目录")
    parser.add_argument("-r", "--recursive", action="store_true", default=True,
                        help="递归搜索子目录（默认启用）")
    parser.add_argument("--no-recursive", action="store_false", dest="recursive",
                        help="不递归搜索子目录")

    # 搜索条件参数组
    search_group = parser.add_argument_group("搜索条件（至少指定一个）")

    # 按名称搜索
    search_group.add_argument("-n", "--name",
                              help="按文件名搜索，支持通配符（如 *.txt）")
    search_group.add_argument("--regex", action="store_true",
                              help="将名称或内容参数解释为正则表达式")
    search_group.add_argument("-i", "--ignore-case", action="store_true",
                              help="忽略大小写")

    # 按扩展名搜索
    search_group.add_argument("-e", "--extension", nargs="+",
                              help="按文件扩展名搜索（如 txt py）")

    # 按大小搜索
    search_group.add_argument("--min-size",
                              help="最小文件大小（如 1KB、2MB）")
    search_group.add_argument("--max-size",
                              help="最大文件大小（如 5MB、1GB）")

    # 按时间搜索
    search_group.add_argument("--min-date",
                              help="最早日期（YYYY-MM-DD 或 YYYY-MM-DD HH:MM:SS）")
    search_group.add_argument("--max-date",
                              help="最晚日期（YYYY-MM-DD 或 YYYY-MM-DD HH:MM:SS）")
    search_group.add_argument("--time-type", choices=["modified", "created", "accessed"], default="modified",
                              help="时间类型（默认: modified）")

    # 按内容搜索
    search_group.add_argument("-c", "--content",
                              help="按文件内容搜索")
    search_group.add_argument("--max-content-size", default="10MB",
                              help="内容搜索的最大文件大小（默认: 10MB）")
    search_group.add_argument("--include-binary", action="store_true",
                              help="包含二进制文件在内容搜索中")
    search_group.add_argument("--context-lines", type=int, default=0,
                              help="显示匹配行周围的上下文行数")

    # 过滤参数
    filter_group = parser.add_argument_group("结果过滤")
    filter_group.add_argument("--include-hidden", action="store_true",
                              help="包含隐藏文件")
    filter_group.add_argument("--only-files", action="store_true",
                              help="只包含文件，不包含目录")
    filter_group.add_argument("--only-dirs", action="store_true",
                              help="只包含目录，不包含文件")
    filter_group.add_argument("--limit", type=int, default=0,
                              help="限制结果数量（0表示不限制）")

    # 排序参数
    sort_group = parser.add_argument_group("结果排序")
    sort_group.add_argument("--sort-by", choices=["name", "size", "modified", "created", "extension", "path"],
                            default="name",
                            help="排序关键字（默认: name）")
    sort_group.add_argument("--reverse", action="store_true",
                            help="倒序排列")

    # 输出格式参数
    output_group = parser.add_argument_group("输出选项")
    output_group.add_argument("--format", choices=["list", "table", "csv"], default="list",
                              help="输出格式（默认: list）")
    output_group.add_argument("-d", "--details", action="store_true",
                              help="显示详细信息")
    output_group.add_argument("--show-matches", action="store_true",
                              help="显示内容匹配行")
    output_group.add_argument("-o", "--output",
                              help="将结果保存到文件")

    return parser.parse_args()


def main():
    """主函数"""
    args = parse_arguments()

    # 创建文件搜索器
    finder = FileFinder(args.search_path, args.recursive)

    # 执行搜索（至少需要一个搜索条件）
    if args.name:
        results = finder.find_by_name(args.name, not args.ignore_case, args.regex)
    elif args.extension:
        results = finder.find_by_extension(args.extension)
    elif args.min_size or args.max_size:
        results = finder.find_by_size(args.min_size, args.max_size)
    elif args.min_date or args.max_date:
        results = finder.find_by_time(args.min_date, args.max_date, args.time_type)
    elif args.content:
        results = finder.find_by_content(
            args.content,
            not args.ignore_case,
            args.regex,
            args.max_content_size,
            not args.include_binary,
            args.context_lines
        )
    else:
        print("错误: 需要至少指定一个搜索条件")
        return 1

    # 过滤结果
    finder.filter_results(args.include_hidden, args.only_files, args.only_dirs)

    # 排序结果
    finder.sort_results(args.sort_by, args.reverse)

    # 限制结果数量
    if args.limit > 0:
        finder.limit_results(args.limit)

    # 格式化并输出结果
    format_results(
        finder.results,
        args.format,
        args.details,
        args.show_matches,
        args.output
    )

    return 0


if __name__ == "__main__":
    try:
        sys.exit(main())
    except KeyboardInterrupt:
        print("\n搜索已被用户中断")
        sys.exit(1)
    except Exception as e:
        logger.error(f"搜索失败: {e}")
        print(f"错误: {e}")
        sys.exit(1)
