#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
文件同步工具

这个脚本提供了目录同步功能，可以在两个目录之间保持文件内容的一致性。
支持多种同步模式、文件过滤、冲突处理和详细的同步报告。
适用于备份数据、工作文件同步和项目协作等场景。
"""

import argparse
import datetime
import hashlib
import json
import logging
import os
import shutil
import sys
import time
from enum import Enum
from typing import Dict, List, Optional, Tuple

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)
logger = logging.getLogger(__name__)


class SyncMode(Enum):
    """同步模式枚举"""
    ONE_WAY = "one-way"  # 单向同步（源->目标）
    TWO_WAY = "two-way"  # 双向同步（保留两边最新的文件）
    MIRROR = "mirror"  # 镜像同步（目标完全匹配源）
    UPDATE = "update"  # 更新模式（仅更新目标中已存在的文件）


class ConflictResolution(Enum):
    """冲突解决策略枚举"""
    NEWER = "newer"  # 保留较新的文件
    LARGER = "larger"  # 保留较大的文件
    SOURCE = "source"  # 始终使用源文件
    TARGET = "target"  # 始终使用目标文件
    SKIP = "skip"  # 跳过冲突文件
    PROMPT = "prompt"  # 提示用户选择


class FileAction(Enum):
    """文件操作枚举"""
    COPY = "copy"  # 复制文件
    DELETE = "delete"  # 删除文件
    SKIP = "skip"  # 跳过文件


class FileInfo:
    """文件信息类，存储文件的元数据"""

    def __init__(self, path: str):
        """
        初始化文件信息
        
        Args:
            path: 文件路径
        """
        self.path = path
        self.exists = os.path.exists(path)

        if self.exists:
            stat = os.stat(path)
            self.size = stat.st_size
            self.mtime = stat.st_mtime
            self.is_dir = os.path.isdir(path)
            self.is_file = os.path.isfile(path)
        else:
            self.size = 0
            self.mtime = 0
            self.is_dir = False
            self.is_file = False

    def get_hash(self) -> str:
        """
        计算文件的MD5哈希值
        
        Returns:
            文件的MD5哈希值，如果是目录或文件不存在则返回空字符串
        """
        if not self.is_file or not self.exists:
            return ""

        hasher = hashlib.md5()
        with open(self.path, 'rb') as f:
            for chunk in iter(lambda: f.read(65536), b''):
                hasher.update(chunk)
        return hasher.hexdigest()

    def __str__(self) -> str:
        """返回文件信息的字符串表示"""
        if not self.exists:
            return f"{self.path} (不存在)"

        file_type = "目录" if self.is_dir else "文件"
        size_str = f"{self.size} 字节" if self.is_file else ""
        time_str = datetime.datetime.fromtimestamp(self.mtime).strftime('%Y-%m-%d %H:%M:%S')

        return f"{self.path} ({file_type}, {size_str}, 修改时间: {time_str})"


class SyncPair:
    """同步文件对，表示源和目标中对应的文件"""

    def __init__(self,
                 source_path: str,
                 target_path: str,
                 rel_path: str):
        """
        初始化同步文件对
        
        Args:
            source_path: 源文件路径
            target_path: 目标文件路径
            rel_path: 相对于同步根目录的路径
        """
        self.source = FileInfo(source_path)
        self.target = FileInfo(target_path)
        self.rel_path = rel_path
        self.action = FileAction.SKIP
        self.reason = ""
        self.conflict = False

    def is_identical(self) -> bool:
        """
        检查源文件和目标文件是否相同
        
        Returns:
            如果文件内容相同则返回True
        """
        # 首先检查两个文件是否都存在
        if not self.source.exists or not self.target.exists:
            return False

        # 如果两者都是目录，认为它们相同（内容会在子文件中比较）
        if self.source.is_dir and self.target.is_dir:
            return True

        # 如果一个是文件一个是目录，它们肯定不同
        if self.source.is_dir != self.target.is_dir:
            return False

        # 检查文件大小，如果不同则文件内容一定不同
        if self.source.size != self.target.size:
            return False

        # 如果修改时间和大小都相同，可能相同（快速检查）
        if abs(self.source.mtime - self.target.mtime) < 0.1 and self.source.size == self.target.size:
            return True

        # 计算哈希值进行精确比较
        return self.source.get_hash() == self.target.get_hash()

    def need_sync(self, mode: SyncMode) -> bool:
        """
        根据同步模式判断是否需要同步
        
        Args:
            mode: 同步模式
            
        Returns:
            如果需要同步则返回True
        """
        # 如果两个文件相同，不需要同步
        if self.is_identical():
            return False

        # 镜像模式：源目录的文件结构会完全复制到目标目录
        if mode == SyncMode.MIRROR:
            return True

        # 单向同步：只从源复制到目标
        if mode == SyncMode.ONE_WAY:
            # 如果源文件存在而目标不存在，或源文件较新，则需要同步
            return self.source.exists and (not self.target.exists or self.source.mtime > self.target.mtime)

        # 更新模式：只更新目标中已存在的文件
        if mode == SyncMode.UPDATE:
            # 如果两者都存在且源文件较新，则需要同步
            return self.source.exists and self.target.exists and self.source.mtime > self.target.mtime

        # 双向同步：两边都进行同步，保留最新的文件
        if mode == SyncMode.TWO_WAY:
            # 如果一方不存在而另一方存在，需要同步
            if self.source.exists and not self.target.exists:
                return True
            if not self.source.exists and self.target.exists:
                return True
            # 如果两者都存在，且修改时间不同，需要同步
            if self.source.exists and self.target.exists and abs(self.source.mtime - self.target.mtime) > 0.1:
                return True

        return False

    def resolve_conflict(self, resolution: ConflictResolution) -> Tuple[FileAction, str]:
        """
        解决文件冲突
        
        Args:
            resolution: 冲突解决策略
            
        Returns:
            文件操作和原因
        """
        # 如果没有冲突，不需要解决
        if not self.conflict:
            return FileAction.SKIP, "无冲突"

        # 根据冲突解决策略决定操作
        if resolution == ConflictResolution.NEWER:
            if self.source.mtime > self.target.mtime:
                return FileAction.COPY, "源文件较新"
            else:
                return FileAction.SKIP, "目标文件较新"

        elif resolution == ConflictResolution.LARGER:
            if self.source.size > self.target.size:
                return FileAction.COPY, "源文件较大"
            else:
                return FileAction.SKIP, "目标文件较大"

        elif resolution == ConflictResolution.SOURCE:
            return FileAction.COPY, "始终使用源文件"

        elif resolution == ConflictResolution.TARGET:
            return FileAction.SKIP, "始终使用目标文件"

        elif resolution == ConflictResolution.SKIP:
            return FileAction.SKIP, "跳过冲突文件"

        elif resolution == ConflictResolution.PROMPT:
            # 提示用户选择，需要在调用处实现
            return FileAction.SKIP, "需要用户决定"

        return FileAction.SKIP, "未知的冲突解决策略"


class DirectorySynchronizer:
    """
    目录同步器类
    
    提供两个目录之间的同步功能
    """

    def __init__(self,
                 source_dir: str,
                 target_dir: str,
                 mode: SyncMode = SyncMode.ONE_WAY,
                 conflict_resolution: ConflictResolution = ConflictResolution.NEWER,
                 exclude_patterns: List[str] = None,
                 include_hidden: bool = False,
                 follow_symlinks: bool = False,
                 dry_run: bool = False,
                 delete_orphaned: bool = False,
                 preserve_metadata: bool = True):
        """
        初始化同步器
        
        Args:
            source_dir: 源目录路径
            target_dir: 目标目录路径
            mode: 同步模式
            conflict_resolution: 冲突解决策略
            exclude_patterns: 要排除的文件模式列表
            include_hidden: 是否包括隐藏文件
            follow_symlinks: 是否跟随符号链接
            dry_run: 是否只模拟运行而不实际修改文件
            delete_orphaned: 是否删除目标中孤立的文件（源中不存在）
            preserve_metadata: 是否保留文件元数据（修改时间等）
        """
        self.source_dir = os.path.abspath(source_dir)
        self.target_dir = os.path.abspath(target_dir)
        self.mode = mode
        self.conflict_resolution = conflict_resolution
        self.exclude_patterns = exclude_patterns or []
        self.include_hidden = include_hidden
        self.follow_symlinks = follow_symlinks
        self.dry_run = dry_run
        self.delete_orphaned = delete_orphaned
        self.preserve_metadata = preserve_metadata

        # 检查目录是否存在
        if not os.path.exists(self.source_dir):
            raise ValueError(f"源目录不存在: {self.source_dir}")

        if not os.path.exists(self.target_dir) and not self.dry_run:
            os.makedirs(self.target_dir, exist_ok=True)

        # 同步结果统计
        self.stats = {
            "files_scanned": 0,
            "files_copied": 0,
            "files_updated": 0,
            "files_deleted": 0,
            "files_skipped": 0,
            "dirs_created": 0,
            "conflicts_resolved": 0,
            "errors": 0,
            "total_bytes_copied": 0
        }

        # 同步计划（存储需要执行的操作）
        self.sync_plan = []

        # 当前正在处理的文件
        self.current_file = ""

        # 同步开始时间
        self.start_time = time.time()

    def synchronize(self) -> Dict:
        """
        执行同步操作
        
        Returns:
            同步结果统计
        """
        try:
            # 重置统计信息
            self.stats = {
                "files_scanned": 0,
                "files_copied": 0,
                "files_updated": 0,
                "files_deleted": 0,
                "files_skipped": 0,
                "dirs_created": 0,
                "conflicts_resolved": 0,
                "errors": 0,
                "total_bytes_copied": 0
            }

            # 记录开始时间
            self.start_time = time.time()

            # 创建同步计划
            logger.info("正在分析目录差异...")
            self._create_sync_plan()

            # 执行同步计划
            logger.info("开始执行同步操作...")
            self._execute_sync_plan()

            # 计算总时间
            total_time = time.time() - self.start_time
            self.stats["total_time"] = total_time

            # 记录完成信息
            logger.info(f"同步完成，耗时 {total_time:.2f} 秒")
            logger.info(f"扫描的文件: {self.stats['files_scanned']}")
            logger.info(f"复制的文件: {self.stats['files_copied']}")
            logger.info(f"更新的文件: {self.stats['files_updated']}")
            logger.info(f"删除的文件: {self.stats['files_deleted']}")
            logger.info(f"跳过的文件: {self.stats['files_skipped']}")
            logger.info(f"创建的目录: {self.stats['dirs_created']}")
            logger.info(f"解决的冲突: {self.stats['conflicts_resolved']}")
            logger.info(f"发生的错误: {self.stats['errors']}")
            logger.info(f"复制的总字节数: {self.stats['total_bytes_copied']}")

            return self.stats

        except Exception as e:
            logger.error(f"同步过程中出错: {e}")
            self.stats["errors"] += 1
            return self.stats

    def generate_report(self, output_file: Optional[str] = None) -> str:
        """
        生成同步报告
        
        Args:
            output_file: 输出文件路径，如果为None则只返回报告内容
            
        Returns:
            报告内容
        """
        # 创建报告内容
        report = {
            "source_dir": self.source_dir,
            "target_dir": self.target_dir,
            "sync_mode": self.mode.value,
            "conflict_resolution": self.conflict_resolution.value,
            "dry_run": self.dry_run,
            "start_time": datetime.datetime.fromtimestamp(self.start_time).strftime('%Y-%m-%d %H:%M:%S'),
            "end_time": datetime.datetime.fromtimestamp(time.time()).strftime('%Y-%m-%d %H:%M:%S'),
            "stats": self.stats,
            "actions": [
                {
                    "file": item.rel_path,
                    "action": item.action.value,
                    "reason": item.reason,
                    "conflict": item.conflict
                }
                for item in self.sync_plan
            ]
        }

        # 将报告转换为JSON字符串
        report_str = json.dumps(report, indent=2)

        # 如果指定了输出文件，则写入文件
        if output_file:
            with open(output_file, 'w', encoding='utf-8') as f:
                f.write(report_str)

        return report_str

    def _create_sync_plan(self) -> None:
        """创建同步计划，确定需要执行的文件操作"""
        # 清空现有的同步计划
        self.sync_plan = []

        # 扫描源目录和目标目录中的所有文件
        source_files = self._scan_directory(self.source_dir)
        target_files = self._scan_directory(self.target_dir)

        # 合并文件列表，获取所有唯一的相对路径
        all_rel_paths = set(source_files) | set(target_files)

        # 对每个相对路径创建同步对
        for rel_path in all_rel_paths:
            source_path = os.path.join(self.source_dir, rel_path)
            target_path = os.path.join(self.target_dir, rel_path)

            # 创建同步对
            sync_pair = SyncPair(source_path, target_path, rel_path)

            # 检查是否需要同步
            if sync_pair.need_sync(self.mode):
                # 检查是否存在冲突
                if (self.mode == SyncMode.TWO_WAY and
                        sync_pair.source.exists and sync_pair.target.exists and
                        not sync_pair.is_identical()):

                    sync_pair.conflict = True
                    # 解决冲突
                    action, reason = sync_pair.resolve_conflict(self.conflict_resolution)
                    sync_pair.action = action
                    sync_pair.reason = reason

                    if action != FileAction.SKIP:
                        self.sync_plan.append(sync_pair)
                        self.stats["conflicts_resolved"] += 1

                # 处理镜像模式下的文件删除
                elif (self.mode == SyncMode.MIRROR and
                      not sync_pair.source.exists and sync_pair.target.exists):

                    sync_pair.action = FileAction.DELETE
                    sync_pair.reason = "镜像模式：删除目标中的孤立文件"
                    self.sync_plan.append(sync_pair)

                # 处理普通的文件复制（单向、更新和双向模式）
                elif sync_pair.source.exists:
                    if not sync_pair.target.exists:
                        sync_pair.action = FileAction.COPY
                        sync_pair.reason = "目标不存在"
                        self.sync_plan.append(sync_pair)
                    elif sync_pair.source.mtime > sync_pair.target.mtime:
                        sync_pair.action = FileAction.COPY
                        sync_pair.reason = "源文件较新"
                        self.sync_plan.append(sync_pair)

                # 处理双向模式下的反向复制（从目标到源）
                elif (self.mode == SyncMode.TWO_WAY and
                      not sync_pair.source.exists and sync_pair.target.exists):

                    # 反转源和目标
                    reverse_pair = SyncPair(target_path, source_path, rel_path)
                    reverse_pair.action = FileAction.COPY
                    reverse_pair.reason = "源不存在，目标存在（双向同步）"
                    self.sync_plan.append(reverse_pair)

            # 统计已扫描的文件数
            self.stats["files_scanned"] += 1

        logger.info(f"同步计划已创建，需要处理 {len(self.sync_plan)} 个文件")

    def _execute_sync_plan(self) -> None:
        """执行同步计划，进行实际的文件操作"""
        for sync_pair in self.sync_plan:
            try:
                self.current_file = sync_pair.rel_path

                # 如果是模拟运行，只记录而不执行操作
                if self.dry_run:
                    logger.info(f"[模拟] {sync_pair.action.value} {sync_pair.rel_path} - {sync_pair.reason}")
                    continue

                # 根据操作类型执行不同的操作
                if sync_pair.action == FileAction.COPY:
                    if sync_pair.source.is_dir:
                        # 创建目录
                        if not os.path.exists(sync_pair.target.path):
                            os.makedirs(sync_pair.target.path, exist_ok=True)
                            logger.info(f"创建目录: {sync_pair.rel_path}")
                            self.stats["dirs_created"] += 1
                    else:
                        # 创建父目录（如果不存在）
                        parent_dir = os.path.dirname(sync_pair.target.path)
                        if parent_dir and not os.path.exists(parent_dir):
                            os.makedirs(parent_dir, exist_ok=True)
                            self.stats["dirs_created"] += 1

                        # 复制文件
                        if os.path.exists(sync_pair.target.path):
                            logger.info(f"更新文件: {sync_pair.rel_path}")
                            self.stats["files_updated"] += 1
                        else:
                            logger.info(f"复制文件: {sync_pair.rel_path}")
                            self.stats["files_copied"] += 1

                        # 执行复制
                        shutil.copy2(sync_pair.source.path, sync_pair.target.path)

                        # 更新统计信息
                        self.stats["total_bytes_copied"] += sync_pair.source.size

                        # 如果不保留元数据，则更新修改时间
                        if not self.preserve_metadata:
                            os.utime(sync_pair.target.path, None)  # 设置为当前时间

                elif sync_pair.action == FileAction.DELETE:
                    if sync_pair.target.is_dir:
                        # 删除目录
                        shutil.rmtree(sync_pair.target.path)
                        logger.info(f"删除目录: {sync_pair.rel_path}")
                    else:
                        # 删除文件
                        os.remove(sync_pair.target.path)
                        logger.info(f"删除文件: {sync_pair.rel_path}")

                    self.stats["files_deleted"] += 1

                elif sync_pair.action == FileAction.SKIP:
                    logger.debug(f"跳过文件: {sync_pair.rel_path} - {sync_pair.reason}")
                    self.stats["files_skipped"] += 1

            except Exception as e:
                logger.error(f"处理文件 {sync_pair.rel_path} 时出错: {e}")
                self.stats["errors"] += 1

    def _scan_directory(self, dir_path: str) -> Dict[str, str]:
        """
        扫描目录，返回所有文件的相对路径
        
        Args:
            dir_path: 目录路径
            
        Returns:
            文件相对路径字典，键为相对路径，值为绝对路径
        """
        result = {}

        # 如果目录不存在，返回空字典
        if not os.path.exists(dir_path):
            return result

        base_path = os.path.abspath(dir_path)

        for root, dirs, files in os.walk(dir_path, followlinks=self.follow_symlinks):
            # 过滤隐藏文件和目录
            if not self.include_hidden:
                dirs[:] = [d for d in dirs if not d.startswith('.')]
                files = [f for f in files if not f.startswith('.')]

            # 过滤排除的模式
            for exclude_pattern in self.exclude_patterns:
                dirs[:] = [d for d in dirs if not self._match_pattern(d, exclude_pattern)]
                files = [f for f in files if not self._match_pattern(f, exclude_pattern)]

            # 计算相对路径
            rel_root = os.path.relpath(root, base_path)
            if rel_root == '.':
                rel_root = ''

            # 添加目录
            if rel_root:
                result[rel_root] = os.path.join(base_path, rel_root)

            # 添加文件
            for file in files:
                rel_path = os.path.join(rel_root, file)
                result[rel_path] = os.path.join(base_path, rel_path)

        return result

    def _match_pattern(self, name: str, pattern: str) -> bool:
        """
        检查文件名是否匹配给定模式
        
        Args:
            name: 文件名
            pattern: 匹配模式（支持通配符）
            
        Returns:
            是否匹配
        """
        import fnmatch
        return fnmatch.fnmatch(name, pattern)


def parse_arguments():
    """解析命令行参数"""
    parser = argparse.ArgumentParser(description="文件同步工具 - 同步两个目录的内容")

    # 基本参数
    parser.add_argument("source", help="源目录路径")
    parser.add_argument("target", help="目标目录路径")

    # 同步模式
    parser.add_argument("-m", "--mode", choices=["one-way", "two-way", "mirror", "update"],
                        default="one-way", help="同步模式（默认: one-way）")

    # 冲突解决
    parser.add_argument("-c", "--conflict", choices=["newer", "larger", "source", "target", "skip", "prompt"],
                        default="newer", help="冲突解决策略（默认: newer）")

    # 文件过滤
    parser.add_argument("-e", "--exclude", nargs="+", default=[],
                        help="排除的文件模式列表（如 *.tmp *.log）")
    parser.add_argument("--include-hidden", action="store_true",
                        help="包括隐藏文件（以.开头）")

    # 同步选项
    parser.add_argument("--delete-orphaned", action="store_true",
                        help="删除目标中源不存在的文件")
    parser.add_argument("--no-metadata", action="store_false", dest="preserve_metadata",
                        help="不保留文件元数据（修改时间等）")
    parser.add_argument("--follow-symlinks", action="store_true",
                        help="跟随符号链接")

    # 运行模式
    parser.add_argument("--dry-run", action="store_true",
                        help="仅模拟运行，不实际修改文件")

    # 输出选项
    parser.add_argument("-r", "--report", help="生成同步报告的文件路径")
    parser.add_argument("-q", "--quiet", action="store_true",
                        help="静默模式，减少输出")
    parser.add_argument("-v", "--verbose", action="store_true",
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

    try:
        # 确保源目录存在
        if not os.path.exists(args.source):
            logger.error(f"源目录不存在: {args.source}")
            return 1

        # 创建同步器
        synchronizer = DirectorySynchronizer(
            source_dir=args.source,
            target_dir=args.target,
            mode=SyncMode(args.mode),
            conflict_resolution=ConflictResolution(args.conflict),
            exclude_patterns=args.exclude,
            include_hidden=args.include_hidden,
            follow_symlinks=args.follow_symlinks,
            dry_run=args.dry_run,
            delete_orphaned=args.delete_orphaned,
            preserve_metadata=args.preserve_metadata
        )

        # 执行同步
        synchronizer.synchronize()

        # 生成报告
        if args.report:
            synchronizer.generate_report(args.report)
            logger.info(f"同步报告已保存到: {args.report}")

        return 0

    except Exception as e:
        logger.error(f"同步过程中出错: {e}")
        return 1


if __name__ == "__main__":
    try:
        sys.exit(main())
    except KeyboardInterrupt:
        print("\n同步操作被用户中断")
        sys.exit(1)
    except Exception as e:
        logger.error(f"程序出错: {e}")
        sys.exit(2)
