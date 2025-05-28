#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
文件清理工具

这个脚本用于查找和删除临时文件、旧文件或不必要的文件，帮助优化磁盘空间、
提高系统性能并保持文件系统整洁。支持多种文件筛选方法、安全删除选项和
详细的清理报告，适用于系统维护、开发环境清理和定期磁盘整理等场景。
"""

import argparse
import datetime
import fnmatch
import logging
import os
import re
import shutil
import stat
import sys
from enum import Enum, auto
from typing import Dict, List, Optional

# 设置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)
logger = logging.getLogger(__name__)

# 尝试导入平台特定的库
try:
    import send2trash

    HAS_SEND2TRASH = True
except ImportError:
    HAS_SEND2TRASH = False
    logger.warning("未安装send2trash库，无法使用'移至回收站'功能。可通过运行 pip install send2trash 安装。")

try:
    import psutil

    HAS_PSUTIL = True
except ImportError:
    HAS_PSUTIL = False
    logger.warning("未安装psutil库，无法使用'检测运行中进程'功能。可通过运行 pip install psutil 安装。")


class CleanMode(Enum):
    """清理模式枚举"""
    REPORT = auto()  # 仅报告，不删除
    DELETE = auto()  # 直接删除
    TRASH = auto()  # 移至回收站
    MOVE = auto()  # 移动到指定目录
    INTERACTIVE = auto()  # 交互式确认


class FileCategory(Enum):
    """文件分类枚举"""
    TEMP = "临时文件"
    BACKUP = "备份文件"
    CACHE = "缓存文件"
    LOG = "日志文件"
    EMPTY = "空文件"
    DUPLICATE = "重复文件"
    OLD = "旧文件"
    SYSTEM = "系统文件"
    CUSTOM = "自定义规则"
    OTHER = "其他文件"


class FileMatch:
    """表示匹配的文件及其信息"""

    def __init__(self, path: str, category: FileCategory, reason: str, size: int = 0):
        """
        初始化文件匹配对象
        
        Args:
            path: 文件路径
            category: 文件分类
            reason: 匹配原因
            size: 文件大小（字节）
        """
        self.path = path
        self.category = category
        self.reason = reason
        self._size = size
        self._stat = None

    @property
    def size(self) -> int:
        """获取文件大小"""
        if self._size == 0:
            try:
                self._size = os.path.getsize(self.path)
            except (OSError, FileNotFoundError):
                self._size = 0
        return self._size

    @property
    def stat(self) -> os.stat_result:
        """获取文件状态信息"""
        if not self._stat:
            try:
                self._stat = os.stat(self.path)
            except (OSError, FileNotFoundError):
                pass
        return self._stat

    @property
    def modified_time(self) -> datetime.datetime:
        """获取文件修改时间"""
        if self.stat:
            return datetime.datetime.fromtimestamp(self.stat.st_mtime)
        return datetime.datetime.now()

    @property
    def access_time(self) -> datetime.datetime:
        """获取文件访问时间"""
        if self.stat:
            return datetime.datetime.fromtimestamp(self.stat.st_atime)
        return datetime.datetime.now()

    @property
    def creation_time(self) -> datetime.datetime:
        """获取文件创建时间"""
        if self.stat:
            # Windows和部分Unix系统支持创建时间
            if hasattr(self.stat, 'st_birthtime'):
                return datetime.datetime.fromtimestamp(self.stat.st_birthtime)
            # 回退到修改时间
            return self.modified_time
        return datetime.datetime.now()

    @property
    def is_directory(self) -> bool:
        """检查是否为目录"""
        return os.path.isdir(self.path)

    @property
    def is_system_file(self) -> bool:
        """检查是否为系统文件"""
        if self.stat:
            # Windows系统文件检测
            if os.name == 'nt':
                return bool(self.stat.st_file_attributes & stat.FILE_ATTRIBUTE_SYSTEM) if hasattr(self.stat,
                                                                                                  'st_file_attributes') else False
        return False

    @property
    def extension(self) -> str:
        """获取文件扩展名"""
        return os.path.splitext(self.path)[1].lower()

    @property
    def filename(self) -> str:
        """获取文件名"""
        return os.path.basename(self.path)

    def format_size(self) -> str:
        """格式化文件大小"""
        size = self.size
        for unit in ['B', 'KB', 'MB', 'GB', 'TB']:
            if size < 1024 or unit == 'TB':
                return f"{size:.2f} {unit}"
            size /= 1024

    def __str__(self) -> str:
        """字符串表示"""
        return f"{self.path} ({self.format_size()}) - {self.category.value}: {self.reason}"


class FileCleaner:
    """文件清理工具类，提供查找和删除临时文件、旧文件或不必要文件的功能"""

    # 常见临时文件扩展名
    TEMP_EXTENSIONS = [
        '.tmp', '.temp', '.bak', '.old', '.swp', '.swo',
        '.dmp', '.dump', '.$$', '.~', '.part'
    ]

    # 常见临时文件模式
    TEMP_PATTERNS = [
        '*.tmp', '*.temp', '*~', '*.bak', '*.old', '*.swp',
        '*.swo', '*.dmp', '*.dump', '*.$$$', '*.part',
        'thumbs.db', '.ds_store', '._*', '*.crdownload',
        '~$*', '*.cache'
    ]

    # 常见缓存目录名
    CACHE_DIRS = [
        'cache', '.cache', 'tmp', 'temp', 'thumbs',
        '__pycache__', '.pytest_cache', '.mypy_cache',
        'node_modules', '.gradle', 'build'
    ]

    # 系统特定临时文件
    SYSTEM_TEMP_FILES = {
        'windows': ['thumbs.db', 'desktop.ini', 'ntuser.dat*'],
        'macos': ['.ds_store', '.localized', '.Spotlight-V100', '.Trashes', '.fseventsd'],
        'linux': ['.directory', '*~', '.Trash*']
    }

    def __init__(
            self,
            paths: List[str],
            recursive: bool = True,
            mode: CleanMode = CleanMode.REPORT,
            include_patterns: Optional[List[str]] = None,
            exclude_patterns: Optional[List[str]] = None,
            exclude_dirs: Optional[List[str]] = None,
            min_size: Optional[int] = None,
            max_size: Optional[int] = None,
            min_age: Optional[int] = None,
            last_access: Optional[int] = None,
            only_empty: bool = False,
            find_duplicates: bool = False,
            target_dir: Optional[str] = None,
            keep_structure: bool = False,
            log_file: Optional[str] = None,
            dry_run: bool = False,
            verbose: bool = False,
            clean_temp: bool = True,
            clean_cache: bool = False,
            clean_logs: bool = False,
            clean_backups: bool = False,
            custom_rules: Optional[List[str]] = None
    ):
        """
        初始化文件清理器
        
        Args:
            paths: 要清理的文件或目录路径列表
            recursive: 是否递归处理子目录
            mode: 清理模式（报告、删除、移至回收站等）
            include_patterns: 要包含的文件模式列表（支持通配符）
            exclude_patterns: 要排除的文件模式列表（支持通配符）
            exclude_dirs: 要排除的目录名列表
            min_size: 最小文件大小（字节）
            max_size: 最大文件大小（字节）
            min_age: 最小文件年龄（天）
            last_access: 最后访问时间（天）
            only_empty: 仅处理空文件
            find_duplicates: 是否查找重复文件
            target_dir: 移动文件的目标目录（当mode为MOVE时使用）
            keep_structure: 移动文件时是否保持目录结构
            log_file: 日志文件路径
            dry_run: 模拟运行，不实际删除文件
            verbose: 显示详细信息
            clean_temp: 是否清理临时文件
            clean_cache: 是否清理缓存文件
            clean_logs: 是否清理日志文件
            clean_backups: 是否清理备份文件
            custom_rules: 自定义清理规则（正则表达式）
        """
        self.paths = [os.path.abspath(p) for p in paths]
        self.recursive = recursive
        self.mode = mode
        self.include_patterns = include_patterns or ['*.*']
        self.exclude_patterns = exclude_patterns or []
        self.exclude_dirs = exclude_dirs or []
        self.min_size = min_size
        self.max_size = max_size
        self.min_age = min_age
        self.last_access = last_access
        self.only_empty = only_empty
        self.find_duplicates = find_duplicates
        self.target_dir = os.path.abspath(target_dir) if target_dir else None
        self.keep_structure = keep_structure
        self.log_file = log_file
        self.dry_run = dry_run or mode == CleanMode.REPORT
        self.verbose = verbose

        # 清理选项
        self.clean_temp = clean_temp
        self.clean_cache = clean_cache
        self.clean_logs = clean_logs
        self.clean_backups = clean_backups
        self.custom_rules = custom_rules or []

        # 如果用户选择移动模式但未指定目标目录，则强制报告模式
        if self.mode == CleanMode.MOVE and not self.target_dir:
            logger.warning("未指定目标目录，强制使用报告模式。")
            self.mode = CleanMode.REPORT
            self.dry_run = True

        # 如果用户选择回收站模式但未安装send2trash，则发出警告
        if self.mode == CleanMode.TRASH and not HAS_SEND2TRASH:
            logger.warning("未安装send2trash库，无法使用'移至回收站'功能。将使用报告模式。")
            self.mode = CleanMode.REPORT
            self.dry_run = True

        # 创建目标目录（如果需要）
        if self.mode == CleanMode.MOVE and self.target_dir and not self.dry_run:
            os.makedirs(self.target_dir, exist_ok=True)

        # 设置文件日志（如果需要）
        if self.log_file:
            file_handler = logging.FileHandler(self.log_file, 'w', encoding='utf-8')
            file_handler.setFormatter(logging.Formatter('%(asctime)s - %(levelname)s - %(message)s'))
            logger.addHandler(file_handler)

        # 统计信息
        self.stats = {
            'scanned_files': 0,
            'scanned_dirs': 0,
            'matched_files': 0,
            'matched_dirs': 0,
            'cleaned_files': 0,
            'cleaned_dirs': 0,
            'errors': 0,
            'total_size': 0,
            'saved_size': 0,
            'categories': {cat: {'count': 0, 'size': 0} for cat in FileCategory}
        }

        # 匹配的文件列表
        self.matched_files: List[FileMatch] = []

        # 重复文件字典
        self.duplicate_files: Dict[str, List[str]] = {}

    def run(self) -> bool:
        """
        运行文件清理流程
        
        Returns:
            处理是否成功
        """
        logger.info(f"开始扫描文件...")

        # 扫描文件
        for path in self.paths:
            if os.path.isfile(path):
                self._process_file(path)
            elif os.path.isdir(path):
                self._scan_directory(path)
            else:
                logger.warning(f"路径不存在或无法访问: {path}")

        # 查找重复文件（如果启用）
        if self.find_duplicates:
            self._find_duplicate_files()

        # 处理匹配的文件
        self._process_matched_files()

        # 打印统计信息
        self._print_summary()

        return self.stats['errors'] == 0

    def _scan_directory(self, directory: str) -> None:
        """
        递归扫描目录
        
        Args:
            directory: 目录路径
        """
        try:
            self.stats['scanned_dirs'] += 1

            # 检查目录是否应被排除
            dir_name = os.path.basename(directory)
            if any(dir_name == exclude_dir for exclude_dir in self.exclude_dirs):
                if self.verbose:
                    logger.info(f"排除目录: {directory}")
                return

            # 检查目录是否是缓存目录
            if self.clean_cache and self._is_cache_directory(directory):
                reason = f"缓存目录"
                self.matched_files.append(FileMatch(directory, FileCategory.CACHE, reason))
                self.stats['matched_dirs'] += 1
                return

            # 遍历目录
            for item in os.listdir(directory):
                item_path = os.path.join(directory, item)

                if os.path.isfile(item_path):
                    self._process_file(item_path)
                elif os.path.isdir(item_path) and self.recursive:
                    self._scan_directory(item_path)

        except (PermissionError, OSError) as e:
            logger.error(f"处理目录时出错: {directory} - {str(e)}")
            self.stats['errors'] += 1

    def _process_file(self, file_path: str) -> None:
        """
        处理单个文件
        
        Args:
            file_path: 文件路径
        """
        try:
            self.stats['scanned_files'] += 1

            # 检查文件是否匹配包含/排除模式
            if not self._matches_patterns(file_path):
                return

            # 检查文件是否匹配特定规则
            match = self._check_file_match(file_path)
            if match:
                self.matched_files.append(match)
                self.stats['matched_files'] += 1
                self.stats['categories'][match.category]['count'] += 1
                self.stats['categories'][match.category]['size'] += match.size
                self.stats['total_size'] += match.size

                if self.verbose:
                    logger.info(f"匹配文件: {match}")

        except (PermissionError, OSError) as e:
            logger.error(f"处理文件时出错: {file_path} - {str(e)}")
            self.stats['errors'] += 1

    def _check_file_match(self, file_path: str) -> Optional[FileMatch]:
        """
        检查文件是否匹配清理条件
        
        Args:
            file_path: 文件路径
            
        Returns:
            如果匹配则返回FileMatch对象，否则返回None
        """
        try:
            # 获取文件信息
            file_name = os.path.basename(file_path)
            file_ext = os.path.splitext(file_name)[1].lower()
            file_size = os.path.getsize(file_path)
            file_stat = os.stat(file_path)

            # 检查空文件
            if self.only_empty and file_size == 0:
                return FileMatch(file_path, FileCategory.EMPTY, "空文件", file_size)

            # 检查文件大小
            if self.min_size is not None and file_size < self.min_size:
                return None
            if self.max_size is not None and file_size > self.max_size:
                return None

            # 检查文件年龄
            if self.min_age is not None:
                modified_time = datetime.datetime.fromtimestamp(file_stat.st_mtime)
                age_days = (datetime.datetime.now() - modified_time).days
                if age_days < self.min_age:
                    return None
                if age_days >= self.min_age:
                    return FileMatch(file_path, FileCategory.OLD, f"文件已有{age_days}天未修改", file_size)

            # 检查最后访问时间
            if self.last_access is not None:
                access_time = datetime.datetime.fromtimestamp(file_stat.st_atime)
                days_since_access = (datetime.datetime.now() - access_time).days
                if days_since_access >= self.last_access:
                    return FileMatch(file_path, FileCategory.OLD, f"文件已有{days_since_access}天未访问", file_size)

            # 检查临时文件
            if self.clean_temp and self._is_temp_file(file_path):
                return FileMatch(file_path, FileCategory.TEMP, "临时文件", file_size)

            # 检查日志文件
            if self.clean_logs and self._is_log_file(file_path):
                return FileMatch(file_path, FileCategory.LOG, "日志文件", file_size)

            # 检查备份文件
            if self.clean_backups and self._is_backup_file(file_path):
                return FileMatch(file_path, FileCategory.BACKUP, "备份文件", file_size)

            # 检查系统临时文件
            if self._is_system_temp_file(file_path):
                return FileMatch(file_path, FileCategory.SYSTEM, "系统临时文件", file_size)

            # 检查自定义规则
            for rule in self.custom_rules:
                if re.search(rule, file_path):
                    return FileMatch(file_path, FileCategory.CUSTOM, f"匹配自定义规则: {rule}", file_size)

            return None

        except (PermissionError, OSError) as e:
            logger.error(f"检查文件时出错: {file_path} - {str(e)}")
            self.stats['errors'] += 1
            return None

    def _matches_patterns(self, file_path: str) -> bool:
        """
        检查文件是否匹配包含/排除模式
        
        Args:
            file_path: 文件路径
            
        Returns:
            是否匹配
        """
        file_name = os.path.basename(file_path)

        # 检查包含模式
        included = any(fnmatch.fnmatch(file_name, pattern) for pattern in self.include_patterns)
        if not included:
            return False

        # 检查排除模式
        excluded = any(fnmatch.fnmatch(file_name, pattern) for pattern in self.exclude_patterns)
        if excluded:
            return False

        return True

    def _is_temp_file(self, file_path: str) -> bool:
        """
        检查是否为临时文件
        
        Args:
            file_path: 文件路径
            
        Returns:
            是否为临时文件
        """
        file_name = os.path.basename(file_path)
        file_ext = os.path.splitext(file_name)[1].lower()

        # 检查扩展名
        if file_ext in self.TEMP_EXTENSIONS:
            return True

        # 检查文件名模式
        for pattern in self.TEMP_PATTERNS:
            if fnmatch.fnmatch(file_name.lower(), pattern.lower()):
                return True

        return False

    def _is_cache_directory(self, directory: str) -> bool:
        """
        检查是否为缓存目录
        
        Args:
            directory: 目录路径
            
        Returns:
            是否为缓存目录
        """
        dir_name = os.path.basename(directory).lower()

        for cache_dir in self.CACHE_DIRS:
            if dir_name == cache_dir.lower():
                return True

        return False

    def _is_log_file(self, file_path: str) -> bool:
        """
        检查是否为日志文件
        
        Args:
            file_path: 文件路径
            
        Returns:
            是否为日志文件
        """
        file_name = os.path.basename(file_path).lower()
        file_ext = os.path.splitext(file_name)[1].lower()

        # 检查扩展名
        if file_ext == '.log':
            return True

        # 检查文件名
        log_patterns = ['*.log', '*_log', 'log_*', '*-log', 'log-*', 'debug*', 'error*', 'access*']
        for pattern in log_patterns:
            if fnmatch.fnmatch(file_name, pattern):
                return True

        return False

    def _is_backup_file(self, file_path: str) -> bool:
        """
        检查是否为备份文件
        
        Args:
            file_path: 文件路径
            
        Returns:
            是否为备份文件
        """
        file_name = os.path.basename(file_path).lower()
        file_ext = os.path.splitext(file_name)[1].lower()

        # 检查扩展名
        backup_extensions = ['.bak', '.backup', '.old', '.orig', '.save', '.copy']
        if file_ext in backup_extensions:
            return True

        # 检查文件名
        backup_patterns = ['*-backup*', '*_backup*', '*backup*', '*.bak', '*.old', '*.orig', '*_old', '*-old']
        for pattern in backup_patterns:
            if fnmatch.fnmatch(file_name, pattern):
                return True

        return False

    def _is_system_temp_file(self, file_path: str) -> bool:
        """
        检查是否为系统临时文件
        
        Args:
            file_path: 文件路径
            
        Returns:
            是否为系统临时文件
        """
        file_name = os.path.basename(file_path).lower()

        # 确定操作系统类型
        if os.name == 'nt':  # Windows
            os_type = 'windows'
        elif sys.platform == 'darwin':  # macOS
            os_type = 'macos'
        else:  # Linux等类Unix系统
            os_type = 'linux'

        # 检查操作系统特定的临时文件
        for pattern in self.SYSTEM_TEMP_FILES.get(os_type, []):
            if fnmatch.fnmatch(file_name, pattern):
                return True

        # 检查所有系统的通用临时文件
        common_temp_files = ['.svn', '.git', '.hg', '.vscode', '.idea', '.vs']
        for temp_file in common_temp_files:
            if file_name == temp_file:
                return True

        return False

    def _find_duplicate_files(self) -> None:
        """查找重复文件"""
        if not self.find_duplicates:
            return

        logger.info("开始查找重复文件...")

        # 按大小分组文件（快速预筛选）
        size_groups = {}
        for file_match in self.matched_files:
            if file_match.is_directory:
                continue

            size = file_match.size
            if size > 0:  # 忽略空文件
                if size not in size_groups:
                    size_groups[size] = []
                size_groups[size].append(file_match.path)

        # 对每个大小组，检查内容是否相同
        for size, files in size_groups.items():
            if len(files) < 2:
                continue

            # 使用文件内容哈希进行比较
            hash_groups = {}
            for file_path in files:
                try:
                    file_hash = self._get_file_hash(file_path)
                    if file_hash not in hash_groups:
                        hash_groups[file_hash] = []
                    hash_groups[file_hash].append(file_path)
                except (IOError, OSError) as e:
                    logger.error(f"计算文件哈希时出错: {file_path} - {str(e)}")

            # 将重复文件添加到结果中
            for file_hash, duplicate_files in hash_groups.items():
                if len(duplicate_files) > 1:
                    self.duplicate_files[file_hash] = duplicate_files

                    # 保留第一个文件，将其余文件标记为重复
                    original = duplicate_files[0]
                    for duplicate in duplicate_files[1:]:
                        # 检查文件是否已在匹配列表中
                        already_matched = False
                        for match in self.matched_files:
                            if match.path == duplicate:
                                already_matched = True
                                break

                        if not already_matched:
                            size = os.path.getsize(duplicate)
                            match = FileMatch(duplicate, FileCategory.DUPLICATE, f"重复文件，原始文件: {original}", size)
                            self.matched_files.append(match)
                            self.stats['matched_files'] += 1
                            self.stats['categories'][FileCategory.DUPLICATE]['count'] += 1
                            self.stats['categories'][FileCategory.DUPLICATE]['size'] += size
                            self.stats['total_size'] += size

                            if self.verbose:
                                logger.info(f"匹配重复文件: {match}")

    def _get_file_hash(self, file_path: str, block_size: int = 65536) -> str:
        """
        计算文件哈希值
        
        Args:
            file_path: 文件路径
            block_size: 读取块大小
            
        Returns:
            文件哈希值
        """
        import hashlib
        hasher = hashlib.md5()

        with open(file_path, 'rb') as f:
            buf = f.read(block_size)
            while len(buf) > 0:
                hasher.update(buf)
                buf = f.read(block_size)

        return hasher.hexdigest()

    def _process_matched_files(self) -> None:
        """处理匹配的文件"""
        if not self.matched_files:
            logger.info("未找到匹配的文件")
            return

        logger.info(
            f"找到 {len(self.matched_files)} 个文件可能需要清理，总大小 {self._format_size(self.stats['total_size'])}")

        # 如果只是报告模式，直接返回
        if self.mode == CleanMode.REPORT or self.dry_run:
            return

        # 对匹配的文件按路径排序，以确保先处理子目录中的文件，再处理目录本身
        self.matched_files.sort(key=lambda x: x.path)

        # 处理每个匹配的文件
        for match in self.matched_files:
            try:
                if match.is_directory:
                    self._process_directory(match)
                else:
                    self._process_single_file(match)

            except (PermissionError, OSError) as e:
                logger.error(f"处理文件时出错: {match.path} - {str(e)}")
                self.stats['errors'] += 1

    def _process_directory(self, match: FileMatch) -> None:
        """
        处理目录
        
        Args:
            match: 匹配的目录
        """
        if self.dry_run:
            logger.info(f"[模拟] 将处理目录: {match.path}")
            return

        try:
            if self.mode == CleanMode.INTERACTIVE:
                response = input(f"是否要处理目录 {match.path}? (y/n): ").lower()
                if response != 'y':
                    logger.info(f"跳过目录: {match.path}")
                    return

            if self.mode == CleanMode.DELETE:
                logger.info(f"删除目录: {match.path}")
                shutil.rmtree(match.path)
                self.stats['cleaned_dirs'] += 1
                self.stats['saved_size'] += match.size

            elif self.mode == CleanMode.TRASH:
                logger.info(f"移动目录到回收站: {match.path}")
                send2trash.send2trash(match.path)
                self.stats['cleaned_dirs'] += 1
                self.stats['saved_size'] += match.size

            elif self.mode == CleanMode.MOVE:
                target_path = self._get_target_path(match.path)
                logger.info(f"移动目录: {match.path} -> {target_path}")
                os.makedirs(os.path.dirname(target_path), exist_ok=True)
                shutil.move(match.path, target_path)
                self.stats['cleaned_dirs'] += 1

        except (PermissionError, OSError) as e:
            logger.error(f"处理目录时出错: {match.path} - {str(e)}")
            self.stats['errors'] += 1

    def _process_single_file(self, match: FileMatch) -> None:
        """
        处理单个文件
        
        Args:
            match: 匹配的文件
        """
        if self.dry_run:
            logger.info(f"[模拟] 将处理文件: {match.path}")
            return

        try:
            if self.mode == CleanMode.INTERACTIVE:
                response = input(f"是否要处理文件 {match.path}? (y/n): ").lower()
                if response != 'y':
                    logger.info(f"跳过文件: {match.path}")
                    return

            if self.mode == CleanMode.DELETE:
                logger.info(f"删除文件: {match.path}")
                os.remove(match.path)
                self.stats['cleaned_files'] += 1
                self.stats['saved_size'] += match.size

            elif self.mode == CleanMode.TRASH:
                logger.info(f"移动文件到回收站: {match.path}")
                send2trash.send2trash(match.path)
                self.stats['cleaned_files'] += 1
                self.stats['saved_size'] += match.size

            elif self.mode == CleanMode.MOVE:
                target_path = self._get_target_path(match.path)
                logger.info(f"移动文件: {match.path} -> {target_path}")
                os.makedirs(os.path.dirname(target_path), exist_ok=True)
                shutil.move(match.path, target_path)
                self.stats['cleaned_files'] += 1

        except (PermissionError, OSError) as e:
            logger.error(f"处理文件时出错: {match.path} - {str(e)}")
            self.stats['errors'] += 1

    def _get_target_path(self, source_path: str) -> str:
        """
        获取目标路径
        
        Args:
            source_path: 源文件路径
            
        Returns:
            目标文件路径
        """
        if not self.target_dir:
            return source_path

        if self.keep_structure:
            # 保持目录结构
            rel_path = os.path.relpath(source_path, self.paths[0])
            return os.path.join(self.target_dir, rel_path)
        else:
            # 直接放在目标目录下
            return os.path.join(self.target_dir, os.path.basename(source_path))

    def _print_summary(self) -> None:
        """打印清理统计摘要"""
        logger.info("=" * 60)
        logger.info("清理操作摘要")
        logger.info("=" * 60)
        logger.info(f"扫描的文件数: {self.stats['scanned_files']}")
        logger.info(f"扫描的目录数: {self.stats['scanned_dirs']}")
        logger.info(f"匹配的文件数: {self.stats['matched_files']}")
        logger.info(f"匹配的目录数: {self.stats['matched_dirs']}")

        if not self.dry_run and self.mode != CleanMode.REPORT:
            logger.info(f"清理的文件数: {self.stats['cleaned_files']}")
            logger.info(f"清理的目录数: {self.stats['cleaned_dirs']}")
            logger.info(f"释放的空间: {self._format_size(self.stats['saved_size'])}")
        else:
            logger.info(f"可释放的空间: {self._format_size(self.stats['total_size'])}")

        logger.info(f"错误数: {self.stats['errors']}")
        logger.info("-" * 60)

        # 按类别打印统计信息
        logger.info("按类别统计:")
        for category, stats in self.stats['categories'].items():
            if stats['count'] > 0:
                logger.info(f"  {category.value}: {stats['count']} 个文件，大小 {self._format_size(stats['size'])}")

        logger.info("=" * 60)

    @staticmethod
    def _format_size(size: int) -> str:
        """
        格式化文件大小
        
        Args:
            size: 文件大小（字节）
            
        Returns:
            格式化后的字符串
        """
        for unit in ['B', 'KB', 'MB', 'GB', 'TB']:
            if size < 1024 or unit == 'TB':
                return f"{size:.2f} {unit}"
            size /= 1024


def parse_size(size_str: str) -> int:
    """
    解析大小字符串（如1KB, 5MB）为字节数
    
    Args:
        size_str: 大小字符串
        
    Returns:
        字节数
    """
    if not size_str:
        return 0

    size_str = size_str.upper()
    units = {
        'B': 1,
        'KB': 1024,
        'MB': 1024 * 1024,
        'GB': 1024 * 1024 * 1024,
        'TB': 1024 * 1024 * 1024 * 1024
    }

    # 正则表达式匹配数字和单位
    match = re.match(r'^(\d+(\.\d+)?)\s*([KMGT]?B?)$', size_str)
    if match:
        value = float(match.group(1))
        unit = match.group(3)

        # 默认单位为字节
        if not unit:
            unit = 'B'

        # 转换为字节
        if unit in units:
            return int(value * units[unit])

    # 如果无法解析，尝试直接转换为整数
    try:
        return int(size_str)
    except ValueError:
        raise ValueError(f"无法解析大小: {size_str}")


def parse_args():
    """解析命令行参数"""
    parser = argparse.ArgumentParser(description='文件清理工具 - 查找和删除临时文件、旧文件或不必要的文件')

    # 文件选择参数
    parser.add_argument('paths', nargs='+', help='要清理的文件或目录路径')
    parser.add_argument('-r', '--recursive', action='store_true', help='递归处理子目录（默认启用）')
    parser.add_argument('--no-recursive', action='store_true', help='不递归处理子目录')

    # 清理模式
    mode_group = parser.add_argument_group('清理模式')
    mode_options = mode_group.add_mutually_exclusive_group()
    mode_options.add_argument('--report', action='store_true', help='仅报告，不删除文件（默认）')
    mode_options.add_argument('--delete', action='store_true', help='直接删除匹配的文件')
    mode_options.add_argument('--trash', action='store_true', help='将匹配的文件移至回收站（需要安装send2trash）')
    mode_options.add_argument('--move', action='store_true', help='将匹配的文件移动到指定目录')
    mode_options.add_argument('-i', '--interactive', action='store_true', help='交互式确认每个文件')

    # 文件筛选参数
    filter_group = parser.add_argument_group('文件筛选')
    filter_group.add_argument('--include', nargs='+', help='要包含的文件模式列表（如 *.tmp *.bak）')
    filter_group.add_argument('--exclude', nargs='+', help='要排除的文件模式列表')
    filter_group.add_argument('--exclude-dir', nargs='+', dest='exclude_dirs', help='要排除的目录名列表')
    filter_group.add_argument('--min-size', help='最小文件大小（如 1KB, 5MB）')
    filter_group.add_argument('--max-size', help='最大文件大小（如 10MB, 1GB）')
    filter_group.add_argument('--min-age', type=int, help='最小文件年龄（天）')
    filter_group.add_argument('--last-access', type=int, help='最后访问时间（天）')
    filter_group.add_argument('--empty-only', action='store_true', help='仅处理空文件')

    # 清理选项
    clean_group = parser.add_argument_group('清理选项')
    clean_group.add_argument('--temp', action='store_true', help='清理临时文件（默认启用）')
    clean_group.add_argument('--no-temp', action='store_true', help='不清理临时文件')
    clean_group.add_argument('--cache', action='store_true', help='清理缓存文件和目录')
    clean_group.add_argument('--logs', action='store_true', help='清理日志文件')
    clean_group.add_argument('--backups', action='store_true', help='清理备份文件')
    clean_group.add_argument('--duplicates', action='store_true', help='查找和清理重复文件')
    clean_group.add_argument('--custom', nargs='+', dest='custom_rules', help='自定义清理规则（正则表达式）')

    # 移动选项
    move_group = parser.add_argument_group('移动选项')
    move_group.add_argument('-t', '--target-dir', help='移动文件的目标目录（当--move选项启用时使用）')
    move_group.add_argument('--keep-structure', action='store_true', help='移动文件时保持目录结构')

    # 输出选项
    output_group = parser.add_argument_group('输出选项')
    output_group.add_argument('-l', '--log-file', help='将日志写入指定文件')
    output_group.add_argument('-n', '--dry-run', action='store_true', help='模拟运行，不实际删除文件')
    output_group.add_argument('-v', '--verbose', action='store_true', help='显示详细信息')

    args = parser.parse_args()

    # 处理矛盾的选项
    if args.no_recursive:
        args.recursive = False

    return args


def main():
    """主函数"""
    args = parse_args()

    # 确定清理模式
    if args.delete:
        mode = CleanMode.DELETE
    elif args.trash:
        mode = CleanMode.TRASH
    elif args.move:
        mode = CleanMode.MOVE
    elif args.interactive:
        mode = CleanMode.INTERACTIVE
    else:
        mode = CleanMode.REPORT

    # 解析文件大小
    min_size = parse_size(args.min_size) if args.min_size else None
    max_size = parse_size(args.max_size) if args.max_size else None

    # 确定清理选项
    clean_temp = not args.no_temp

    # 创建清理器实例
    cleaner = FileCleaner(
        paths=args.paths,
        recursive=args.recursive,
        mode=mode,
        include_patterns=args.include,
        exclude_patterns=args.exclude,
        exclude_dirs=args.exclude_dirs,
        min_size=min_size,
        max_size=max_size,
        min_age=args.min_age,
        last_access=args.last_access,
        only_empty=args.empty_only,
        find_duplicates=args.duplicates,
        target_dir=args.target_dir,
        keep_structure=args.keep_structure,
        log_file=args.log_file,
        dry_run=args.dry_run,
        verbose=args.verbose,
        clean_temp=clean_temp,
        clean_cache=args.cache,
        clean_logs=args.logs,
        clean_backups=args.backups,
        custom_rules=args.custom_rules
    )

    # 运行清理器
    success = cleaner.run()

    # 返回退出码
    return 0 if success else 1


if __name__ == '__main__':
    sys.exit(main())
