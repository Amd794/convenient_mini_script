#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
文件压缩/解压工具

这个脚本提供了文件和目录的压缩与解压功能，支持多种压缩格式，
包括zip、tar、tar.gz、tar.bz2等，适用于文件备份、文件共享和存储空间优化。
"""

import argparse
import logging
import os
import shutil
import sys
import tarfile
import zipfile
from enum import Enum
from typing import List, Optional

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)
logger = logging.getLogger(__name__)


class CompressFormat(Enum):
    """压缩格式枚举"""
    ZIP = "zip"
    TAR = "tar"
    TAR_GZ = "tar.gz"
    TAR_BZ2 = "tar.bz2"


class FileCompressor:
    """文件压缩器类，提供文件和目录的压缩与解压功能"""

    def __init__(self,
                 format: CompressFormat = CompressFormat.ZIP,
                 compression_level: int = 9,
                 exclude_patterns: List[str] = None,
                 include_hidden: bool = False):
        """
        初始化文件压缩器
        
        Args:
            format: 压缩格式
            compression_level: 压缩级别（0-9，仅适用于ZIP格式）
            exclude_patterns: 要排除的文件模式列表
            include_hidden: 是否包括隐藏文件
        """
        self.format = format
        self.compression_level = compression_level
        self.exclude_patterns = exclude_patterns or []
        self.include_hidden = include_hidden

        # 压缩统计信息
        self.stats = {
            "files_processed": 0,
            "total_size_before": 0,
            "total_size_after": 0,
            "skipped_files": 0,
            "errors": 0
        }

    def compress(self, source_path: str, output_path: Optional[str] = None) -> str:
        """
        压缩文件或目录
        
        Args:
            source_path: 要压缩的文件或目录路径
            output_path: 输出文件路径，如果为None则自动生成
            
        Returns:
            压缩文件的路径
        """
        # 检查源路径是否存在
        if not os.path.exists(source_path):
            raise FileNotFoundError(f"源路径不存在: {source_path}")

        # 如果输出路径未指定，则自动生成
        if output_path is None:
            source_base = os.path.basename(os.path.normpath(source_path))
            output_path = f"{source_base}.{self.format.value}"

        # 重置统计信息
        self.stats = {
            "files_processed": 0,
            "total_size_before": 0,
            "total_size_after": 0,
            "skipped_files": 0,
            "errors": 0
        }

        try:
            # 根据格式选择压缩方法
            if self.format == CompressFormat.ZIP:
                self._compress_zip(source_path, output_path)
            elif self.format in [CompressFormat.TAR, CompressFormat.TAR_GZ, CompressFormat.TAR_BZ2]:
                self._compress_tar(source_path, output_path)

            # 计算压缩后的大小
            if os.path.exists(output_path):
                self.stats["total_size_after"] = os.path.getsize(output_path)

            # 计算压缩率
            if self.stats["total_size_before"] > 0:
                compression_ratio = (1 - self.stats["total_size_after"] / self.stats["total_size_before"]) * 100
                logger.info(f"压缩完成: {self.stats['files_processed']} 个文件, "
                            f"压缩前: {self._format_size(self.stats['total_size_before'])}, "
                            f"压缩后: {self._format_size(self.stats['total_size_after'])}, "
                            f"压缩率: {compression_ratio:.2f}%")

            return output_path

        except Exception as e:
            logger.error(f"压缩过程中出错: {e}")
            self.stats["errors"] += 1
            raise

    def decompress(self, archive_path: str, output_dir: Optional[str] = None,
                   flatten: bool = False, specific_files: List[str] = None) -> str:
        """
        解压文件
        
        Args:
            archive_path: 压缩文件路径
            output_dir: 输出目录路径，如果为None则在当前目录创建同名目录
            flatten: 是否展平目录结构
            specific_files: 要解压的特定文件列表
            
        Returns:
            解压目录的路径
        """
        # 检查压缩文件是否存在
        if not os.path.exists(archive_path):
            raise FileNotFoundError(f"压缩文件不存在: {archive_path}")

        # 确定解压目标目录
        if output_dir is None:
            # 使用压缩文件名（不含扩展名）作为目录名
            archive_name = os.path.basename(archive_path)
            # 移除所有可能的扩展名
            for ext in ['.zip', '.tar', '.gz', '.bz2']:
                if archive_name.endswith(ext):
                    archive_name = archive_name[:-len(ext)]
            output_dir = archive_name

        # 创建输出目录（如果不存在）
        os.makedirs(output_dir, exist_ok=True)

        # 重置统计信息
        self.stats = {
            "files_processed": 0,
            "total_size_before": os.path.getsize(archive_path),
            "total_size_after": 0,
            "skipped_files": 0,
            "errors": 0
        }

        try:
            # 根据文件扩展名判断压缩格式
            if archive_path.endswith('.zip'):
                self._decompress_zip(archive_path, output_dir, flatten, specific_files)
            elif any(archive_path.endswith(ext) for ext in ['.tar', '.tar.gz', '.tgz', '.tar.bz2']):
                self._decompress_tar(archive_path, output_dir, flatten, specific_files)
            else:
                raise ValueError(f"不支持的压缩格式: {archive_path}")

            # 计算解压后的总大小
            self.stats["total_size_after"] = self._get_directory_size(output_dir)

            logger.info(f"解压完成: {self.stats['files_processed']} 个文件解压到 {output_dir}")

            return output_dir

        except Exception as e:
            logger.error(f"解压过程中出错: {e}")
            self.stats["errors"] += 1
            raise

    def list_contents(self, archive_path: str, verbose: bool = False) -> List[dict]:
        """
        列出压缩文件的内容
        
        Args:
            archive_path: 压缩文件路径
            verbose: 是否显示详细信息
            
        Returns:
            文件信息列表
        """
        # 检查压缩文件是否存在
        if not os.path.exists(archive_path):
            raise FileNotFoundError(f"压缩文件不存在: {archive_path}")

        files_info = []

        try:
            # 根据文件扩展名判断压缩格式
            if archive_path.endswith('.zip'):
                with zipfile.ZipFile(archive_path, 'r') as zip_file:
                    for info in zip_file.infolist():
                        file_info = {
                            'name': info.filename,
                            'size': info.file_size,
                            'compressed_size': info.compress_size,
                            'modified': f"{info.date_time[0]}-{info.date_time[1]:02d}-{info.date_time[2]:02d} "
                                        f"{info.date_time[3]:02d}:{info.date_time[4]:02d}:{info.date_time[5]:02d}",
                            'is_dir': info.filename.endswith('/')
                        }
                        files_info.append(file_info)

            elif any(archive_path.endswith(ext) for ext in ['.tar', '.tar.gz', '.tgz', '.tar.bz2']):
                with tarfile.open(archive_path, 'r:*') as tar_file:
                    for member in tar_file.getmembers():
                        file_info = {
                            'name': member.name,
                            'size': member.size,
                            'modified': member.mtime,
                            'is_dir': member.isdir(),
                            'type': self._get_tarfile_type(member)
                        }
                        files_info.append(file_info)
            else:
                raise ValueError(f"不支持的压缩格式: {archive_path}")

            # 输出文件列表
            if verbose:
                for info in files_info:
                    is_dir = '目录' if info.get('is_dir') else '文件'
                    size_str = self._format_size(info['size'])
                    modified = info.get('modified', 'N/A')
                    logger.info(f"{info['name']} ({is_dir}, {size_str}, 修改时间: {modified})")
            else:
                for info in files_info:
                    logger.info(info['name'])

            return files_info

        except Exception as e:
            logger.error(f"列出压缩文件内容时出错: {e}")
            raise

    def _compress_zip(self, source_path: str, output_path: str) -> None:
        """使用ZIP格式压缩文件或目录"""
        logger.info(f"正在创建ZIP压缩文件: {output_path}")

        # 创建ZIP文件
        with zipfile.ZipFile(output_path, 'w',
                             compression=zipfile.ZIP_DEFLATED,
                             compresslevel=self.compression_level) as zip_file:

            # 如果源路径是目录，则递归添加所有文件
            if os.path.isdir(source_path):
                base_dir = os.path.basename(os.path.normpath(source_path))

                for root, dirs, files in os.walk(source_path):
                    # 过滤隐藏文件和目录
                    if not self.include_hidden:
                        dirs[:] = [d for d in dirs if not d.startswith('.')]
                        files = [f for f in files if not f.startswith('.')]

                    # 过滤排除的文件模式
                    for pattern in self.exclude_patterns:
                        import fnmatch
                        files = [f for f in files if not fnmatch.fnmatch(f, pattern)]

                    # 创建目录项
                    rel_dir = os.path.relpath(root, os.path.dirname(source_path))
                    if rel_dir != '.':
                        zip_dir = os.path.join(base_dir, rel_dir)
                        zip_file.write(root, zip_dir)

                    # 添加文件
                    for file in files:
                        file_path = os.path.join(root, file)

                        try:
                            # 计算文件在ZIP中的路径
                            if rel_dir == '.':
                                zip_path = os.path.join(base_dir, file)
                            else:
                                zip_path = os.path.join(base_dir, rel_dir, file)

                            # 添加文件到ZIP
                            zip_file.write(file_path, zip_path)

                            # 更新统计信息
                            file_size = os.path.getsize(file_path)
                            self.stats["files_processed"] += 1
                            self.stats["total_size_before"] += file_size

                        except Exception as e:
                            logger.error(f"添加文件 {file_path} 到ZIP时出错: {e}")
                            self.stats["errors"] += 1
                            self.stats["skipped_files"] += 1
            else:
                # 源路径是单个文件
                try:
                    zip_file.write(source_path, os.path.basename(source_path))

                    # 更新统计信息
                    file_size = os.path.getsize(source_path)
                    self.stats["files_processed"] += 1
                    self.stats["total_size_before"] += file_size

                except Exception as e:
                    logger.error(f"添加文件 {source_path} 到ZIP时出错: {e}")
                    self.stats["errors"] += 1

    def _compress_tar(self, source_path: str, output_path: str) -> None:
        """使用TAR格式（可选GZIP或BZIP2压缩）压缩文件或目录"""
        # 根据格式选择打开模式
        if self.format == CompressFormat.TAR:
            mode = 'w'
        elif self.format == CompressFormat.TAR_GZ:
            mode = 'w:gz'
        elif self.format == CompressFormat.TAR_BZ2:
            mode = 'w:bz2'
        else:
            raise ValueError(f"不支持的TAR压缩格式: {self.format}")

        logger.info(f"正在创建{self.format.value}压缩文件: {output_path}")

        # 创建TAR文件
        with tarfile.open(output_path, mode) as tar_file:
            # 如果源路径是目录，则递归添加所有文件
            if os.path.isdir(source_path):
                base_dir = os.path.basename(os.path.normpath(source_path))

                for root, dirs, files in os.walk(source_path):
                    # 过滤隐藏文件和目录
                    if not self.include_hidden:
                        dirs[:] = [d for d in dirs if not d.startswith('.')]
                        files = [f for f in files if not f.startswith('.')]

                    # 过滤排除的文件模式
                    for pattern in self.exclude_patterns:
                        import fnmatch
                        files = [f for f in files if not fnmatch.fnmatch(f, pattern)]

                    # 添加文件
                    for file in files:
                        file_path = os.path.join(root, file)

                        try:
                            # 计算文件在TAR中的路径
                            rel_path = os.path.relpath(file_path, os.path.dirname(source_path))
                            tar_path = os.path.join(base_dir, os.path.relpath(rel_path, base_dir))

                            # 添加文件到TAR
                            tar_file.add(file_path, arcname=tar_path)

                            # 更新统计信息
                            file_size = os.path.getsize(file_path)
                            self.stats["files_processed"] += 1
                            self.stats["total_size_before"] += file_size

                        except Exception as e:
                            logger.error(f"添加文件 {file_path} 到TAR时出错: {e}")
                            self.stats["errors"] += 1
                            self.stats["skipped_files"] += 1
            else:
                # 源路径是单个文件
                try:
                    tar_file.add(source_path, arcname=os.path.basename(source_path))

                    # 更新统计信息
                    file_size = os.path.getsize(source_path)
                    self.stats["files_processed"] += 1
                    self.stats["total_size_before"] += file_size

                except Exception as e:
                    logger.error(f"添加文件 {source_path} 到TAR时出错: {e}")
                    self.stats["errors"] += 1

    def _decompress_zip(self, archive_path: str, output_dir: str,
                        flatten: bool = False, specific_files: List[str] = None) -> None:
        """解压ZIP文件"""
        with zipfile.ZipFile(archive_path, 'r') as zip_file:
            # 获取文件列表
            file_list = zip_file.namelist()

            # 如果指定了特定文件，则过滤列表
            if specific_files:
                file_list = [f for f in file_list if any(f.startswith(sf) for sf in specific_files)]

            # 提取文件
            for file in file_list:
                try:
                    # 确定输出路径
                    if flatten:
                        # 展平目录结构，只使用文件名
                        output_path = os.path.join(output_dir, os.path.basename(file))
                        # 跳过目录
                        if file.endswith('/'):
                            continue
                    else:
                        output_path = os.path.join(output_dir, file)

                    # 确保目标目录存在
                    os.makedirs(os.path.dirname(output_path), exist_ok=True)

                    # 如果是目录，只创建目录
                    if file.endswith('/'):
                        os.makedirs(output_path, exist_ok=True)
                        continue

                    # 提取文件
                    with zip_file.open(file) as source, open(output_path, 'wb') as target:
                        shutil.copyfileobj(source, target)

                    # 更新统计信息
                    self.stats["files_processed"] += 1

                except Exception as e:
                    logger.error(f"解压文件 {file} 时出错: {e}")
                    self.stats["errors"] += 1
                    self.stats["skipped_files"] += 1

    def _decompress_tar(self, archive_path: str, output_dir: str,
                        flatten: bool = False, specific_files: List[str] = None) -> None:
        """解压TAR文件（包括TAR.GZ和TAR.BZ2）"""
        with tarfile.open(archive_path, 'r:*') as tar_file:
            # 获取文件列表
            members = tar_file.getmembers()

            # 如果指定了特定文件，则过滤列表
            if specific_files:
                members = [m for m in members if any(m.name.startswith(sf) for sf in specific_files)]

            # 提取文件
            for member in members:
                try:
                    # 确定输出路径
                    if flatten:
                        # 展平目录结构，只使用文件名
                        output_path = os.path.join(output_dir, os.path.basename(member.name))
                        # 跳过目录
                        if member.isdir():
                            continue
                    else:
                        output_path = os.path.join(output_dir, member.name)

                    # 如果是目录，只创建目录
                    if member.isdir():
                        os.makedirs(output_path, exist_ok=True)
                        continue

                    # 确保目标目录存在
                    os.makedirs(os.path.dirname(output_path), exist_ok=True)

                    # 提取文件
                    with tar_file.extractfile(member) as source, open(output_path, 'wb') as target:
                        shutil.copyfileobj(source, target)

                    # 更新统计信息
                    self.stats["files_processed"] += 1

                except Exception as e:
                    logger.error(f"解压文件 {member.name} 时出错: {e}")
                    self.stats["errors"] += 1
                    self.stats["skipped_files"] += 1

    def _format_size(self, size_bytes: int) -> str:
        """将字节大小格式化为易读的字符串"""
        for unit in ['B', 'KB', 'MB', 'GB', 'TB']:
            if size_bytes < 1024.0 or unit == 'TB':
                return f"{size_bytes:.2f} {unit}"
            size_bytes /= 1024.0

    def _get_directory_size(self, directory: str) -> int:
        """计算目录的总大小（字节）"""
        total_size = 0
        for root, dirs, files in os.walk(directory):
            for file in files:
                file_path = os.path.join(root, file)
                if os.path.isfile(file_path):
                    total_size += os.path.getsize(file_path)
        return total_size

    def _get_tarfile_type(self, member: tarfile.TarInfo) -> str:
        """获取TAR文件成员的类型描述"""
        if member.isdir():
            return "目录"
        elif member.isfile():
            return "文件"
        elif member.issym():
            return "符号链接"
        elif member.islnk():
            return "硬链接"
        elif member.isfifo():
            return "管道"
        elif member.ischr():
            return "字符设备"
        elif member.isblk():
            return "块设备"
        else:
            return "未知"


def parse_arguments():
    """解析命令行参数"""
    parser = argparse.ArgumentParser(description="文件压缩/解压工具")

    # 创建互斥的操作组
    action_group = parser.add_mutually_exclusive_group(required=True)
    action_group.add_argument('-c', '--compress', action='store_true',
                              help='压缩文件或目录')
    action_group.add_argument('-d', '--decompress', action='store_true',
                              help='解压文件')
    action_group.add_argument('-l', '--list', action='store_true',
                              help='列出压缩文件内容')

    # 路径参数
    parser.add_argument('path', help='要处理的文件或目录路径')
    parser.add_argument('-o', '--output', help='输出文件或目录路径')

    # 压缩选项
    format_group = parser.add_argument_group('压缩选项')
    format_group.add_argument('-f', '--format', choices=['zip', 'tar', 'tar.gz', 'tar.bz2'],
                              default='zip', help='压缩格式（默认: zip）')
    format_group.add_argument('--level', type=int, choices=range(10), default=9,
                              help='压缩级别 0-9，9为最高压缩率（仅用于ZIP格式，默认: 9）')
    format_group.add_argument('-e', '--exclude', nargs='+',
                              help='要排除的文件模式列表（如 *.tmp *.log）')
    format_group.add_argument('--include-hidden', action='store_true',
                              help='包括隐藏文件')

    # 解压选项
    extract_group = parser.add_argument_group('解压选项')
    extract_group.add_argument('--flatten', action='store_true',
                               help='展平目录结构（所有文件直接解压到输出目录）')
    extract_group.add_argument('--files', nargs='+',
                               help='只解压指定的文件或目录')

    # 其他选项
    parser.add_argument('-v', '--verbose', action='store_true',
                        help='详细模式，显示更多信息')

    return parser.parse_args()


def main():
    """主函数"""
    args = parse_arguments()

    try:
        # 创建压缩器实例
        compressor = FileCompressor(
            format=CompressFormat(args.format) if args.compress else None,
            compression_level=args.level,
            exclude_patterns=args.exclude or [],
            include_hidden=args.include_hidden
        )

        # 执行操作
        if args.compress:
            # 压缩文件或目录
            output_path = compressor.compress(args.path, args.output)
            logger.info(f"压缩完成: {output_path}")

        elif args.decompress:
            # 解压文件
            output_dir = compressor.decompress(
                args.path,
                args.output,
                args.flatten,
                args.files
            )
            logger.info(f"解压完成: {output_dir}")

        elif args.list:
            # 列出压缩文件内容
            logger.info(f"压缩文件内容: {args.path}")
            compressor.list_contents(args.path, args.verbose)

        return 0

    except Exception as e:
        logger.error(f"操作失败: {e}")
        return 1


if __name__ == "__main__":
    sys.exit(main())
