#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
文本文件合并工具

这个脚本用于将多个文本文件合并成一个文件，支持各种合并方式、
文件排序方法、分隔符选项和文本处理功能。适用于日志整合、
文档汇编、数据收集等场景。
"""

import argparse
import datetime
import logging
import os
import re
import sys
from enum import Enum
from typing import List, Optional

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)
logger = logging.getLogger(__name__)


class SortMethod(Enum):
    """文件排序方法枚举"""
    NAME = "name"  # 按文件名排序
    SIZE = "size"  # 按文件大小排序
    MODIFIED = "modified"  # 按修改时间排序
    CUSTOM = "custom"  # 按用户自定义顺序


class SeparatorType(Enum):
    """文件分隔符类型枚举"""
    NONE = "none"  # 无分隔符
    NEWLINE = "newline"  # 空行
    CUSTOM = "custom"  # 自定义分隔符
    FILENAME = "filename"  # 文件名作为分隔符
    FILENAME_BOX = "filename_box"  # 带框的文件名
    MARKER_LINE = "marker_line"  # 标记行（如 ----------）


class TextProcessor:
    """文本处理类，提供各种文本处理功能"""

    def __init__(
            self,
            remove_empty_lines: bool = False,
            remove_duplicate_lines: bool = False,
            trim_lines: bool = False,
            line_prefix: Optional[str] = None,
            line_suffix: Optional[str] = None,
            include_pattern: Optional[str] = None,
            exclude_pattern: Optional[str] = None,
            case_sensitive: bool = True,
            max_line_length: Optional[int] = None,
            remove_html: bool = False,
            convert_tabs: bool = False,
            tab_size: int = 4,
            number_lines: bool = False,
            wrap_lines: Optional[int] = None
    ):
        """
        初始化文本处理器

        Args:
            remove_empty_lines: 是否删除空行
            remove_duplicate_lines: 是否删除重复行
            trim_lines: 是否修剪行（删除首尾空白）
            line_prefix: 行前缀
            line_suffix: 行后缀
            include_pattern: 包含模式（正则表达式）
            exclude_pattern: 排除模式（正则表达式）
            case_sensitive: 是否区分大小写
            max_line_length: 最大行长度
            remove_html: 是否删除HTML标签
            convert_tabs: 是否将制表符转换为空格
            tab_size: 制表符大小
            number_lines: 是否添加行号
            wrap_lines: 行包装宽度
        """
        self.remove_empty_lines = remove_empty_lines
        self.remove_duplicate_lines = remove_duplicate_lines
        self.trim_lines = trim_lines
        self.line_prefix = line_prefix
        self.line_suffix = line_suffix
        self.case_sensitive = case_sensitive
        self.max_line_length = max_line_length
        self.remove_html = remove_html
        self.convert_tabs = convert_tabs
        self.tab_size = tab_size
        self.number_lines = number_lines
        self.wrap_lines = wrap_lines

        # 编译正则表达式
        self.include_regex = None
        if include_pattern:
            flags = 0 if case_sensitive else re.IGNORECASE
            self.include_regex = re.compile(include_pattern, flags)

        self.exclude_regex = None
        if exclude_pattern:
            flags = 0 if case_sensitive else re.IGNORECASE
            self.exclude_regex = re.compile(exclude_pattern, flags)

        self.html_regex = None
        if remove_html:
            self.html_regex = re.compile(r'<[^>]+>')

        # 用于去重的集合
        self.seen_lines = set()
        self.line_number = 1

    def process_line(self, line: str) -> Optional[str]:
        """
        处理单行文本

        Args:
            line: 要处理的文本行

        Returns:
            处理后的文本行，如果行应该被过滤则返回 None
        """
        # 删除空行
        if self.remove_empty_lines and not line.strip():
            return None

        # 修剪行
        if self.trim_lines:
            line = line.strip()

        # 检查包含模式
        if self.include_regex and not self.include_regex.search(line):
            return None

        # 检查排除模式
        if self.exclude_regex and self.exclude_regex.search(line):
            return None

        # 删除HTML标签
        if self.remove_html:
            line = self.html_regex.sub('', line)

        # 转换制表符
        if self.convert_tabs:
            line = line.replace('\t', ' ' * self.tab_size)

        # 检查行长度
        if self.max_line_length and len(line) > self.max_line_length:
            line = line[:self.max_line_length]

        # 添加行前缀和后缀
        if self.line_prefix:
            line = self.line_prefix + line
        if self.line_suffix:
            line = line + self.line_suffix

        # 添加行号
        if self.number_lines:
            line = f"{self.line_number:6d}: {line}"
            self.line_number += 1

        # 行包装
        if self.wrap_lines and len(line) > self.wrap_lines:
            wrapped_lines = []
            for i in range(0, len(line), self.wrap_lines):
                wrapped_lines.append(line[i:i + self.wrap_lines])
            line = '\n'.join(wrapped_lines)

        # 检查重复行
        if self.remove_duplicate_lines:
            # 如果我们不区分大小写，使用小写版本进行比较
            line_key = line.lower() if not self.case_sensitive else line
            if line_key in self.seen_lines:
                return None
            self.seen_lines.add(line_key)

        return line

    def process_file(self, file_path: str, encoding: str = 'utf-8') -> List[str]:
        """
        处理整个文件

        Args:
            file_path: 文件路径
            encoding: 文件编码

        Returns:
            处理后的文件内容行列表
        """
        try:
            with open(file_path, 'r', encoding=encoding, errors='replace') as f:
                lines = f.readlines()

            processed_lines = []
            for line in lines:
                processed_line = self.process_line(line.rstrip('\r\n'))
                if processed_line is not None:
                    processed_lines.append(processed_line)

            return processed_lines
        except Exception as e:
            logger.error(f"处理文件 {file_path} 时出错: {e}")
            return [f"Error processing {file_path}: {e}"]

    def reset_state(self):
        """重置处理器状态"""
        self.seen_lines = set()
        self.line_number = 1


class TextMerger:
    """文本合并器类，用于合并多个文本文件"""

    def __init__(
            self,
            file_paths: List[str],
            output_path: Optional[str] = None,
            sort_method: SortMethod = SortMethod.NAME,
            separator_type: SeparatorType = SeparatorType.NEWLINE,
            custom_separator: Optional[str] = None,
            file_encoding: str = 'utf-8',
            output_encoding: str = 'utf-8',
            sort_reverse: bool = False,
            processor: Optional[TextProcessor] = None,
            skip_errors: bool = False,
            header: Optional[str] = None,
            footer: Optional[str] = None,
            custom_order: Optional[List[str]] = None
    ):
        """
        初始化文本合并器

        Args:
            file_paths: 要合并的文件路径列表
            output_path: 输出文件路径（如果为None，则输出到标准输出）
            sort_method: 文件排序方法
            separator_type: 文件分隔符类型
            custom_separator: 自定义分隔符
            file_encoding: 输入文件编码
            output_encoding: 输出文件编码
            sort_reverse: 是否逆序排序
            processor: 文本处理器
            skip_errors: 是否跳过错误
            header: 添加到输出文件开头的文本
            footer: 添加到输出文件结尾的文本
            custom_order: 自定义文件排序顺序
        """
        self.file_paths = file_paths
        self.output_path = output_path
        self.sort_method = sort_method
        self.separator_type = separator_type
        self.custom_separator = custom_separator
        self.file_encoding = file_encoding
        self.output_encoding = output_encoding
        self.sort_reverse = sort_reverse
        self.processor = processor or TextProcessor()
        self.skip_errors = skip_errors
        self.header = header
        self.footer = footer
        self.custom_order = custom_order

    def sort_files(self) -> List[str]:
        """
        排序文件路径

        Returns:
            排序后的文件路径列表
        """
        # 检查文件是否存在
        existing_files = []
        for file_path in self.file_paths:
            if not os.path.exists(file_path):
                if not self.skip_errors:
                    logger.error(f"文件不存在: {file_path}")
                continue
            if not os.path.isfile(file_path):
                if not self.skip_errors:
                    logger.error(f"路径不是文件: {file_path}")
                continue
            existing_files.append(file_path)

        # 如果是自定义顺序，使用指定顺序
        if self.sort_method == SortMethod.CUSTOM and self.custom_order:
            # 使用在custom_order中出现的顺序排序文件，过滤掉不存在的文件
            file_order = {file: i for i, file in enumerate(self.custom_order)}
            existing_files = sorted(
                existing_files,
                key=lambda f: file_order.get(os.path.basename(f), float('inf'))
            )
            return existing_files

        # 按指定方法排序
        if self.sort_method == SortMethod.NAME:
            sorted_files = sorted(existing_files, key=lambda f: os.path.basename(f).lower(), reverse=self.sort_reverse)
        elif self.sort_method == SortMethod.SIZE:
            sorted_files = sorted(existing_files, key=lambda f: os.path.getsize(f), reverse=self.sort_reverse)
        elif self.sort_method == SortMethod.MODIFIED:
            sorted_files = sorted(existing_files, key=lambda f: os.path.getmtime(f), reverse=self.sort_reverse)
        else:
            # 默认按名称排序
            sorted_files = sorted(existing_files, key=lambda f: os.path.basename(f).lower(), reverse=self.sort_reverse)

        return sorted_files

    def get_separator(self, file_path: str) -> str:
        """
        根据分隔符类型和文件生成分隔符

        Args:
            file_path: 文件路径

        Returns:
            分隔符字符串
        """
        if self.separator_type == SeparatorType.NONE:
            return ""
        elif self.separator_type == SeparatorType.NEWLINE:
            return "\n"
        elif self.separator_type == SeparatorType.CUSTOM:
            return self.custom_separator or "\n---\n"
        elif self.separator_type == SeparatorType.FILENAME:
            return f"\n# {os.path.basename(file_path)}\n"
        elif self.separator_type == SeparatorType.FILENAME_BOX:
            filename = os.path.basename(file_path)
            box_line = "+" + "-" * (len(filename) + 2) + "+"
            return f"\n{box_line}\n| {filename} |\n{box_line}\n"
        elif self.separator_type == SeparatorType.MARKER_LINE:
            return "\n" + "-" * 80 + "\n"
        else:
            return "\n"

    def merge_files(self) -> str:
        """
        合并文件

        Returns:
            合并后的文本内容
        """
        # 排序文件
        sorted_files = self.sort_files()
        if not sorted_files:
            logger.error("没有有效的文件可合并")
            return ""

        # 准备结果
        result = []
        if self.header:
            result.append(self.header)

        # 处理每个文件
        for i, file_path in enumerate(sorted_files):
            # 如果不是第一个文件，添加分隔符
            if i > 0:
                result.append(self.get_separator(file_path))

            # 重置文本处理器状态
            self.processor.reset_state()

            # 处理文件内容
            try:
                processed_lines = self.processor.process_file(file_path, self.file_encoding)
                result.extend(processed_lines)
            except Exception as e:
                if self.skip_errors:
                    logger.error(f"处理文件 {file_path} 时出错: {e}")
                else:
                    raise

        if self.footer:
            result.append(self.footer)

        # 连接结果
        return "\n".join(result)

    def save_result(self, content: str) -> bool:
        """
        保存合并结果

        Args:
            content: 要保存的内容

        Returns:
            保存是否成功
        """
        if self.output_path:
            try:
                with open(self.output_path, 'w', encoding=self.output_encoding) as f:
                    f.write(content)
                logger.info(f"合并结果已保存到：{self.output_path}")
                return True
            except Exception as e:
                logger.error(f"保存结果时出错: {e}")
                return False
        else:
            # 输出到标准输出
            print(content)
            return True

    def run(self) -> bool:
        """
        运行合并操作

        Returns:
            操作是否成功
        """
        try:
            content = self.merge_files()
            return self.save_result(content)
        except Exception as e:
            logger.error(f"合并过程中出错: {e}")
            if not self.skip_errors:
                raise
            return False


def parse_arguments():
    """解析命令行参数"""
    parser = argparse.ArgumentParser(description="文本文件合并工具")

    # 基本参数
    parser.add_argument('files', nargs='+', help='要合并的文件列表')
    parser.add_argument('-o', '--output', help='输出文件路径（如果省略则输出到标准输出）')

    # 排序选项
    sort_group = parser.add_argument_group('排序选项')
    sort_group.add_argument('-s', '--sort', choices=['name', 'size', 'modified', 'custom'], default='name',
                            help='文件排序方法（默认: name）')
    sort_group.add_argument('-r', '--reverse', action='store_true', help='逆序排序')
    sort_group.add_argument('--custom-order', nargs='+',
                            help='自定义文件排序顺序（仅当sort=custom时有效）')

    # 分隔符选项
    separator_group = parser.add_argument_group('分隔符选项')
    separator_group.add_argument('--separator',
                                 choices=['none', 'newline', 'custom', 'filename', 'filename_box', 'marker_line'],
                                 default='newline', help='文件分隔符类型（默认: newline）')
    separator_group.add_argument('--custom-separator', help='自定义分隔符（当separator=custom时使用）')

    # 编码选项
    encoding_group = parser.add_argument_group('编码选项')
    encoding_group.add_argument('--file-encoding', default='utf-8',
                                help='输入文件编码（默认: utf-8）')
    encoding_group.add_argument('--output-encoding', default='utf-8',
                                help='输出文件编码（默认: utf-8）')

    # 处理选项
    process_group = parser.add_argument_group('处理选项')
    process_group.add_argument('--remove-empty-lines', action='store_true',
                               help='删除空行')
    process_group.add_argument('--remove-duplicate-lines', action='store_true',
                               help='删除重复行')
    process_group.add_argument('--trim-lines', action='store_true',
                               help='修剪行（删除首尾空白）')
    process_group.add_argument('--line-prefix',
                               help='添加到每行开头的前缀')
    process_group.add_argument('--line-suffix',
                               help='添加到每行结尾的后缀')
    process_group.add_argument('--include',
                               help='包含正则表达式模式（仅包含匹配的行）')
    process_group.add_argument('--exclude',
                               help='排除正则表达式模式（排除匹配的行）')
    process_group.add_argument('--ignore-case', action='store_true',
                               help='正则表达式忽略大小写')
    process_group.add_argument('--max-line-length', type=int,
                               help='最大行长度（截断更长的行）')
    process_group.add_argument('--remove-html', action='store_true',
                               help='删除HTML标签')
    process_group.add_argument('--convert-tabs', action='store_true',
                               help='将制表符转换为空格')
    process_group.add_argument('--tab-size', type=int, default=4,
                               help='制表符大小（默认: 4）')
    process_group.add_argument('--number-lines', action='store_true',
                               help='添加行号')
    process_group.add_argument('--wrap-lines', type=int,
                               help='行包装宽度（每行最大字符数）')

    # 其他选项
    other_group = parser.add_argument_group('其他选项')
    other_group.add_argument('--skip-errors', action='store_true',
                             help='跳过处理错误')
    other_group.add_argument('--header',
                             help='添加到输出文件开头的文本')
    other_group.add_argument('--header-file',
                             help='从文件读取要添加到输出文件开头的文本')
    other_group.add_argument('--footer',
                             help='添加到输出文件结尾的文本')
    other_group.add_argument('--footer-file',
                             help='从文件读取要添加到输出文件结尾的文本')
    other_group.add_argument('--no-warning', action='store_true',
                             help='不添加生成文件的警告注释')
    other_group.add_argument('-q', '--quiet', action='store_true',
                             help='静默模式，减少输出')
    other_group.add_argument('-v', '--verbose', action='store_true',
                             help='详细模式，显示更多信息')

    return parser.parse_args()


def read_file_content(file_path: str, encoding: str = 'utf-8') -> str:
    """
    读取文件内容
    
    Args:
        file_path: 文件路径
        encoding: 文件编码
        
    Returns:
        文件内容
    """
    try:
        with open(file_path, 'r', encoding=encoding) as f:
            return f.read()
    except Exception as e:
        logger.error(f"读取文件 {file_path} 时出错: {e}")
        return ""


def main():
    """主函数"""
    args = parse_arguments()

    # 配置日志级别
    if args.quiet:
        logging.getLogger().setLevel(logging.WARNING)
    elif args.verbose:
        logging.getLogger().setLevel(logging.DEBUG)

    # 创建文本处理器
    processor = TextProcessor(
        remove_empty_lines=args.remove_empty_lines,
        remove_duplicate_lines=args.remove_duplicate_lines,
        trim_lines=args.trim_lines,
        line_prefix=args.line_prefix,
        line_suffix=args.line_suffix,
        include_pattern=args.include,
        exclude_pattern=args.exclude,
        case_sensitive=not args.ignore_case,
        max_line_length=args.max_line_length,
        remove_html=args.remove_html,
        convert_tabs=args.convert_tabs,
        tab_size=args.tab_size,
        number_lines=args.number_lines,
        wrap_lines=args.wrap_lines
    )

    # 准备头部和尾部
    header = args.header
    if args.header_file:
        header = read_file_content(args.header_file, args.file_encoding)

    footer = args.footer
    if args.footer_file:
        footer = read_file_content(args.footer_file, args.file_encoding)

    # 添加自动生成的警告
    if not args.no_warning and args.output:
        timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        auto_header = f"""
# 此文件由文本文件合并工具自动生成
# 生成时间: {timestamp}
# 源文件数量: {len(args.files)}
# 请勿直接修改此文件，应修改源文件后重新合并

"""
        if header:
            header = auto_header + header
        else:
            header = auto_header

    # 创建文本合并器
    merger = TextMerger(
        file_paths=args.files,
        output_path=args.output,
        sort_method=SortMethod(args.sort),
        separator_type=SeparatorType(args.separator),
        custom_separator=args.custom_separator,
        file_encoding=args.file_encoding,
        output_encoding=args.output_encoding,
        sort_reverse=args.reverse,
        processor=processor,
        skip_errors=args.skip_errors,
        header=header,
        footer=footer,
        custom_order=args.custom_order
    )

    # 运行合并操作
    try:
        success = merger.run()
        if success:
            if args.output:
                logger.info(f"文件合并成功：{args.output}")
            else:
                logger.info("文件合并内容已输出到标准输出")
        else:
            logger.error("文件合并操作失败")
            return 1
    except Exception as e:
        logger.error(f"执行合并操作时出错: {e}")
        if args.verbose:
            import traceback
            traceback.print_exc()
        return 1

    return 0


if __name__ == "__main__":
    sys.exit(main())
