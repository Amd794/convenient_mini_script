#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
文件重复查找工具

这个脚本用于查找目录中的重复文件，支持多种比较方式和重复文件处理选项。
可用于清理磁盘空间、整理备份和优化文件存储。
"""

import argparse
import hashlib
import logging
import os
import shutil
import sys
import time
from collections import defaultdict
from enum import Enum
from typing import Dict, List, Optional

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)
logger = logging.getLogger(__name__)


class CompareMethod(Enum):
    """文件比较方法枚举"""
    SIZE = "size"  # 仅比较文件大小
    HASH = "hash"  # 比较文件哈希值（默认）
    CONTENT = "content"  # 逐字节比较文件内容


class HashAlgorithm(Enum):
    """哈希算法枚举"""
    MD5 = "md5"  # MD5算法（较快，但安全性较低）
    SHA1 = "sha1"  # SHA1算法
    SHA256 = "sha256"  # SHA256算法（较慢，但安全性高）


class DuplicateAction(Enum):
    """重复文件处理操作枚举"""
    REPORT = "report"  # 仅报告重复文件（默认）
    DELETE = "delete"  # 删除重复文件（保留第一个）
    HARDLINK = "hardlink"  # 创建硬链接（仅支持同一文件系统）
    SYMLINK = "symlink"  # 创建符号链接
    MOVE = "move"  # 移动重复文件到指定目录
    INTERACTIVE = "interactive"  # 交互式处理每组重复文件


class DuplicateFinder:
    """重复文件查找器类，提供查找和处理重复文件的功能"""

    def __init__(self,
                 compare_method: CompareMethod = CompareMethod.HASH,
                 hash_algorithm: HashAlgorithm = HashAlgorithm.MD5,
                 min_size: int = 1,
                 exclude_patterns: List[str] = None,
                 include_hidden: bool = False,
                 follow_symlinks: bool = False):
        """
        初始化重复文件查找器
        
        Args:
            compare_method: 文件比较方法
            hash_algorithm: 哈希算法（当compare_method为HASH时使用）
            min_size: 最小文件大小（字节），小于此大小的文件将被忽略
            exclude_patterns: 要排除的文件模式列表
            include_hidden: 是否包括隐藏文件
            follow_symlinks: 是否跟随符号链接
        """
        self.compare_method = compare_method
        self.hash_algorithm = hash_algorithm
        self.min_size = min_size
        self.exclude_patterns = exclude_patterns or []
        self.include_hidden = include_hidden
        self.follow_symlinks = follow_symlinks

        # 查找结果
        self.size_groups = defaultdict(list)  # 按大小分组的文件
        self.duplicate_groups = []  # 重复文件组
        self.total_duplicates = 0  # 重复文件总数
        self.wasted_space = 0  # 浪费的空间（字节）

        # 统计信息
        self.stats = {
            "total_files": 0,
            "total_size": 0,
            "files_processed": 0,
            "duplicate_files": 0,
            "duplicate_groups": 0,
            "wasted_space": 0,
            "saved_space": 0,
            "errors": 0,
            "skipped_files": 0
        }

        # 缓存已计算的文件哈希值
        self._hash_cache = {}

        # 扫描开始时间
        self.start_time = 0

    def find_duplicates(self, directories: List[str], recursive: bool = True) -> List[List[str]]:
        """
        在指定目录中查找重复文件
        
        Args:
            directories: 要扫描的目录路径列表
            recursive: 是否递归扫描子目录
            
        Returns:
            重复文件组列表，每组包含路径相同的文件
        """
        self.start_time = time.time()

        # 重置统计信息
        self.stats = {
            "total_files": 0,
            "total_size": 0,
            "files_processed": 0,
            "duplicate_files": 0,
            "duplicate_groups": 0,
            "wasted_space": 0,
            "saved_space": 0,
            "errors": 0,
            "skipped_files": 0
        }

        # 清空之前的结果
        self.size_groups.clear()
        self.duplicate_groups.clear()
        self._hash_cache.clear()

        logger.info(f"开始查找重复文件...")
        logger.info(f"比较方法: {self.compare_method.value}")
        if self.compare_method == CompareMethod.HASH:
            logger.info(f"哈希算法: {self.hash_algorithm.value}")
        logger.info(f"最小文件大小: {self._format_size(self.min_size)}")

        # 第一步：扫描文件并按大小分组
        for directory in directories:
            self._scan_directory(directory, recursive)

        logger.info(f"扫描完成，共找到 {self.stats['total_files']} 个文件，"
                    f"总大小: {self._format_size(self.stats['total_size'])}")

        # 第二步：按大小筛选可能的重复文件
        potential_duplicates = {size: files for size, files in self.size_groups.items() if len(files) > 1}
        logger.info(f"找到 {len(potential_duplicates)} 组可能的重复文件（按大小分组）")

        # 第三步：进一步比较文件内容确认重复
        self._find_exact_duplicates(potential_duplicates)

        # 计算统计信息
        self.stats["duplicate_groups"] = len(self.duplicate_groups)
        self.stats["duplicate_files"] = sum(len(group) - 1 for group in self.duplicate_groups)
        self.stats["wasted_space"] = sum((len(group) - 1) * os.path.getsize(group[0])
                                         for group in self.duplicate_groups)

        # 记录查找结果
        elapsed_time = time.time() - self.start_time
        logger.info(f"查找完成，耗时: {elapsed_time:.2f} 秒")
        logger.info(f"找到 {self.stats['duplicate_groups']} 组重复文件，"
                    f"共 {self.stats['duplicate_files']} 个重复文件")
        logger.info(f"浪费的空间: {self._format_size(self.stats['wasted_space'])}")

        return self.duplicate_groups

    def process_duplicates(self, action: DuplicateAction, target_dir: Optional[str] = None) -> Dict:
        """
        处理重复文件
        
        Args:
            action: 处理操作
            target_dir: 目标目录（移动操作时使用）
            
        Returns:
            处理结果统计
        """
        if not self.duplicate_groups:
            logger.warning("没有找到重复文件，无需处理")
            return self.stats

        logger.info(f"开始处理重复文件，操作: {action.value}")

        # 处理前检查
        if action == DuplicateAction.MOVE and not target_dir:
            raise ValueError("移动操作需要指定目标目录")

        if action == DuplicateAction.MOVE and not os.path.exists(target_dir):
            os.makedirs(target_dir, exist_ok=True)
            logger.info(f"创建目标目录: {target_dir}")

        # 根据操作类型处理重复文件
        processed_files = 0
        saved_space = 0

        for group_idx, file_group in enumerate(self.duplicate_groups):
            # 保留第一个文件，处理其余文件
            original_file = file_group[0]
            duplicates = file_group[1:]

            if not duplicates:
                continue

            # 获取原始文件大小
            original_size = os.path.getsize(original_file)

            logger.info(f"处理重复组 #{group_idx + 1}: {len(duplicates)} 个副本，"
                        f"每个 {self._format_size(original_size)}")
            logger.info(f"  保留: {original_file}")

            # 根据操作类型处理重复文件
            if action == DuplicateAction.REPORT:
                # 仅报告，不做任何操作
                for idx, duplicate in enumerate(duplicates):
                    logger.info(f"  重复 #{idx + 1}: {duplicate}")

            elif action == DuplicateAction.DELETE:
                # 删除重复文件
                for duplicate in duplicates:
                    try:
                        os.remove(duplicate)
                        logger.info(f"  已删除: {duplicate}")
                        processed_files += 1
                        saved_space += original_size
                    except Exception as e:
                        logger.error(f"  删除文件 {duplicate} 时出错: {e}")
                        self.stats["errors"] += 1

            elif action == DuplicateAction.HARDLINK:
                # 创建硬链接
                for duplicate in duplicates:
                    try:
                        os.remove(duplicate)
                        os.link(original_file, duplicate)
                        logger.info(f"  已创建硬链接: {duplicate}")
                        processed_files += 1
                        saved_space += original_size
                    except Exception as e:
                        logger.error(f"  创建硬链接 {duplicate} 时出错: {e}")
                        self.stats["errors"] += 1

            elif action == DuplicateAction.SYMLINK:
                # 创建符号链接
                for duplicate in duplicates:
                    try:
                        os.remove(duplicate)
                        os.symlink(os.path.abspath(original_file), duplicate)
                        logger.info(f"  已创建符号链接: {duplicate}")
                        processed_files += 1
                        saved_space += original_size
                    except Exception as e:
                        logger.error(f"  创建符号链接 {duplicate} 时出错: {e}")
                        self.stats["errors"] += 1

            elif action == DuplicateAction.MOVE:
                # 移动到目标目录
                for duplicate in duplicates:
                    try:
                        base_name = os.path.basename(duplicate)
                        # 确保文件名不冲突
                        target_path = os.path.join(target_dir, base_name)
                        if os.path.exists(target_path):
                            name, ext = os.path.splitext(base_name)
                            target_path = os.path.join(target_dir, f"{name}_{int(time.time())}{ext}")

                        shutil.move(duplicate, target_path)
                        logger.info(f"  已移动: {duplicate} -> {target_path}")
                        processed_files += 1
                    except Exception as e:
                        logger.error(f"  移动文件 {duplicate} 时出错: {e}")
                        self.stats["errors"] += 1

            elif action == DuplicateAction.INTERACTIVE:
                # 交互式处理
                self._handle_interactive(group_idx, original_file, duplicates)

        # 更新统计信息
        self.stats["saved_space"] = saved_space

        logger.info(f"处理完成，共处理 {processed_files} 个重复文件")
        if saved_space > 0:
            logger.info(f"节省空间: {self._format_size(saved_space)}")

        return self.stats

    def generate_report(self, output_file: Optional[str] = None,
                        format_type: str = "text") -> str:
        """
        生成重复文件报告
        
        Args:
            output_file: 输出文件路径，如果为None则只返回报告内容
            format_type: 报告格式，可选值: text, csv, json
            
        Returns:
            报告内容
        """
        if not self.duplicate_groups:
            report = "未找到重复文件"
            if output_file:
                with open(output_file, 'w', encoding='utf-8') as f:
                    f.write(report)
            return report

        # 生成报告内容
        if format_type == "text":
            report = self._generate_text_report()
        elif format_type == "csv":
            report = self._generate_csv_report()
        elif format_type == "json":
            report = self._generate_json_report()
        else:
            raise ValueError(f"不支持的报告格式: {format_type}")

        # 如果指定了输出文件，则写入文件
        if output_file:
            with open(output_file, 'w', encoding='utf-8') as f:
                f.write(report)
            logger.info(f"报告已保存到: {output_file}")

        return report

    def _scan_directory(self, directory: str, recursive: bool) -> None:
        """扫描目录，收集文件信息"""
        try:
            directory = os.path.abspath(directory)

            if not os.path.exists(directory):
                logger.error(f"目录不存在: {directory}")
                return

            logger.info(f"扫描目录: {directory}")

            for root, dirs, files in os.walk(directory, followlinks=self.follow_symlinks):
                # 过滤隐藏文件和目录
                if not self.include_hidden:
                    dirs[:] = [d for d in dirs if not d.startswith('.')]
                    files = [f for f in files if not f.startswith('.')]

                # 过滤排除的文件模式
                for pattern in self.exclude_patterns:
                    import fnmatch
                    files = [f for f in files if not fnmatch.fnmatch(f, pattern)]

                # 处理文件
                for filename in files:
                    try:
                        file_path = os.path.join(root, filename)

                        # 跳过非常规文件
                        if not os.path.isfile(file_path):
                            continue

                        # 获取文件大小
                        file_size = os.path.getsize(file_path)

                        # 跳过小于最小大小的文件
                        if file_size < self.min_size:
                            self.stats["skipped_files"] += 1
                            continue

                        # 按大小分组
                        self.size_groups[file_size].append(file_path)

                        # 更新统计信息
                        self.stats["total_files"] += 1
                        self.stats["total_size"] += file_size

                    except Exception as e:
                        logger.error(f"处理文件 {os.path.join(root, filename)} 时出错: {e}")
                        self.stats["errors"] += 1

                # 如果不递归，则清空子目录列表
                if not recursive:
                    dirs.clear()

        except Exception as e:
            logger.error(f"扫描目录 {directory} 时出错: {e}")
            self.stats["errors"] += 1

    def _find_exact_duplicates(self, potential_duplicates: Dict[int, List[str]]) -> None:
        """通过比较文件内容找出精确的重复文件"""
        total_groups = len(potential_duplicates)
        processed_groups = 0

        for size, files in potential_duplicates.items():
            processed_groups += 1
            if len(files) < 2:
                continue

            logger.debug(f"处理可能的重复组 ({processed_groups}/{total_groups}): "
                         f"{len(files)} 个文件，每个 {self._format_size(size)}")

            # 根据比较方法进行精确比较
            if self.compare_method == CompareMethod.SIZE:
                # 如果仅按大小比较，则直接添加到结果中
                self.duplicate_groups.append(files)

            elif self.compare_method == CompareMethod.HASH:
                # 按哈希值比较
                hash_groups = defaultdict(list)

                for file_path in files:
                    try:
                        file_hash = self._calculate_file_hash(file_path)
                        hash_groups[file_hash].append(file_path)
                        self.stats["files_processed"] += 1
                    except Exception as e:
                        logger.error(f"计算文件 {file_path} 的哈希值时出错: {e}")
                        self.stats["errors"] += 1

                # 将哈希值相同的文件组添加到结果中
                for hash_value, file_group in hash_groups.items():
                    if len(file_group) > 1:
                        self.duplicate_groups.append(file_group)

            elif self.compare_method == CompareMethod.CONTENT:
                # 逐字节比较文件内容
                # 先按哈希值进行初步分组，再进行详细比较
                hash_groups = defaultdict(list)

                for file_path in files:
                    try:
                        file_hash = self._calculate_file_hash(file_path)
                        hash_groups[file_hash].append(file_path)
                        self.stats["files_processed"] += 1
                    except Exception as e:
                        logger.error(f"计算文件 {file_path} 的哈希值时出错: {e}")
                        self.stats["errors"] += 1

                # 对哈希值相同的文件组进行逐字节比较
                for hash_value, file_group in hash_groups.items():
                    if len(file_group) > 1:
                        content_groups = self._group_by_content(file_group)
                        for content_group in content_groups:
                            if len(content_group) > 1:
                                self.duplicate_groups.append(content_group)

    def _calculate_file_hash(self, file_path: str) -> str:
        """计算文件的哈希值"""
        # 检查缓存
        if file_path in self._hash_cache:
            return self._hash_cache[file_path]

        # 选择哈希算法
        if self.hash_algorithm == HashAlgorithm.MD5:
            hasher = hashlib.md5()
        elif self.hash_algorithm == HashAlgorithm.SHA1:
            hasher = hashlib.sha1()
        elif self.hash_algorithm == HashAlgorithm.SHA256:
            hasher = hashlib.sha256()
        else:
            raise ValueError(f"不支持的哈希算法: {self.hash_algorithm}")

        # 读取文件并计算哈希值
        buffer_size = 8192  # 8KB buffer
        with open(file_path, 'rb') as f:
            while True:
                data = f.read(buffer_size)
                if not data:
                    break
                hasher.update(data)

        # 存入缓存并返回
        hash_value = hasher.hexdigest()
        self._hash_cache[file_path] = hash_value
        return hash_value

    def _group_by_content(self, files: List[str]) -> List[List[str]]:
        """通过逐字节比较文件内容对文件进行分组"""
        if len(files) < 2:
            return [files]

        # 简单实现：两两比较文件内容
        groups = []
        remaining = set(files)

        while remaining:
            # 取一个文件作为基准
            base_file = next(iter(remaining))
            remaining.remove(base_file)

            # 找出与基准文件内容相同的文件
            same_content = [base_file]

            for file in list(remaining):
                if self._compare_file_content(base_file, file):
                    same_content.append(file)
                    remaining.remove(file)

            # 添加到结果
            groups.append(same_content)

        return groups

    def _compare_file_content(self, file1: str, file2: str) -> bool:
        """逐字节比较两个文件的内容"""
        # 先检查文件大小是否相同
        if os.path.getsize(file1) != os.path.getsize(file2):
            return False

        # 逐字节比较
        buffer_size = 8192  # 8KB buffer
        with open(file1, 'rb') as f1, open(file2, 'rb') as f2:
            while True:
                b1 = f1.read(buffer_size)
                b2 = f2.read(buffer_size)

                if b1 != b2:
                    return False

                if not b1:  # 文件结束
                    return True

    def _handle_interactive(self, group_idx: int, original: str, duplicates: List[str]) -> None:
        """交互式处理重复文件组"""
        print(f"\n重复组 #{group_idx + 1}:")
        print(f"  [0] {original} (保留)")

        for idx, duplicate in enumerate(duplicates):
            print(f"  [{idx + 1}] {duplicate}")

        actions = {
            's': "跳过此组",
            'd': "删除所有重复文件（保留原始文件）",
            'h': "将所有重复文件替换为硬链接",
            'l': "将所有重复文件替换为符号链接",
            'q': "退出交互模式"
        }

        print("\n可用操作:")
        for key, desc in actions.items():
            print(f"  {key}: {desc}")

        while True:
            choice = input("\n请选择操作 [s/d/h/l/q]: ").strip().lower()

            if choice == 's':
                print("已跳过此组")
                break
            elif choice == 'd':
                # 删除所有重复文件
                for duplicate in duplicates:
                    try:
                        os.remove(duplicate)
                        print(f"已删除: {duplicate}")
                    except Exception as e:
                        print(f"删除文件 {duplicate} 时出错: {e}")
                break
            elif choice == 'h':
                # 创建硬链接
                for duplicate in duplicates:
                    try:
                        os.remove(duplicate)
                        os.link(original, duplicate)
                        print(f"已创建硬链接: {duplicate}")
                    except Exception as e:
                        print(f"创建硬链接 {duplicate} 时出错: {e}")
                break
            elif choice == 'l':
                # 创建符号链接
                for duplicate in duplicates:
                    try:
                        os.remove(duplicate)
                        os.symlink(os.path.abspath(original), duplicate)
                        print(f"已创建符号链接: {duplicate}")
                    except Exception as e:
                        print(f"创建符号链接 {duplicate} 时出错: {e}")
                break
            elif choice == 'q':
                print("退出交互模式")
                return
            else:
                print("无效的选择，请重试")

    def _generate_text_report(self) -> str:
        """生成文本格式的报告"""
        lines = []
        lines.append("===== 重复文件报告 =====")
        lines.append("")
        lines.append(f"扫描时间: {time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(self.start_time))}")
        lines.append(f"耗时: {time.time() - self.start_time:.2f} 秒")
        lines.append(f"扫描的文件总数: {self.stats['total_files']}")
        lines.append(f"文件总大小: {self._format_size(self.stats['total_size'])}")
        lines.append(f"找到的重复组: {self.stats['duplicate_groups']}")
        lines.append(f"重复文件数: {self.stats['duplicate_files']}")
        lines.append(f"浪费的空间: {self._format_size(self.stats['wasted_space'])}")
        lines.append("")

        lines.append("=== 重复文件组详情 ===")
        for idx, group in enumerate(self.duplicate_groups):
            group_size = os.path.getsize(group[0])
            lines.append(f"\n组 #{idx + 1} - {len(group)} 个文件，每个 {self._format_size(group_size)}")

            for file_idx, file_path in enumerate(group):
                if file_idx == 0:
                    lines.append(f"  原始: {file_path}")
                else:
                    lines.append(f"  重复 #{file_idx}: {file_path}")

        return "\n".join(lines)

    def _generate_csv_report(self) -> str:
        """生成CSV格式的报告"""
        import csv
        from io import StringIO

        output = StringIO()
        writer = csv.writer(output)

        # 写入标题行
        writer.writerow(["Group", "Type", "Size", "Path"])

        # 写入数据行
        for group_idx, group in enumerate(self.duplicate_groups):
            group_size = os.path.getsize(group[0])

            for file_idx, file_path in enumerate(group):
                file_type = "Original" if file_idx == 0 else "Duplicate"
                writer.writerow([group_idx + 1, file_type, group_size, file_path])

        return output.getvalue()

    def _generate_json_report(self) -> str:
        """生成JSON格式的报告"""
        import json

        report = {
            "scan_time": time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(self.start_time)),
            "elapsed_time": time.time() - self.start_time,
            "stats": self.stats,
            "duplicate_groups": []
        }

        for group_idx, group in enumerate(self.duplicate_groups):
            group_size = os.path.getsize(group[0])
            group_data = {
                "group_id": group_idx + 1,
                "file_count": len(group),
                "file_size": group_size,
                "files": []
            }

            for file_idx, file_path in enumerate(group):
                file_type = "original" if file_idx == 0 else "duplicate"
                group_data["files"].append({
                    "path": file_path,
                    "type": file_type
                })

            report["duplicate_groups"].append(group_data)

        return json.dumps(report, indent=2)

    def _format_size(self, size_bytes: int) -> str:
        """将字节大小格式化为易读的字符串"""
        for unit in ['B', 'KB', 'MB', 'GB', 'TB']:
            if size_bytes < 1024.0 or unit == 'TB':
                return f"{size_bytes:.2f} {unit}"
            size_bytes /= 1024.0


def parse_arguments():
    """解析命令行参数"""
    parser = argparse.ArgumentParser(description="文件重复查找工具")

    # 基本参数
    parser.add_argument('directories', nargs='+',
                        help='要扫描的目录路径列表')
    parser.add_argument('-r', '--recursive', action='store_true', default=True,
                        help='递归扫描子目录（默认启用）')
    parser.add_argument('--no-recursive', action='store_false', dest='recursive',
                        help='不递归扫描子目录')

    # 比较选项
    compare_group = parser.add_argument_group('比较选项')
    compare_group.add_argument('-m', '--method', choices=['size', 'hash', 'content'],
                               default='hash', help='文件比较方法（默认: hash）')
    compare_group.add_argument('-a', '--algorithm', choices=['md5', 'sha1', 'sha256'],
                               default='md5', help='哈希算法（默认: md5）')
    compare_group.add_argument('--min-size', type=str, default='1B',
                               help='最小文件大小，如 1KB、2MB（默认: 1B）')

    # 过滤选项
    filter_group = parser.add_argument_group('过滤选项')
    filter_group.add_argument('-e', '--exclude', nargs='+',
                              help='要排除的文件模式列表（如 *.tmp *.log）')
    filter_group.add_argument('--include-hidden', action='store_true',
                              help='包括隐藏文件')
    filter_group.add_argument('--follow-symlinks', action='store_true',
                              help='跟随符号链接')

    # 处理选项
    action_group = parser.add_argument_group('处理选项')
    action_group.add_argument('-p', '--process', choices=['report', 'delete', 'hardlink',
                                                          'symlink', 'move', 'interactive'],
                              default='report', help='重复文件处理操作（默认: report）')
    action_group.add_argument('-t', '--target-dir',
                              help='移动重复文件的目标目录（用于move操作）')

    # 输出选项
    output_group = parser.add_argument_group('输出选项')
    output_group.add_argument('-o', '--output',
                              help='报告输出文件路径')
    output_group.add_argument('-f', '--format', choices=['text', 'csv', 'json'],
                              default='text', help='报告格式（默认: text）')
    output_group.add_argument('-q', '--quiet', action='store_true',
                              help='静默模式，减少输出')
    output_group.add_argument('-v', '--verbose', action='store_true',
                              help='详细模式，显示更多信息')

    return parser.parse_args()


def parse_size(size_str: str) -> int:
    """解析大小字符串为字节数"""
    size_str = size_str.strip().upper()

    # 如果只有数字，直接返回
    if size_str.isdigit():
        return int(size_str)

    # 解析单位
    units = {
        'B': 1,
        'KB': 1024,
        'MB': 1024 * 1024,
        'GB': 1024 * 1024 * 1024,
        'TB': 1024 * 1024 * 1024 * 1024
    }

    # 匹配数字和单位
    import re
    match = re.match(r'^(\d+(?:\.\d+)?)\s*([KMGT]?B?)$', size_str)

    if not match:
        raise ValueError(f"无效的大小格式: {size_str}")

    value, unit = match.groups()
    value = float(value)
    unit = unit.upper() if unit else 'B'

    # 处理简写单位
    if unit == 'K':
        unit = 'KB'
    elif unit == 'M':
        unit = 'MB'
    elif unit == 'G':
        unit = 'GB'
    elif unit == 'T':
        unit = 'TB'

    if unit not in units:
        raise ValueError(f"无效的大小单位: {unit}")

    return int(value * units[unit])


def main():
    """主函数"""
    args = parse_arguments()

    # 配置日志级别
    if args.quiet:
        logging.getLogger().setLevel(logging.WARNING)
    elif args.verbose:
        logging.getLogger().setLevel(logging.DEBUG)

    try:
        # 解析最小文件大小
        min_size = parse_size(args.min_size)

        # 创建重复文件查找器
        finder = DuplicateFinder(
            compare_method=CompareMethod(args.method),
            hash_algorithm=HashAlgorithm(args.algorithm),
            min_size=min_size,
            exclude_patterns=args.exclude or [],
            include_hidden=args.include_hidden,
            follow_symlinks=args.follow_symlinks
        )

        # 查找重复文件
        finder.find_duplicates(args.directories, args.recursive)

        # 处理重复文件
        finder.process_duplicates(
            action=DuplicateAction(args.process),
            target_dir=args.target_dir
        )

        # 生成报告
        if args.output:
            finder.generate_report(args.output, args.format)
        else:
            print(finder.generate_report(format_type=args.format))

        return 0

    except Exception as e:
        logger.error(f"程序出错: {e}")
        if args.verbose:
            import traceback
            traceback.print_exc()
        return 1


if __name__ == "__main__":
    sys.exit(main())
