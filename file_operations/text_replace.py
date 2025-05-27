#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
文本批量查找替换工具

这个脚本用于在多个文件中批量查找和替换文本内容，支持普通文本和
正则表达式匹配，可以递归处理整个目录结构，并提供详细的替换报告。
适用于代码重构、文档更新、内容规范化等场景。
"""

import argparse
import difflib
import fnmatch
import logging
import os
import re
import shutil
import sys
from datetime import datetime
from enum import Enum
from typing import List, Dict, Optional, Pattern

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)
logger = logging.getLogger(__name__)


class ReplaceMode(Enum):
    """替换模式枚举"""
    TEXT = "text"  # 普通文本替换
    REGEX = "regex"  # 正则表达式替换
    WHOLE_WORD = "word"  # 全词匹配替换
    LINE = "line"  # 整行替换


class FileChange:
    """表示单个文件的变更"""

    def __init__(self, file_path: str):
        self.file_path = file_path
        self.original_content = ""
        self.modified_content = ""
        self.matches_count = 0
        self.lines_changed = set()
        self.is_binary = False
        self.error = None
        self.diff = ""

    def generate_diff(self) -> str:
        """生成差异比较"""
        if self.is_binary or self.error:
            return ""

        if self.original_content == self.modified_content:
            return ""

        original_lines = self.original_content.splitlines(True)
        modified_lines = self.modified_content.splitlines(True)

        diff = difflib.unified_diff(
            original_lines,
            modified_lines,
            fromfile=f"a/{os.path.basename(self.file_path)}",
            tofile=f"b/{os.path.basename(self.file_path)}",
            n=3
        )

        return "".join(diff)


class TextReplacer:
    """文本查找替换器类"""

    def __init__(
            self,
            search_pattern: str,
            replacement: str,
            paths: List[str],
            mode: ReplaceMode = ReplaceMode.TEXT,
            recursive: bool = True,
            include_patterns: Optional[List[str]] = None,
            exclude_patterns: Optional[List[str]] = None,
            exclude_dirs: Optional[List[str]] = None,
            max_size: Optional[int] = None,
            ignore_case: bool = False,
            backup: bool = False,
            backup_extension: str = '.bak',
            encoding: str = 'utf-8',
            ignore_errors: bool = False,
            match_limit: int = 0,
            skip_binary: bool = True,
            dry_run: bool = False,
            show_diff: bool = False,
            parallel: bool = False,
            verbose: bool = False
    ):
        """
        初始化文本替换器
        
        Args:
            search_pattern: 要查找的文本或正则表达式模式
            replacement: 替换内容（可以包含正则表达式引用，如 \1, \2 等）
            paths: 要处理的文件或目录路径列表
            mode: 替换模式，支持普通文本、正则表达式、全词匹配和整行替换
            recursive: 是否递归处理子目录
            include_patterns: 要包含的文件模式列表（如 *.txt, *.py）
            exclude_patterns: 要排除的文件模式列表
            exclude_dirs: 要排除的目录名列表
            max_size: 处理的最大文件大小（字节）
            ignore_case: 是否忽略大小写
            backup: 是否备份原始文件
            backup_extension: 备份文件扩展名
            encoding: 文件编码
            ignore_errors: 是否忽略错误并继续处理
            match_limit: 每个文件最多替换的匹配次数（0表示不限制）
            skip_binary: 是否跳过二进制文件
            dry_run: 是否仅模拟运行而不实际修改文件
            show_diff: 是否显示详细的替换差异
            parallel: 是否使用并行处理（多核处理）
            verbose: 是否显示详细信息
        """
        self.search_pattern = search_pattern
        self.replacement = replacement
        self.paths = paths
        self.mode = mode
        self.recursive = recursive
        self.include_patterns = include_patterns or ["*"]
        self.exclude_patterns = exclude_patterns or []
        self.exclude_dirs = exclude_dirs or [".git", ".svn", "__pycache__", "node_modules"]
        self.max_size = max_size
        self.ignore_case = ignore_case
        self.backup = backup
        self.backup_extension = backup_extension
        self.encoding = encoding
        self.ignore_errors = ignore_errors
        self.match_limit = match_limit
        self.skip_binary = skip_binary
        self.dry_run = dry_run
        self.show_diff = show_diff
        self.parallel = parallel
        self.verbose = verbose

        # 存储处理结果
        self.results: Dict[str, FileChange] = {}
        self.total_files_processed = 0
        self.total_files_modified = 0
        self.total_matches = 0
        self.errors = []

        # 编译正则表达式
        self.regex = self._compile_regex()

    def _compile_regex(self) -> Optional[Pattern]:
        """编译查找模式为正则表达式"""
        try:
            if self.mode == ReplaceMode.TEXT:
                # 普通文本模式需要转义特殊字符
                pattern = re.escape(self.search_pattern)
            elif self.mode == ReplaceMode.WHOLE_WORD:
                # 全词匹配模式
                pattern = r'\b' + re.escape(self.search_pattern) + r'\b'
            elif self.mode == ReplaceMode.LINE:
                # 整行匹配模式
                pattern = f'^.*{re.escape(self.search_pattern)}.*$'
            else:
                # 已经是正则表达式模式
                pattern = self.search_pattern

            flags = 0
            if self.ignore_case:
                flags |= re.IGNORECASE

            return re.compile(pattern, flags)
        except re.error as e:
            logger.error(f"正则表达式编译错误: {e}")
            raise ValueError(f"无效的正则表达式模式: {self.search_pattern}")

    def _is_binary_file(self, file_path: str) -> bool:
        """
        检查文件是否为二进制文件
        
        Args:
            file_path: 文件路径
            
        Returns:
            是否为二进制文件
        """
        try:
            with open(file_path, 'r', encoding=self.encoding) as f:
                f.read(4096)
            return False
        except UnicodeDecodeError:
            return True

    def _should_process_file(self, file_path: str) -> bool:
        """
        检查是否应处理该文件
        
        Args:
            file_path: 文件路径
            
        Returns:
            是否应处理该文件
        """
        # 检查文件大小
        if self.max_size and os.path.getsize(file_path) > self.max_size:
            if self.verbose:
                logger.info(f"跳过过大的文件 {file_path}")
            return False

        # 检查是否为二进制文件
        if self.skip_binary and self._is_binary_file(file_path):
            if self.verbose:
                logger.info(f"跳过二进制文件 {file_path}")
            return False

        # 检查文件名匹配
        filename = os.path.basename(file_path)

        # 检查是否符合包含模式
        included = any(fnmatch.fnmatch(filename, pattern) for pattern in self.include_patterns)
        if not included:
            if self.verbose:
                logger.info(f"跳过不匹配包含模式的文件 {file_path}")
            return False

        # 检查是否符合排除模式
        excluded = any(fnmatch.fnmatch(filename, pattern) for pattern in self.exclude_patterns)
        if excluded:
            if self.verbose:
                logger.info(f"跳过匹配排除模式的文件 {file_path}")
            return False

        return True

    def _should_process_dir(self, dir_path: str) -> bool:
        """
        检查是否应处理该目录
        
        Args:
            dir_path: 目录路径
            
        Returns:
            是否应处理该目录
        """
        dir_name = os.path.basename(dir_path)
        return dir_name not in self.exclude_dirs

    def _replace_in_file(self, file_path: str) -> FileChange:
        """
        在单个文件中进行替换
        
        Args:
            file_path: 文件路径
            
        Returns:
            文件变更对象
        """
        file_change = FileChange(file_path)

        try:
            # 检查文件是否应该被处理
            if not self._should_process_file(file_path):
                return file_change

            # 读取文件内容
            with open(file_path, 'r', encoding=self.encoding) as f:
                content = f.read()

            file_change.original_content = content

            # 执行替换
            if self.match_limit > 0:
                modified_content, count = self.regex.subn(self.replacement, content, self.match_limit)
            else:
                modified_content, count = self.regex.subn(self.replacement, content)

            file_change.modified_content = modified_content
            file_change.matches_count = count

            # 如果有修改，记录变更的行号
            if count > 0 and content != modified_content:
                for i, (old_line, new_line) in enumerate(zip(
                        content.splitlines(),
                        modified_content.splitlines()
                )):
                    if old_line != new_line:
                        file_change.lines_changed.add(i + 1)

                # 生成差异比较
                if self.show_diff:
                    file_change.diff = file_change.generate_diff()

                # 如果不是干运行模式，保存修改
                if not self.dry_run:
                    # 备份原文件
                    if self.backup:
                        backup_path = file_path + self.backup_extension
                        shutil.copy2(file_path, backup_path)
                        if self.verbose:
                            logger.info(f"已创建备份：{backup_path}")

                    # 写入修改后的内容
                    with open(file_path, 'w', encoding=self.encoding) as f:
                        f.write(modified_content)

                    if self.verbose:
                        logger.info(f"已更新文件：{file_path} (替换了 {count} 处匹配)")

        except Exception as e:
            file_change.error = str(e)
            if not self.ignore_errors:
                raise
            if self.verbose:
                logger.error(f"处理文件 {file_path} 时出错: {e}")

        return file_change

    def process_files(self) -> Dict[str, FileChange]:
        """
        处理指定路径中的所有文件
        
        Returns:
            文件变更字典，键为文件路径，值为FileChange对象
        """
        self.results = {}
        self.total_files_processed = 0
        self.total_files_modified = 0
        self.total_matches = 0
        self.errors = []

        if self.parallel:
            self._process_files_parallel()
        else:
            self._process_files_sequential()

        return self.results

    def _process_files_sequential(self):
        """顺序处理文件"""
        for path in self.paths:
            if os.path.isfile(path):
                self._process_single_file(path)
            elif os.path.isdir(path):
                self._process_directory(path)
            else:
                logger.warning(f"路径不存在或无法访问: {path}")

    def _process_files_parallel(self):
        """并行处理文件（使用多线程）"""
        import concurrent.futures

        # 收集所有需要处理的文件
        files_to_process = []
        for path in self.paths:
            if os.path.isfile(path):
                files_to_process.append(path)
            elif os.path.isdir(path):
                for file_path in self._collect_files_in_directory(path):
                    files_to_process.append(file_path)
            else:
                logger.warning(f"路径不存在或无法访问: {path}")

        # 使用线程池处理文件
        with concurrent.futures.ThreadPoolExecutor() as executor:
            future_to_file = {executor.submit(self._replace_in_file, file_path): file_path
                              for file_path in files_to_process}

            for future in concurrent.futures.as_completed(future_to_file):
                file_path = future_to_file[future]
                try:
                    file_change = future.result()
                    self._update_statistics(file_change)
                except Exception as e:
                    self.errors.append(f"{file_path}: {str(e)}")
                    if not self.ignore_errors:
                        raise

    def _collect_files_in_directory(self, dir_path: str) -> List[str]:
        """收集目录中的所有文件路径"""
        files = []

        for root, dirs, filenames in os.walk(dir_path):
            # 过滤掉不应处理的目录
            dirs[:] = [d for d in dirs if self._should_process_dir(os.path.join(root, d))]

            for filename in filenames:
                file_path = os.path.join(root, filename)
                files.append(file_path)

            # 如果不递归处理子目录，则在第一次迭代后退出
            if not self.recursive:
                break

        return files

    def _process_directory(self, dir_path: str):
        """处理目录中的文件"""
        for root, dirs, filenames in os.walk(dir_path):
            # 过滤掉不应处理的目录
            dirs[:] = [d for d in dirs if self._should_process_dir(os.path.join(root, d))]

            for filename in filenames:
                file_path = os.path.join(root, filename)
                self._process_single_file(file_path)

            # 如果不递归处理子目录，则在第一次迭代后退出
            if not self.recursive:
                break

    def _process_single_file(self, file_path: str):
        """处理单个文件"""
        file_change = self._replace_in_file(file_path)
        self._update_statistics(file_change)

    def _update_statistics(self, file_change: FileChange):
        """更新统计信息"""
        self.results[file_change.file_path] = file_change
        self.total_files_processed += 1

        if file_change.matches_count > 0:
            self.total_files_modified += 1
            self.total_matches += file_change.matches_count

        if file_change.error:
            self.errors.append(f"{file_change.file_path}: {file_change.error}")

    def generate_report(self) -> str:
        """生成替换操作的详细报告"""
        report = []
        report.append("=== 批量查找替换报告 ===")
        report.append(f"时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        report.append(f"查找模式: '{self.search_pattern}'")
        report.append(f"替换为: '{self.replacement}'")
        report.append(f"替换模式: {self.mode.value}")
        report.append(f"递归处理: {'是' if self.recursive else '否'}")
        report.append(f"处理的路径: {', '.join(self.paths)}")
        report.append(f"包含的文件模式: {', '.join(self.include_patterns)}")
        if self.exclude_patterns:
            report.append(f"排除的文件模式: {', '.join(self.exclude_patterns)}")
        if self.exclude_dirs:
            report.append(f"排除的目录: {', '.join(self.exclude_dirs)}")
        report.append("")
        report.append("=== 处理结果 ===")
        report.append(f"处理的文件总数: {self.total_files_processed}")
        report.append(f"修改的文件数: {self.total_files_modified}")
        report.append(f"替换的匹配总数: {self.total_matches}")
        report.append(f"错误数: {len(self.errors)}")

        if self.total_files_modified > 0:
            report.append("")
            report.append("=== 修改的文件 ===")
            for file_path, change in sorted(self.results.items()):
                if change.matches_count > 0:
                    lines_str = ", ".join(
                        str(line) for line in sorted(change.lines_changed)) if change.lines_changed else "未知"
                    report.append(f"{file_path}: {change.matches_count} 处替换, 修改的行: {lines_str}")

        if self.show_diff and any(change.diff for change in self.results.values()):
            report.append("")
            report.append("=== 详细差异 ===")
            for file_path, change in sorted(self.results.items()):
                if change.diff:
                    report.append(f"\n文件: {file_path}")
                    report.append(change.diff)

        if self.errors:
            report.append("")
            report.append("=== 错误 ===")
            for error in self.errors:
                report.append(error)

        return "\n".join(report)


def parse_size(size_str: str) -> int:
    """解析大小字符串（如 '1KB', '5MB'）为字节数"""
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


def parse_arguments():
    """解析命令行参数"""
    parser = argparse.ArgumentParser(description="文本批量查找替换工具")

    # 基本参数
    parser.add_argument('search', help='要查找的文本或正则表达式模式')
    parser.add_argument('replacement', help='要替换成的内容')
    parser.add_argument('paths', nargs='+', help='要处理的文件或目录路径列表')

    # 替换模式
    replace_mode = parser.add_argument_group('替换模式选项')
    mode_group = replace_mode.add_mutually_exclusive_group()
    mode_group.add_argument('-t', '--text', action='store_true', help='普通文本替换（默认）')
    mode_group.add_argument('-r', '--regex', action='store_true', help='正则表达式替换')
    mode_group.add_argument('-w', '--whole-word', action='store_true', help='全词匹配替换')
    mode_group.add_argument('-l', '--line', action='store_true', help='整行替换（包含匹配文本的整行）')
    replace_mode.add_argument('-i', '--ignore-case', action='store_true', help='忽略大小写')

    # 文件选项
    file_group = parser.add_argument_group('文件选项')
    file_group.add_argument('--no-recursive', action='store_true', help='不递归处理子目录')
    file_group.add_argument('--include', nargs='+', metavar='PATTERN', help='要包含的文件模式列表（如 *.txt）')
    file_group.add_argument('--exclude', nargs='+', metavar='PATTERN', help='要排除的文件模式列表')
    file_group.add_argument('--exclude-dir', nargs='+', metavar='DIR', help='要排除的目录名列表')
    file_group.add_argument('--max-size', help='处理的最大文件大小（如 1MB）')
    file_group.add_argument('--encoding', default='utf-8', help='文件编码（默认: utf-8）')
    file_group.add_argument('--include-binary', action='store_true', help='也处理二进制文件（默认跳过）')

    # 操作选项
    operation_group = parser.add_argument_group('操作选项')
    operation_group.add_argument('-n', '--dry-run', action='store_true', help='模拟运行，不实际修改文件')
    operation_group.add_argument('-b', '--backup', action='store_true', help='备份原始文件')
    operation_group.add_argument('--backup-ext', default='.bak', help='备份文件扩展名（默认: .bak）')
    operation_group.add_argument('--limit', type=int, default=0, help='每个文件最多替换的匹配次数（默认: 无限制）')
    operation_group.add_argument('--force', action='store_true', help='忽略错误并继续处理')
    operation_group.add_argument('--parallel', action='store_true', help='使用并行处理（多核处理）')

    # 输出选项
    output_group = parser.add_argument_group('输出选项')
    output_group.add_argument('-d', '--diff', action='store_true', help='显示详细的替换差异')
    output_group.add_argument('-o', '--output', help='将报告保存到指定文件')
    output_group.add_argument('--summary', action='store_true', help='仅显示摘要信息')
    output_group.add_argument('-v', '--verbose', action='store_true', help='显示详细信息')
    output_group.add_argument('-q', '--quiet', action='store_true', help='静默模式')

    args = parser.parse_args()

    # 设置日志级别
    if args.quiet:
        logging.getLogger().setLevel(logging.WARNING)
    elif args.verbose:
        logging.getLogger().setLevel(logging.DEBUG)

    return args


def main():
    """主函数"""
    args = parse_arguments()

    try:
        # 确定替换模式
        mode = ReplaceMode.TEXT  # 默认是普通文本替换
        if args.regex:
            mode = ReplaceMode.REGEX
        elif args.whole_word:
            mode = ReplaceMode.WHOLE_WORD
        elif args.line:
            mode = ReplaceMode.LINE

        # 处理最大文件大小
        max_size = None
        if args.max_size:
            try:
                max_size = parse_size(args.max_size)
            except ValueError as e:
                logger.error(str(e))
                return 1

        # 创建文本替换器
        replacer = TextReplacer(
            search_pattern=args.search,
            replacement=args.replacement,
            paths=args.paths,
            mode=mode,
            recursive=not args.no_recursive,
            include_patterns=args.include,
            exclude_patterns=args.exclude,
            exclude_dirs=args.exclude_dir,
            max_size=max_size,
            ignore_case=args.ignore_case,
            backup=args.backup,
            backup_extension=args.backup_ext,
            encoding=args.encoding,
            ignore_errors=args.force,
            match_limit=args.limit,
            skip_binary=not args.include_binary,
            dry_run=args.dry_run,
            show_diff=args.diff or not args.summary,
            parallel=args.parallel,
            verbose=args.verbose
        )

        # 执行替换
        replacer.process_files()

        # 生成报告
        report = replacer.generate_report()

        # 输出报告
        if args.output:
            with open(args.output, 'w', encoding='utf-8') as f:
                f.write(report)
            if not args.quiet:
                print(f"报告已保存至：{args.output}")
        else:
            if args.summary:
                # 仅显示摘要部分
                summary_lines = []
                for line in report.splitlines():
                    if line.startswith("===") or not summary_lines:
                        summary_lines.append(line)
                    elif summary_lines and not line.strip():
                        summary_lines.append(line)
                    elif line.startswith("处理的文件") or line.startswith("修改的文件数") or line.startswith(
                            "替换的匹配"):
                        summary_lines.append(line)
                print("\n".join(summary_lines))
            else:
                print(report)

        # 如果是干运行模式，提醒用户
        if args.dry_run:
            print("\n注意：这是模拟运行，没有对文件进行实际修改。")
            print("如需进行实际替换，请移除 --dry-run 选项。")

        return 0

    except Exception as e:
        logger.error(f"执行过程中出错: {e}")
        if args.verbose:
            import traceback
            traceback.print_exc()
        return 1


if __name__ == "__main__":
    sys.exit(main())
