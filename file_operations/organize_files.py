#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
文件整理工具

这个脚本可以自动整理指定文件夹中的文件，将它们按照文件类型分类到不同的子文件夹中。
可以帮助你快速整理杂乱的下载文件夹或桌面。
"""

import os
import shutil
import argparse
from pathlib import Path
from datetime import datetime
import logging

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)

# 文件类型分类
FILE_TYPES = {
    "图片": [".jpg", ".jpeg", ".png", ".gif", ".bmp", ".tiff", ".ico", ".webp", ".svg"],
    "文档": [".pdf", ".doc", ".docx", ".xls", ".xlsx", ".ppt", ".pptx", ".txt", ".md", ".rtf"],
    "音频": [".mp3", ".wav", ".flac", ".aac", ".ogg", ".wma", ".m4a"],
    "视频": [".mp4", ".avi", ".mkv", ".mov", ".wmv", ".flv", ".webm", ".m4v"],
    "压缩包": [".zip", ".rar", ".7z", ".tar", ".gz", ".bz2"],
    "代码": [".py", ".js", ".html", ".css", ".java", ".cpp", ".c", ".php", ".go", ".rs"],
    "可执行文件": [".exe", ".msi", ".bat", ".sh"],
}


def get_file_category(ext):
    """根据文件扩展名获取文件类别"""
    ext = ext.lower()
    for category, extensions in FILE_TYPES.items():
        if ext in extensions:
            return category
    return "其他"


def organize_files(directory, create_report=True, move_files=True, exclude_dirs=None, skip_hidden=True):
    """
    整理指定目录中的文件
    
    Args:
        directory (str): 要整理的目录路径
        create_report (bool): 是否创建报告文件
        move_files (bool): 是否移动文件（False则只生成报告）
        exclude_dirs (list): 要排除的目录名列表
        skip_hidden (bool): 是否跳过隐藏文件
    
    Returns:
        dict: 整理统计信息
    """
    if exclude_dirs is None:
        exclude_dirs = []
    
    # 统一转换为绝对路径
    directory = os.path.abspath(directory)
    
    if not os.path.exists(directory):
        logging.error(f"目录不存在: {directory}")
        return {}
    
    stats = {"总文件数": 0, "已处理": 0, "已跳过": 0, "分类统计": {}}
    
    # 遍历目录中的所有文件
    for root, dirs, files in os.walk(directory, topdown=True):
        # 排除指定目录
        dirs[:] = [d for d in dirs if d not in exclude_dirs and (not skip_hidden or not d.startswith('.'))]
        
        # 相对路径，用于判断是否为当前目录的直接子目录
        rel_path = os.path.relpath(root, directory)
        
        # 只处理顶层目录的文件，避免处理已经分类的子目录
        if rel_path != '.':
            continue
        
        for filename in files:
            # 跳过隐藏文件
            if skip_hidden and filename.startswith('.'):
                stats["已跳过"] += 1
                continue
                
            stats["总文件数"] += 1
            
            file_path = os.path.join(root, filename)
            file_ext = os.path.splitext(filename)[1]
            
            if not file_ext:
                category = "无扩展名"
            else:
                category = get_file_category(file_ext)
                
            # 更新统计信息
            if category not in stats["分类统计"]:
                stats["分类统计"][category] = []
            stats["分类统计"][category].append(filename)
            
            if move_files:
                # 创建分类目录
                category_dir = os.path.join(directory, category)
                if not os.path.exists(category_dir):
                    os.makedirs(category_dir)
                    
                # 移动文件到对应分类目录
                dest_path = os.path.join(category_dir, filename)
                # 处理同名文件
                if os.path.exists(dest_path):
                    name, ext = os.path.splitext(filename)
                    dest_path = os.path.join(category_dir, f"{name}_{datetime.now().strftime('%Y%m%d_%H%M%S')}{ext}")
                
                try:
                    shutil.move(file_path, dest_path)
                    stats["已处理"] += 1
                    logging.info(f"移动: {filename} -> {category}/{os.path.basename(dest_path)}")
                except Exception as e:
                    stats["已跳过"] += 1
                    logging.error(f"移动文件失败: {filename} - {str(e)}")
    
    # 生成报告
    if create_report:
        generate_report(directory, stats)
    
    return stats


def generate_report(directory, stats):
    """生成整理报告"""
    report_path = os.path.join(directory, f"整理报告_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt")
    
    with open(report_path, 'w', encoding='utf-8') as f:
        f.write("=== 文件整理报告 ===\n")
        f.write(f"整理时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
        f.write(f"目标目录: {directory}\n\n")
        
        f.write(f"总文件数: {stats['总文件数']}\n")
        f.write(f"已处理: {stats['已处理']}\n")
        f.write(f"已跳过: {stats['已跳过']}\n\n")
        
        f.write("=== 分类统计 ===\n")
        for category, files in stats["分类统计"].items():
            f.write(f"\n[{category}] - {len(files)}个文件\n")
            for filename in files:
                f.write(f"  - {filename}\n")
    
    logging.info(f"报告已生成: {report_path}")


def main():
    parser = argparse.ArgumentParser(description="文件整理工具 - 按类型整理文件")
    parser.add_argument("directory", nargs="?", default=".", help="要整理的目录路径，默认为当前目录")
    parser.add_argument("-r", "--report-only", action="store_true", help="仅生成报告，不移动文件")
    parser.add_argument("-e", "--exclude", nargs="+", default=[], help="排除的目录名列表")
    parser.add_argument("--include-hidden", action="store_true", help="包括隐藏文件")
    
    args = parser.parse_args()
    
    print(f"\n开始整理目录: {args.directory}")
    print("=" * 50)
    
    stats = organize_files(
        directory=args.directory,
        move_files=not args.report_only,
        exclude_dirs=args.exclude,
        skip_hidden=not args.include_hidden
    )
    
    print("\n整理完成!")
    print(f"共处理 {stats['总文件数']} 个文件，成功移动 {stats['已处理']} 个，跳过 {stats['已跳过']} 个")
    print("=" * 50)
    
    # 显示分类统计
    for category, files in stats["分类统计"].items():
        print(f"{category}: {len(files)}个文件")


if __name__ == "__main__":
    main() 