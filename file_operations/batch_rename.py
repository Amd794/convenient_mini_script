#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
批量文件重命名工具

这个脚本提供了多种方式来批量重命名文件，支持添加前缀/后缀、
序列号、日期时间、正则表达式替换等操作，还具有预览和撤销功能。
"""

import argparse
import datetime
import json
import logging
import os
import re
import shutil
import sys
import time
from typing import List, Dict, Optional, Any

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)
logger = logging.getLogger(__name__)

# 全局变量
HISTORY_FILE = os.path.expanduser("~/.batch_rename_history.json")
MAX_HISTORY_ENTRIES = 10


class RenameOperation:
    """重命名操作类，表示单个文件的重命名操作"""

    def __init__(self, original_path: str, new_path: str):
        """
        初始化重命名操作
        
        Args:
            original_path: 原始文件路径
            new_path: 新文件路径
        """
        self.original_path = original_path
        self.new_path = new_path
        self.success = None  # 用于记录操作是否成功
        self.error = None  # 用于记录错误信息

    def __str__(self) -> str:
        """返回操作的字符串表示"""
        orig_name = os.path.basename(self.original_path)
        new_name = os.path.basename(self.new_path)
        return f"'{orig_name}' -> '{new_name}'"


class BatchRenamer:
    """批量重命名器，包含各种重命名方法和操作"""

    def __init__(self, directory: str, recursive: bool = False):
        """
        初始化批量重命名器
        
        Args:
            directory: 要处理的目录
            recursive: 是否递归处理子目录
        """
        self.directory = os.path.abspath(directory)
        self.recursive = recursive
        self.operations: List[RenameOperation] = []
        self.history: List[Dict[str, Any]] = []
        self.load_history()

    def load_history(self) -> None:
        """加载历史重命名记录"""
        if os.path.exists(HISTORY_FILE):
            try:
                with open(HISTORY_FILE, 'r', encoding='utf-8') as f:
                    self.history = json.load(f)
            except Exception as e:
                logger.error(f"加载历史记录失败: {e}")
                self.history = []

    def save_history(self) -> None:
        """保存历史重命名记录"""
        # 确保历史记录目录存在
        history_dir = os.path.dirname(HISTORY_FILE)
        os.makedirs(history_dir, exist_ok=True)

        try:
            # 如果历史记录过多，保留最近的几条
            while len(self.history) > MAX_HISTORY_ENTRIES:
                self.history.pop(0)

            with open(HISTORY_FILE, 'w', encoding='utf-8') as f:
                json.dump(self.history, f, ensure_ascii=False, indent=2)
        except Exception as e:
            logger.error(f"保存历史记录失败: {e}")

    def collect_files(self,
                      extensions: Optional[List[str]] = None,
                      min_size: Optional[int] = None,
                      max_size: Optional[int] = None,
                      exclude_pattern: Optional[str] = None) -> List[str]:
        """
        收集满足条件的文件
        
        Args:
            extensions: 文件扩展名列表，如 ['.jpg', '.png']
            min_size: 最小文件大小（字节）
            max_size: 最大文件大小（字节）
            exclude_pattern: 排除的文件名模式（正则表达式）
            
        Returns:
            符合条件的文件路径列表
        """
        files = []
        exclude_regex = re.compile(exclude_pattern) if exclude_pattern else None

        # 递归遍历目录
        for root, _, filenames in os.walk(self.directory):
            # 如果不是递归模式且不是指定目录，则跳过
            if not self.recursive and root != self.directory:
                continue

            for filename in filenames:
                # 检查是否排除
                if exclude_regex and exclude_regex.search(filename):
                    continue

                # 完整文件路径
                file_path = os.path.join(root, filename)

                # 检查扩展名
                if extensions:
                    _, ext = os.path.splitext(filename)
                    if ext.lower() not in [e.lower() for e in extensions]:
                        continue

                # 检查文件大小
                if min_size or max_size:
                    file_size = os.path.getsize(file_path)
                    if min_size and file_size < min_size:
                        continue
                    if max_size and file_size > max_size:
                        continue

                files.append(file_path)

        return files

    def add_prefix(self, prefix: str, files: Optional[List[str]] = None) -> List[RenameOperation]:
        """
        添加前缀
        
        Args:
            prefix: 要添加的前缀
            files: 要处理的文件列表，如不提供则使用默认收集的文件
            
        Returns:
            重命名操作列表
        """
        operations = []
        if files is None:
            files = self.collect_files()

        for file_path in files:
            directory = os.path.dirname(file_path)
            filename = os.path.basename(file_path)
            new_filename = f"{prefix}{filename}"
            new_path = os.path.join(directory, new_filename)
            operations.append(RenameOperation(file_path, new_path))

        self.operations = operations
        return operations

    def add_suffix(self, suffix: str, before_extension: bool = True, files: Optional[List[str]] = None) -> List[
        RenameOperation]:
        """
        添加后缀
        
        Args:
            suffix: 要添加的后缀
            before_extension: 是否在扩展名之前添加后缀
            files: 要处理的文件列表，如不提供则使用默认收集的文件
            
        Returns:
            重命名操作列表
        """
        operations = []
        if files is None:
            files = self.collect_files()

        for file_path in files:
            directory = os.path.dirname(file_path)
            filename = os.path.basename(file_path)

            if before_extension:
                name, ext = os.path.splitext(filename)
                new_filename = f"{name}{suffix}{ext}"
            else:
                new_filename = f"{filename}{suffix}"

            new_path = os.path.join(directory, new_filename)
            operations.append(RenameOperation(file_path, new_path))

        self.operations = operations
        return operations

    def add_sequence_number(self,
                            start_num: int = 1,
                            padding: int = 3,
                            separator: str = "_",
                            position: str = "prefix",
                            files: Optional[List[str]] = None) -> List[RenameOperation]:
        """
        添加序列号
        
        Args:
            start_num: 起始编号
            padding: 数字位数（补零）
            separator: 分隔符
            position: 序号位置，"prefix"在文件名前，"suffix"在文件名后（扩展名前）
            files: 要处理的文件列表，如不提供则使用默认收集的文件
            
        Returns:
            重命名操作列表
        """
        operations = []
        if files is None:
            files = self.collect_files()

        # 对文件排序以确保序列号是可预测的
        files.sort()

        for i, file_path in enumerate(files):
            directory = os.path.dirname(file_path)
            filename = os.path.basename(file_path)
            name, ext = os.path.splitext(filename)
            sequence = f"{start_num + i:0{padding}d}"

            if position.lower() == "prefix":
                new_filename = f"{sequence}{separator}{name}{ext}"
            else:  # suffix
                new_filename = f"{name}{separator}{sequence}{ext}"

            new_path = os.path.join(directory, new_filename)
            operations.append(RenameOperation(file_path, new_path))

        self.operations = operations
        return operations

    def add_date_time(self,
                      format_str: str = "%Y%m%d_%H%M%S",
                      use_file_time: bool = True,
                      separator: str = "_",
                      position: str = "prefix",
                      files: Optional[List[str]] = None) -> List[RenameOperation]:
        """
        添加日期时间
        
        Args:
            format_str: 日期时间格式
            use_file_time: 使用文件修改时间，否则使用当前时间
            separator: 分隔符
            position: 位置，"prefix"在文件名前，"suffix"在文件名后（扩展名前）
            files: 要处理的文件列表，如不提供则使用默认收集的文件
            
        Returns:
            重命名操作列表
        """
        operations = []
        if files is None:
            files = self.collect_files()

        current_time = datetime.datetime.now()

        for file_path in files:
            directory = os.path.dirname(file_path)
            filename = os.path.basename(file_path)
            name, ext = os.path.splitext(filename)

            if use_file_time:
                mtime = os.path.getmtime(file_path)
                file_datetime = datetime.datetime.fromtimestamp(mtime)
                date_str = file_datetime.strftime(format_str)
            else:
                date_str = current_time.strftime(format_str)

            if position.lower() == "prefix":
                new_filename = f"{date_str}{separator}{name}{ext}"
            else:  # suffix
                new_filename = f"{name}{separator}{date_str}{ext}"

            new_path = os.path.join(directory, new_filename)
            operations.append(RenameOperation(file_path, new_path))

        self.operations = operations
        return operations

    def replace_pattern(self,
                        pattern: str,
                        replacement: str,
                        files: Optional[List[str]] = None) -> List[RenameOperation]:
        """
        使用正则表达式替换文件名中的内容
        
        Args:
            pattern: 正则表达式模式
            replacement: 替换内容
            files: 要处理的文件列表，如不提供则使用默认收集的文件
            
        Returns:
            重命名操作列表
        """
        operations = []
        if files is None:
            files = self.collect_files()

        regex = re.compile(pattern)

        for file_path in files:
            directory = os.path.dirname(file_path)
            filename = os.path.basename(file_path)

            # 应用替换
            new_filename = regex.sub(replacement, filename)

            # 如果没有变化，跳过
            if new_filename == filename:
                continue

            new_path = os.path.join(directory, new_filename)
            operations.append(RenameOperation(file_path, new_path))

        self.operations = operations
        return operations

    def change_case(self,
                    case: str,
                    files: Optional[List[str]] = None) -> List[RenameOperation]:
        """
        更改文件名大小写
        
        Args:
            case: 大小写类型，可选值: "upper", "lower", "title", "capitalize"
            files: 要处理的文件列表，如不提供则使用默认收集的文件
            
        Returns:
            重命名操作列表
        """
        operations = []
        if files is None:
            files = self.collect_files()

        for file_path in files:
            directory = os.path.dirname(file_path)
            filename = os.path.basename(file_path)
            name, ext = os.path.splitext(filename)

            if case.lower() == "upper":
                new_name = name.upper()
            elif case.lower() == "lower":
                new_name = name.lower()
            elif case.lower() == "title":
                new_name = name.title()
            elif case.lower() == "capitalize":
                new_name = name.capitalize()
            else:
                new_name = name

            new_filename = f"{new_name}{ext}"

            # 如果没有变化，跳过
            if new_filename == filename:
                continue

            new_path = os.path.join(directory, new_filename)
            operations.append(RenameOperation(file_path, new_path))

        self.operations = operations
        return operations

    def replace_spaces(self,
                       replacement: str = "_",
                       files: Optional[List[str]] = None) -> List[RenameOperation]:
        """
        替换文件名中的空格
        
        Args:
            replacement: 替换字符
            files: 要处理的文件列表，如不提供则使用默认收集的文件
            
        Returns:
            重命名操作列表
        """
        return self.replace_pattern(r'\s+', replacement, files)

    def preview(self) -> None:
        """预览重命名操作"""
        if not self.operations:
            print("没有重命名操作")
            return

        print(f"\n预览重命名操作 ({len(self.operations)} 个文件):")
        print("-" * 60)

        for i, op in enumerate(self.operations, 1):
            print(f"{i}. {op}")

        print("-" * 60)

        # 检查冲突
        self._check_conflicts()

    def _check_conflicts(self) -> bool:
        """
        检查重命名操作中的冲突
        
        Returns:
            是否存在冲突
        """
        new_paths = {}
        has_conflicts = False

        for op in self.operations:
            if op.new_path in new_paths:
                print(
                    f"警告: 冲突! '{os.path.basename(op.original_path)}' 和 '{os.path.basename(new_paths[op.new_path])}' 将重命名为相同的名称 '{os.path.basename(op.new_path)}'")
                has_conflicts = True
            new_paths[op.new_path] = op.original_path

            # 检查是否与现有文件冲突（不是当前要重命名的文件）
            if os.path.exists(op.new_path) and op.new_path != op.original_path:
                print(f"警告: '{os.path.basename(op.new_path)}' 已存在，将被覆盖!")
                has_conflicts = True

        return has_conflicts

    def execute(self, dry_run: bool = False) -> bool:
        """
        执行重命名操作
        
        Args:
            dry_run: 如果为True，则只模拟执行但不实际重命名
            
        Returns:
            是否全部成功
        """
        if not self.operations:
            print("没有重命名操作")
            return True

        if dry_run:
            print("\n模拟执行重命名操作:")
        else:
            print("\n执行重命名操作:")

        # 检查冲突
        if self._check_conflicts():
            user_input = input("\n检测到冲突，是否继续执行? (y/N): ")
            if user_input.lower() not in ('y', 'yes'):
                print("操作已取消")
                return False

        success_count = 0
        fail_count = 0

        # 记录此批次操作，用于后续可能的撤销
        timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        batch_id = int(time.time())
        history_entry = {
            "id": batch_id,
            "timestamp": timestamp,
            "directory": self.directory,
            "operations": []
        }

        for op in self.operations:
            # 确保目标目录存在
            target_dir = os.path.dirname(op.new_path)
            os.makedirs(target_dir, exist_ok=True)

            try:
                if not dry_run:
                    # 如果新路径已存在且不是当前文件，先备份
                    if os.path.exists(op.new_path) and op.original_path != op.new_path:
                        backup_path = f"{op.new_path}.bak.{batch_id}"
                        shutil.move(op.new_path, backup_path)
                        print(f"  已备份: '{os.path.basename(op.new_path)}' -> '{os.path.basename(backup_path)}'")

                    # 执行重命名
                    shutil.move(op.original_path, op.new_path)

                print(f"  成功: {op}")
                op.success = True
                success_count += 1

                # 添加到历史记录
                history_entry["operations"].append({
                    "original": op.original_path,
                    "new": op.new_path
                })

            except Exception as e:
                print(f"  失败: {op} - {str(e)}")
                op.success = False
                op.error = str(e)
                fail_count += 1

        # 保存历史记录（如果不是dry_run）
        if not dry_run and success_count > 0:
            self.history.append(history_entry)
            self.save_history()

        print(f"\n重命名完成: {success_count} 成功, {fail_count} 失败")
        return fail_count == 0

    def list_history(self) -> None:
        """列出历史重命名记录"""
        if not self.history:
            print("没有历史重命名记录")
            return

        print("\n历史重命名记录:")
        print("-" * 60)

        for i, entry in enumerate(self.history, 1):
            op_count = len(entry.get("operations", []))
            print(f"{i}. [{entry['timestamp']}] {op_count} 个文件 - {entry['directory']}")

        print("-" * 60)

    def undo_operation(self, history_index: int) -> bool:
        """
        撤销指定的重命名操作
        
        Args:
            history_index: 历史记录索引（从1开始）
            
        Returns:
            是否成功撤销
        """
        if not self.history:
            print("没有历史重命名记录")
            return False

        # 调整为从0开始的索引
        idx = history_index - 1

        if idx < 0 or idx >= len(self.history):
            print(f"无效的历史记录索引: {history_index}")
            return False

        entry = self.history[idx]
        operations = entry.get("operations", [])

        if not operations:
            print("没有可撤销的操作")
            return False

        print(f"\n撤销重命名操作 [{entry['timestamp']}]:")
        print("-" * 60)

        # 按相反顺序执行撤销操作（避免潜在冲突）
        success_count = 0
        fail_count = 0

        for op in reversed(operations):
            original_path = op["original"]
            new_path = op["new"]

            try:
                # 确保原目录存在
                original_dir = os.path.dirname(original_path)
                os.makedirs(original_dir, exist_ok=True)

                # 撤销重命名
                if os.path.exists(new_path):
                    shutil.move(new_path, original_path)
                    print(f"  成功: '{os.path.basename(new_path)}' -> '{os.path.basename(original_path)}'")
                    success_count += 1
                else:
                    print(f"  跳过: 文件不存在 '{os.path.basename(new_path)}'")
                    fail_count += 1
            except Exception as e:
                print(f"  失败: '{os.path.basename(new_path)}' -> '{os.path.basename(original_path)}' - {str(e)}")
                fail_count += 1

        # 从历史记录中移除
        if success_count > 0:
            del self.history[idx]
            self.save_history()

        print("-" * 60)
        print(f"撤销完成: {success_count} 成功, {fail_count} 失败")

        return fail_count == 0


def parse_arguments():
    """解析命令行参数"""
    parser = argparse.ArgumentParser(description="批量文件重命名工具")

    # 基本参数
    parser.add_argument("directory", nargs="?", default=".",
                        help="要处理的目录路径，默认为当前目录")
    parser.add_argument("-r", "--recursive", action="store_true",
                        help="递归处理子目录")
    parser.add_argument("--dry-run", action="store_true",
                        help="模拟运行，不实际重命名文件")

    # 文件筛选参数
    filter_group = parser.add_argument_group("文件筛选选项")
    filter_group.add_argument("-e", "--extensions", nargs="+",
                              help="要处理的文件扩展名列表，如 '.jpg .png'")
    filter_group.add_argument("--min-size", type=int,
                              help="最小文件大小（字节）")
    filter_group.add_argument("--max-size", type=int,
                              help="最大文件大小（字节）")
    filter_group.add_argument("--exclude",
                              help="排除的文件名模式（正则表达式）")

    # 重命名操作参数
    operation_group = parser.add_argument_group("重命名操作（仅选择一种）")

    # 添加各种重命名操作的互斥参数组
    rename_ops = operation_group.add_mutually_exclusive_group()

    rename_ops.add_argument("--add-prefix", metavar="PREFIX",
                            help="添加前缀")

    rename_ops.add_argument("--add-suffix", metavar="SUFFIX",
                            help="添加后缀")
    parser.add_argument("--before-ext", action="store_true",
                        help="在扩展名前添加后缀，与--add-suffix一起使用")

    rename_ops.add_argument("--add-sequence", action="store_true",
                            help="添加序列号")
    parser.add_argument("--start-num", type=int, default=1,
                        help="序列号起始值")
    parser.add_argument("--padding", type=int, default=3,
                        help="序列号位数（补零）")
    parser.add_argument("--seq-position", choices=["prefix", "suffix"], default="prefix",
                        help="序列号位置，前缀或后缀")

    rename_ops.add_argument("--add-date", action="store_true",
                            help="添加日期时间")
    parser.add_argument("--date-format", default="%Y%m%d_%H%M%S",
                        help="日期时间格式")
    parser.add_argument("--use-file-time", action="store_true",
                        help="使用文件修改时间（否则使用当前时间）")
    parser.add_argument("--date-position", choices=["prefix", "suffix"], default="prefix",
                        help="日期位置，前缀或后缀")

    rename_ops.add_argument("--replace", nargs=2, metavar=("PATTERN", "REPLACEMENT"),
                            help="替换文件名中的内容（使用正则表达式）")

    rename_ops.add_argument("--change-case", choices=["upper", "lower", "title", "capitalize"],
                            help="更改文件名大小写")

    rename_ops.add_argument("--replace-spaces", metavar="CHAR", nargs="?", const="_",
                            help="替换文件名中的空格（默认替换为下划线）")

    # 历史记录和撤销操作
    history_group = parser.add_argument_group("历史记录和撤销")
    rename_ops.add_argument("--list-history", action="store_true",
                            help="显示历史重命名记录")
    rename_ops.add_argument("--undo", type=int, metavar="ID",
                            help="撤销指定的重命名操作（使用--list-history查看可用ID）")

    return parser.parse_args()


def main():
    """主函数"""
    args = parse_arguments()

    # 确保目录存在
    if not os.path.isdir(args.directory):
        print(f"错误: 目录不存在: {args.directory}")
        return 1

    # 创建重命名器
    renamer = BatchRenamer(args.directory, args.recursive)

    # 准备文件过滤器参数
    extensions = args.extensions
    if extensions:
        # 确保扩展名带点号
        extensions = [ext if ext.startswith(".") else f".{ext}" for ext in extensions]

    # 处理历史记录操作
    if args.list_history:
        renamer.list_history()
        return 0

    if args.undo is not None:
        success = renamer.undo_operation(args.undo)
        return 0 if success else 1

    # 收集文件
    files = renamer.collect_files(
        extensions=extensions,
        min_size=args.min_size,
        max_size=args.max_size,
        exclude_pattern=args.exclude
    )

    if not files:
        print(f"在目录 '{args.directory}' 中没有找到符合条件的文件")
        return 0

    # 根据指定的操作类型执行重命名操作
    if args.add_prefix:
        renamer.add_prefix(args.add_prefix, files)

    elif args.add_suffix:
        renamer.add_suffix(args.add_suffix, args.before_ext, files)

    elif args.add_sequence:
        renamer.add_sequence_number(
            start_num=args.start_num,
            padding=args.padding,
            position=args.seq_position,
            files=files
        )

    elif args.add_date:
        renamer.add_date_time(
            format_str=args.date_format,
            use_file_time=args.use_file_time,
            position=args.date_position,
            files=files
        )

    elif args.replace:
        pattern, replacement = args.replace
        renamer.replace_pattern(pattern, replacement, files)

    elif args.change_case:
        renamer.change_case(args.change_case, files)

    elif args.replace_spaces is not None:
        renamer.replace_spaces(args.replace_spaces, files)

    else:
        # 如果没有选择任何操作，显示帮助
        print("没有选择任何重命名操作。使用 -h 或 --help 获取帮助。")
        return 1

    # 预览重命名操作
    renamer.preview()

    # 询问用户是否继续
    if not args.dry_run:
        user_input = input("\n是否继续执行重命名操作? (y/N): ")
        if user_input.lower() not in ('y', 'yes'):
            print("操作已取消")
            return 0

    # 执行重命名操作
    success = renamer.execute(args.dry_run)
    return 0 if success else 1


if __name__ == "__main__":
    sys.exit(main())
