#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
文件比较工具

这个脚本提供了文件和目录比较功能，可以识别并显示文件之间的差异，
以及比较目录结构和内容。支持文本和二进制文件比较，并提供多种差异
输出格式选项。
"""

import argparse
import difflib
import hashlib
import logging
import os
import sys
import time
from enum import Enum
from typing import Dict, List, Optional

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)
logger = logging.getLogger(__name__)


class CompareResult(Enum):
    """比较结果枚举"""
    IDENTICAL = 0  # 完全相同
    CONTENT_DIFF = 1  # 内容不同
    LEFT_ONLY = 2  # 仅存在于左侧
    RIGHT_ONLY = 3  # 仅存在于右侧
    TYPE_DIFF = 4  # 类型不同（一个是文件，一个是目录）


class FileComparer:
    """
    文件比较工具类
    
    提供单个文件比较和目录结构比较功能
    """

    def __init__(self,
                 ignore_whitespace: bool = False,
                 ignore_case: bool = False,
                 ignore_blank_lines: bool = False,
                 context_lines: int = 3):
        """
        初始化比较器
        
        Args:
            ignore_whitespace: 是否忽略空白字符差异
            ignore_case: 是否忽略大小写差异
            ignore_blank_lines: 是否忽略空行
            context_lines: 显示差异上下文的行数
        """
        self.ignore_whitespace = ignore_whitespace
        self.ignore_case = ignore_case
        self.ignore_blank_lines = ignore_blank_lines
        self.context_lines = context_lines

        # 用于存储比较结果
        self.result_summary = {
            CompareResult.IDENTICAL: [],
            CompareResult.CONTENT_DIFF: [],
            CompareResult.LEFT_ONLY: [],
            CompareResult.RIGHT_ONLY: [],
            CompareResult.TYPE_DIFF: []
        }

        # 存储详细的差异信息
        self.diff_details = {}

    def reset(self):
        """重置比较结果"""
        self.result_summary = {
            CompareResult.IDENTICAL: [],
            CompareResult.CONTENT_DIFF: [],
            CompareResult.LEFT_ONLY: [],
            CompareResult.RIGHT_ONLY: [],
            CompareResult.TYPE_DIFF: []
        }
        self.diff_details = {}

    def compare_files(self,
                      file1_path: str,
                      file2_path: str,
                      binary_mode: bool = False) -> CompareResult:
        """
        比较两个文件的内容
        
        Args:
            file1_path: 第一个文件路径
            file2_path: 第二个文件路径
            binary_mode: 是否以二进制模式比较
            
        Returns:
            比较结果
        """
        if not os.path.exists(file1_path):
            raise FileNotFoundError(f"文件不存在: {file1_path}")

        if not os.path.exists(file2_path):
            raise FileNotFoundError(f"文件不存在: {file2_path}")

        if not os.path.isfile(file1_path) or not os.path.isfile(file2_path):
            raise ValueError("两个路径都必须是文件")

        # 首先比较文件大小
        size1 = os.path.getsize(file1_path)
        size2 = os.path.getsize(file2_path)

        if size1 != size2:
            logger.debug(f"文件大小不同: {size1} vs {size2}")
            return CompareResult.CONTENT_DIFF

        # 如果是二进制模式或文件太大，使用哈希值比较
        if binary_mode or size1 > 10 * 1024 * 1024:  # 大于10MB的文件
            return self._compare_files_by_hash(file1_path, file2_path)
        else:
            # 尝试文本比较
            try:
                return self._compare_text_files(file1_path, file2_path)
            except UnicodeDecodeError:
                # 如果解码失败，可能是二进制文件
                logger.debug("文本比较失败，切换到二进制比较")
                return self._compare_files_by_hash(file1_path, file2_path)

    def _compare_files_by_hash(self, file1_path: str, file2_path: str) -> CompareResult:
        """
        通过计算哈希值比较文件
        
        Args:
            file1_path: 第一个文件路径
            file2_path: 第二个文件路径
            
        Returns:
            比较结果
        """
        hash1 = self._calculate_file_hash(file1_path)
        hash2 = self._calculate_file_hash(file2_path)

        if hash1 == hash2:
            return CompareResult.IDENTICAL
        else:
            return CompareResult.CONTENT_DIFF

    def _calculate_file_hash(self, file_path: str) -> str:
        """
        计算文件的MD5哈希值
        
        Args:
            file_path: 文件路径
            
        Returns:
            MD5哈希值
        """
        hasher = hashlib.md5()
        with open(file_path, 'rb') as f:
            buf = f.read(65536)  # 64kb chunks
            while len(buf) > 0:
                hasher.update(buf)
                buf = f.read(65536)
        return hasher.hexdigest()

    def _compare_text_files(self, file1_path: str, file2_path: str) -> CompareResult:
        """
        比较两个文本文件
        
        Args:
            file1_path: 第一个文件路径
            file2_path: 第二个文件路径
            
        Returns:
            比较结果
        """
        with open(file1_path, 'r', encoding='utf-8') as f1, open(file2_path, 'r', encoding='utf-8') as f2:
            lines1 = f1.readlines()
            lines2 = f2.readlines()

        # 预处理文本行
        if self.ignore_whitespace:
            lines1 = [line.strip() for line in lines1]
            lines2 = [line.strip() for line in lines2]

        if self.ignore_case:
            lines1 = [line.lower() for line in lines1]
            lines2 = [line.lower() for line in lines2]

        if self.ignore_blank_lines:
            lines1 = [line for line in lines1 if line.strip()]
            lines2 = [line for line in lines2 if line.strip()]

        # 计算差异
        diff = list(difflib.unified_diff(
            lines1, lines2,
            fromfile=file1_path,
            tofile=file2_path,
            n=self.context_lines
        ))

        # 存储差异详情
        if diff:
            self.diff_details[file1_path] = diff
            return CompareResult.CONTENT_DIFF
        else:
            return CompareResult.IDENTICAL

    def compare_directories(self,
                            dir1_path: str,
                            dir2_path: str,
                            recursive: bool = True,
                            ignore_patterns: List[str] = None) -> Dict:
        """
        比较两个目录的结构和内容
        
        Args:
            dir1_path: 第一个目录路径
            dir2_path: 第二个目录路径
            recursive: 是否递归比较子目录
            ignore_patterns: 要忽略的文件或目录模式列表
            
        Returns:
            比较结果摘要
        """
        self.reset()

        if not os.path.exists(dir1_path) or not os.path.exists(dir2_path):
            raise FileNotFoundError("目录不存在")

        if not os.path.isdir(dir1_path) or not os.path.isdir(dir2_path):
            raise ValueError("两个路径都必须是目录")

        # 规范化路径
        dir1_path = os.path.abspath(dir1_path)
        dir2_path = os.path.abspath(dir2_path)

        # 进行目录比较
        self._compare_dir_recursive(
            dir1_path, dir2_path,
            recursive=recursive,
            ignore_patterns=ignore_patterns or []
        )

        return self.result_summary

    def _compare_dir_recursive(self,
                               dir1_path: str,
                               dir2_path: str,
                               relative_path: str = "",
                               recursive: bool = True,
                               ignore_patterns: List[str] = None) -> None:
        """
        递归比较目录
        
        Args:
            dir1_path: 第一个目录路径
            dir2_path: 第二个目录路径
            relative_path: 相对于根目录的路径
            recursive: 是否递归比较子目录
            ignore_patterns: 要忽略的文件或目录模式列表
        """
        ignore_patterns = ignore_patterns or []

        # 获取两个目录中的文件和子目录
        entries1 = set(os.listdir(dir1_path))
        entries2 = set(os.listdir(dir2_path))

        # 过滤忽略的文件和目录
        for pattern in ignore_patterns:
            entries1 = {e for e in entries1 if not self._match_pattern(e, pattern)}
            entries2 = {e for e in entries2 if not self._match_pattern(e, pattern)}

        # 找出仅在第一个目录中的项
        for entry in entries1 - entries2:
            path = os.path.join(relative_path, entry) if relative_path else entry
            full_path = os.path.join(dir1_path, entry)
            self.result_summary[CompareResult.LEFT_ONLY].append(path)

        # 找出仅在第二个目录中的项
        for entry in entries2 - entries1:
            path = os.path.join(relative_path, entry) if relative_path else entry
            full_path = os.path.join(dir2_path, entry)
            self.result_summary[CompareResult.RIGHT_ONLY].append(path)

        # 比较两个目录中都存在的项
        for entry in entries1 & entries2:
            path1 = os.path.join(dir1_path, entry)
            path2 = os.path.join(dir2_path, entry)
            rel_path = os.path.join(relative_path, entry) if relative_path else entry

            # 检查类型是否相同（文件vs目录）
            is_dir1 = os.path.isdir(path1)
            is_dir2 = os.path.isdir(path2)

            if is_dir1 != is_dir2:
                self.result_summary[CompareResult.TYPE_DIFF].append(rel_path)
                continue

            if is_dir1 and is_dir2:
                # 两者都是目录，如果递归则继续比较
                if recursive:
                    self._compare_dir_recursive(
                        path1, path2,
                        relative_path=rel_path,
                        recursive=recursive,
                        ignore_patterns=ignore_patterns
                    )
            else:
                # 两者都是文件，比较内容
                try:
                    result = self.compare_files(path1, path2)
                    self.result_summary[result].append(rel_path)
                except Exception as e:
                    logger.error(f"比较文件时出错 {rel_path}: {e}")

    def _match_pattern(self, name: str, pattern: str) -> bool:
        """
        检查文件名是否匹配给定模式
        
        Args:
            name: 文件或目录名
            pattern: 匹配模式
            
        Returns:
            是否匹配
        """
        import fnmatch
        return fnmatch.fnmatch(name, pattern)

    def generate_diff_report(self,
                             output_format: str = 'text',
                             output_file: Optional[str] = None) -> Optional[str]:
        """
        生成差异报告
        
        Args:
            output_format: 输出格式 ('text', 'html', 'json')
            output_file: 输出文件路径
            
        Returns:
            如果没有指定输出文件，则返回报告内容
        """
        if output_format == 'text':
            report = self._generate_text_report()
        elif output_format == 'html':
            report = self._generate_html_report()
        elif output_format == 'json':
            report = self._generate_json_report()
        else:
            raise ValueError(f"不支持的输出格式: {output_format}")

        if output_file:
            with open(output_file, 'w', encoding='utf-8') as f:
                f.write(report)
            return None
        else:
            return report

    def _generate_text_report(self) -> str:
        """
        生成文本格式的差异报告
        
        Returns:
            报告内容
        """
        lines = ["文件比较报告", "=" * 50, ""]

        # 添加摘要信息
        lines.append("比较摘要:")
        lines.append(f"- 相同文件: {len(self.result_summary[CompareResult.IDENTICAL])}")
        lines.append(f"- 内容不同: {len(self.result_summary[CompareResult.CONTENT_DIFF])}")
        lines.append(f"- 仅左侧存在: {len(self.result_summary[CompareResult.LEFT_ONLY])}")
        lines.append(f"- 仅右侧存在: {len(self.result_summary[CompareResult.RIGHT_ONLY])}")
        lines.append(f"- 类型不同: {len(self.result_summary[CompareResult.TYPE_DIFF])}")
        lines.append("")

        # 添加详细信息
        if self.result_summary[CompareResult.CONTENT_DIFF]:
            lines.append("内容不同的文件:")
            for path in self.result_summary[CompareResult.CONTENT_DIFF]:
                lines.append(f"- {path}")
            lines.append("")

        if self.result_summary[CompareResult.LEFT_ONLY]:
            lines.append("仅在左侧存在的文件:")
            for path in self.result_summary[CompareResult.LEFT_ONLY]:
                lines.append(f"- {path}")
            lines.append("")

        if self.result_summary[CompareResult.RIGHT_ONLY]:
            lines.append("仅在右侧存在的文件:")
            for path in self.result_summary[CompareResult.RIGHT_ONLY]:
                lines.append(f"- {path}")
            lines.append("")

        if self.result_summary[CompareResult.TYPE_DIFF]:
            lines.append("类型不同的项目:")
            for path in self.result_summary[CompareResult.TYPE_DIFF]:
                lines.append(f"- {path}")
            lines.append("")

        # 添加差异详情
        if self.diff_details:
            lines.append("文件差异详情:")
            lines.append("=" * 50)

            for file_path, diff in self.diff_details.items():
                lines.append(f"\n文件: {file_path}")
                lines.append("-" * 50)
                lines.extend([line.rstrip() for line in diff])
                lines.append("-" * 50)

        return "\n".join(lines)

    def _generate_html_report(self) -> str:
        """
        生成HTML格式的差异报告
        
        Returns:
            HTML报告内容
        """
        html = [
            "<!DOCTYPE html>",
            "<html>",
            "<head>",
            "    <meta charset='utf-8'>",
            "    <title>文件比较报告</title>",
            "    <style>",
            "        body { font-family: Arial, sans-serif; margin: 20px; }",
            "        h1, h2 { color: #333; }",
            "        .summary { background-color: #f5f5f5; padding: 10px; border-radius: 5px; }",
            "        .files { margin-top: 20px; }",
            "        .file-group { margin-bottom: 15px; }",
            "        .diff { background-color: #f8f8f8; padding: 10px; border-left: 3px solid #ccc; font-family: monospace; white-space: pre; overflow-x: auto; }",
            "        .diff-header { color: #666; margin-bottom: 5px; }",
            "        .diff-add { background-color: #e6ffed; color: #22863a; }",
            "        .diff-del { background-color: #ffdce0; color: #cb2431; }",
            "        .diff-info { color: #666; }",
            "    </style>",
            "</head>",
            "<body>",
            "    <h1>文件比较报告</h1>",
            "    <div class='summary'>",
            "        <h2>比较摘要</h2>",
            f"        <p>相同文件: {len(self.result_summary[CompareResult.IDENTICAL])}</p>",
            f"        <p>内容不同: {len(self.result_summary[CompareResult.CONTENT_DIFF])}</p>",
            f"        <p>仅左侧存在: {len(self.result_summary[CompareResult.LEFT_ONLY])}</p>",
            f"        <p>仅右侧存在: {len(self.result_summary[CompareResult.RIGHT_ONLY])}</p>",
            f"        <p>类型不同: {len(self.result_summary[CompareResult.TYPE_DIFF])}</p>",
            "    </div>",
            "    <div class='files'>"
        ]

        # 添加内容不同的文件列表
        if self.result_summary[CompareResult.CONTENT_DIFF]:
            html.extend([
                "        <div class='file-group'>",
                "            <h2>内容不同的文件</h2>",
                "            <ul>"
            ])

            for path in self.result_summary[CompareResult.CONTENT_DIFF]:
                html.append(f"                <li>{path}</li>")

            html.extend([
                "            </ul>",
                "        </div>"
            ])

        # 添加仅在左侧存在的文件列表
        if self.result_summary[CompareResult.LEFT_ONLY]:
            html.extend([
                "        <div class='file-group'>",
                "            <h2>仅在左侧存在的文件</h2>",
                "            <ul>"
            ])

            for path in self.result_summary[CompareResult.LEFT_ONLY]:
                html.append(f"                <li>{path}</li>")

            html.extend([
                "            </ul>",
                "        </div>"
            ])

        # 添加仅在右侧存在的文件列表
        if self.result_summary[CompareResult.RIGHT_ONLY]:
            html.extend([
                "        <div class='file-group'>",
                "            <h2>仅在右侧存在的文件</h2>",
                "            <ul>"
            ])

            for path in self.result_summary[CompareResult.RIGHT_ONLY]:
                html.append(f"                <li>{path}</li>")

            html.extend([
                "            </ul>",
                "        </div>"
            ])

        # 添加类型不同的项目列表
        if self.result_summary[CompareResult.TYPE_DIFF]:
            html.extend([
                "        <div class='file-group'>",
                "            <h2>类型不同的项目</h2>",
                "            <ul>"
            ])

            for path in self.result_summary[CompareResult.TYPE_DIFF]:
                html.append(f"                <li>{path}</li>")

            html.extend([
                "            </ul>",
                "        </div>"
            ])

        # 添加差异详情
        if self.diff_details:
            html.extend([
                "        <div class='file-group'>",
                "            <h2>文件差异详情</h2>"
            ])

            for file_path, diff in self.diff_details.items():
                html.extend([
                    f"            <h3>文件: {file_path}</h3>",
                    "            <div class='diff'>"
                ])

                for line in diff:
                    line_html = line.replace("<", "&lt;").replace(">", "&gt;")

                    if line.startswith("+"):
                        html.append(f"<div class='diff-add'>{line_html}</div>")
                    elif line.startswith("-"):
                        html.append(f"<div class='diff-del'>{line_html}</div>")
                    elif line.startswith("@@"):
                        html.append(f"<div class='diff-info'>{line_html}</div>")
                    else:
                        html.append(f"<div>{line_html}</div>")

                html.append("            </div>")

            html.append("        </div>")

        html.extend([
            "    </div>",
            "</body>",
            "</html>"
        ])

        return "\n".join(html)

    def _generate_json_report(self) -> str:
        """
        生成JSON格式的差异报告
        
        Returns:
            JSON报告内容
        """
        import json

        report = {
            "summary": {
                "identical": len(self.result_summary[CompareResult.IDENTICAL]),
                "content_diff": len(self.result_summary[CompareResult.CONTENT_DIFF]),
                "left_only": len(self.result_summary[CompareResult.LEFT_ONLY]),
                "right_only": len(self.result_summary[CompareResult.RIGHT_ONLY]),
                "type_diff": len(self.result_summary[CompareResult.TYPE_DIFF])
            },
            "details": {
                "identical": self.result_summary[CompareResult.IDENTICAL],
                "content_diff": self.result_summary[CompareResult.CONTENT_DIFF],
                "left_only": self.result_summary[CompareResult.LEFT_ONLY],
                "right_only": self.result_summary[CompareResult.RIGHT_ONLY],
                "type_diff": self.result_summary[CompareResult.TYPE_DIFF]
            },
            "diff_details": {}
        }

        # 转换差异详情
        for file_path, diff in self.diff_details.items():
            report["diff_details"][file_path] = diff

        return json.dumps(report, indent=2, ensure_ascii=False)


def get_file_info(file_path: str) -> Dict:
    """
    获取文件信息
    
    Args:
        file_path: 文件路径
        
    Returns:
        文件信息字典
    """
    stat_info = os.stat(file_path)

    return {
        "path": file_path,
        "size": stat_info.st_size,
        "modified": time.ctime(stat_info.st_mtime),
        "created": time.ctime(stat_info.st_ctime),
        "is_dir": os.path.isdir(file_path),
        "is_file": os.path.isfile(file_path)
    }


def parse_arguments():
    """解析命令行参数"""
    parser = argparse.ArgumentParser(description="文件和目录比较工具")

    # 添加位置参数
    parser.add_argument("path1", help="第一个文件或目录路径")
    parser.add_argument("path2", help="第二个文件或目录路径")

    # 添加比较选项
    compare_group = parser.add_argument_group("比较选项")
    compare_group.add_argument("-r", "--recursive", action="store_true", default=True,
                               help="递归比较子目录（默认启用）")
    compare_group.add_argument("--no-recursive", action="store_false", dest="recursive",
                               help="不递归比较子目录")
    compare_group.add_argument("-i", "--ignore-case", action="store_true",
                               help="忽略大小写差异")
    compare_group.add_argument("-w", "--ignore-whitespace", action="store_true",
                               help="忽略空白字符差异")
    compare_group.add_argument("-B", "--ignore-blank-lines", action="store_true",
                               help="忽略空行")
    compare_group.add_argument("-c", "--context-lines", type=int, default=3,
                               help="显示差异上下文的行数（默认: 3）")
    compare_group.add_argument("--binary", action="store_true",
                               help="以二进制模式比较文件")

    # 添加过滤选项
    filter_group = parser.add_argument_group("过滤选项")
    filter_group.add_argument("--ignore", nargs="+", default=[],
                              help="忽略的文件或目录模式列表（如 *.pyc __pycache__）")

    # 添加输出选项
    output_group = parser.add_argument_group("输出选项")
    output_group.add_argument("--format", choices=["text", "html", "json"], default="text",
                              help="输出格式（默认: text）")
    output_group.add_argument("-o", "--output",
                              help="输出报告的文件路径")
    output_group.add_argument("-q", "--quiet", action="store_true",
                              help="静默模式，仅显示摘要信息")
    output_group.add_argument("-v", "--verbose", action="store_true",
                              help="详细模式，显示更多信息")

    return parser.parse_args()


def main():
    """主函数"""
    args = parse_arguments()

    # 配置日志级别
    if args.quiet:
        logging.getLogger().setLevel(logging.WARNING)
    elif args.verbose:
        logging.getLogger().setLevel(logging.DEBUG)

    # 检查路径是否存在
    if not os.path.exists(args.path1):
        logger.error(f"路径不存在: {args.path1}")
        return 1

    if not os.path.exists(args.path2):
        logger.error(f"路径不存在: {args.path2}")
        return 1

    # 创建比较器
    comparer = FileComparer(
        ignore_whitespace=args.ignore_whitespace,
        ignore_case=args.ignore_case,
        ignore_blank_lines=args.ignore_blank_lines,
        context_lines=args.context_lines
    )

    # 确定是文件比较还是目录比较
    is_file1 = os.path.isfile(args.path1)
    is_file2 = os.path.isfile(args.path2)

    if is_file1 and is_file2:
        # 文件比较
        try:
            logger.info(f"正在比较文件: {args.path1} 和 {args.path2}")
            result = comparer.compare_files(args.path1, args.path2, binary_mode=args.binary)

            # 显示比较结果
            if result == CompareResult.IDENTICAL:
                print("文件内容完全相同")
                return 0
            else:
                print("文件内容不同")

                # 生成并显示详细报告
                report = comparer.generate_diff_report(
                    output_format=args.format,
                    output_file=args.output
                )

                if report and not args.quiet:
                    print(report)

                return 1
        except Exception as e:
            logger.error(f"比较文件时出错: {e}")
            return 2

    elif not is_file1 and not is_file2:
        # 目录比较
        try:
            logger.info(f"正在比较目录: {args.path1} 和 {args.path2}")
            comparer.compare_directories(
                args.path1, args.path2,
                recursive=args.recursive,
                ignore_patterns=args.ignore
            )

            # 生成并显示报告
            report = comparer.generate_diff_report(
                output_format=args.format,
                output_file=args.output
            )

            if report and not args.quiet:
                print(report)

            # 如果有任何差异，返回1
            if (comparer.result_summary[CompareResult.CONTENT_DIFF] or
                    comparer.result_summary[CompareResult.LEFT_ONLY] or
                    comparer.result_summary[CompareResult.RIGHT_ONLY] or
                    comparer.result_summary[CompareResult.TYPE_DIFF]):
                return 1
            else:
                print("目录内容完全相同")
                return 0
        except Exception as e:
            logger.error(f"比较目录时出错: {e}")
            return 2

    else:
        # 一个是文件，一个是目录
        logger.error("无法比较: 一个是文件，一个是目录")
        return 2


if __name__ == "__main__":
    try:
        sys.exit(main())
    except KeyboardInterrupt:
        print("\n比较操作被用户中断")
        sys.exit(1)
    except Exception as e:
        logger.error(f"程序出错: {e}")
        sys.exit(2)
