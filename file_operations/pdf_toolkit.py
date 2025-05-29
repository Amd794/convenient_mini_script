#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
PDF工具集 - 提供PDF文件处理的多种功能

这个脚本提供了PDF文件处理的核心功能，包括拆分、合并、提取页面、添加水印、
旋转页面、添加页码等，帮助用户高效处理PDF文档。
"""

import argparse
import logging
import os
import sys
from pathlib import Path
from typing import List

try:
    from PyPDF2 import PdfReader, PdfWriter, PdfMerger, PageObject
    import PyPDF2
except ImportError:
    print("缺少必要的依赖库: PyPDF2, 请使用 'pip install PyPDF2' 安装")
    sys.exit(1)

try:
    from reportlab.pdfgen import canvas
    from reportlab.lib.pagesizes import letter, A4
    from reportlab.lib.colors import red, blue, green, black
    from reportlab.pdfbase import pdfmetrics
    from reportlab.pdfbase.ttfonts import TTFont

    REPORTLAB_AVAILABLE = True
except ImportError:
    REPORTLAB_AVAILABLE = False
    print("提示: 安装 'reportlab' 库可以启用水印和页码功能 ('pip install reportlab')")

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)
logger = logging.getLogger(__name__)


class PdfToolkit:
    """PDF工具集类，提供PDF处理的各种功能"""

    def __init__(self, output_dir: str = "./pdf_output"):
        """
        初始化PDF工具集
        
        Args:
            output_dir: 处理后PDF文件的保存目录
        """
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)

        # 检查ReportLab库可用性
        self.reportlab_available = REPORTLAB_AVAILABLE

    def split_pdf(self, input_pdf: str, output_pattern: str = "split_%d.pdf",
                  pages_per_file: int = 1) -> List[str]:
        """
        将PDF文件拆分成多个小文件
        
        Args:
            input_pdf: 输入PDF文件路径
            output_pattern: 输出PDF文件名模式，%d会被替换为序号
            pages_per_file: 每个输出文件包含的页数
            
        Returns:
            拆分后的PDF文件路径列表
        """
        try:
            reader = PdfReader(input_pdf)
            total_pages = len(reader.pages)
            output_files = []

            # 计算需要生成的文件数
            if pages_per_file <= 0:
                pages_per_file = 1
                logger.warning("每个文件的页数必须大于0，已设置为默认值1")

            file_count = (total_pages + pages_per_file - 1) // pages_per_file

            logger.info(f"开始拆分PDF: {input_pdf}")
            logger.info(f"总页数: {total_pages}, 每个文件页数: {pages_per_file}, 将生成 {file_count} 个文件")

            for i in range(file_count):
                start_page = i * pages_per_file
                end_page = min((i + 1) * pages_per_file, total_pages)

                writer = PdfWriter()

                # 添加页面到新文件
                for page_num in range(start_page, end_page):
                    writer.add_page(reader.pages[page_num])

                # 保存拆分后的文件
                output_file = self.output_dir / output_pattern.replace("%d", str(i + 1))
                with open(output_file, "wb") as f:
                    writer.write(f)

                output_files.append(str(output_file))
                logger.info(f"已创建拆分文件 {output_file} (页面 {start_page + 1}-{end_page})")

            logger.info(f"PDF拆分完成，共生成 {len(output_files)} 个文件")
            return output_files

        except Exception as e:
            logger.error(f"拆分PDF时出错: {e}")
            return []

    def merge_pdfs(self, input_files: List[str], output_file: str = "merged.pdf") -> str:
        """
        合并多个PDF文件
        
        Args:
            input_files: 输入PDF文件路径列表
            output_file: 输出的合并后PDF文件名
            
        Returns:
            合并后的PDF文件路径
        """
        try:
            merger = PdfMerger()

            logger.info(f"开始合并 {len(input_files)} 个PDF文件")

            # 检查所有输入文件是否存在
            for file_path in input_files:
                if not os.path.exists(file_path):
                    logger.error(f"文件不存在: {file_path}")
                    return ""

            # 添加所有PDF文件到合并器
            for file_path in input_files:
                try:
                    merger.append(file_path)
                    logger.debug(f"已添加文件: {file_path}")
                except Exception as e:
                    logger.error(f"添加文件 {file_path} 时出错: {e}")
                    continue

            # 保存合并后的文件
            output_path = self.output_dir / output_file
            merger.write(str(output_path))
            merger.close()

            logger.info(f"PDF合并完成，已保存为: {output_path}")
            return str(output_path)

        except Exception as e:
            logger.error(f"合并PDF时出错: {e}")
            return ""

    def extract_pages(self, input_pdf: str, page_ranges: List[str],
                      output_file: str = "extracted.pdf") -> str:
        """
        从PDF中提取指定页面
        
        Args:
            input_pdf: 输入PDF文件路径
            page_ranges: 页面范围列表，格式如 ["1-5", "8", "10-12"]
            output_file: 输出的PDF文件名
            
        Returns:
            提取页面后的PDF文件路径
        """
        try:
            reader = PdfReader(input_pdf)
            writer = PdfWriter()

            total_pages = len(reader.pages)
            logger.info(f"开始从PDF提取页面: {input_pdf} (总页数: {total_pages})")

            # 解析页面范围
            pages_to_extract = []
            for page_range in page_ranges:
                if "-" in page_range:
                    start, end = map(int, page_range.split("-"))
                    # 调整为0-索引
                    start = max(1, start) - 1
                    end = min(total_pages, end) - 1
                    pages_to_extract.extend(range(start, end + 1))
                else:
                    page = int(page_range) - 1  # 调整为0-索引
                    if 0 <= page < total_pages:
                        pages_to_extract.append(page)

            # 去重并排序
            pages_to_extract = sorted(set(pages_to_extract))

            if not pages_to_extract:
                logger.warning("没有有效的页面范围，无法提取页面")
                return ""

            logger.info(f"将提取以下页面: {', '.join(str(p + 1) for p in pages_to_extract)}")

            # 添加指定页面到新文件
            for page_num in pages_to_extract:
                writer.add_page(reader.pages[page_num])

            # 保存提取的页面
            output_path = self.output_dir / output_file
            with open(output_path, "wb") as f:
                writer.write(f)

            logger.info(f"页面提取完成，已保存为: {output_path}")
            return str(output_path)

        except Exception as e:
            logger.error(f"提取PDF页面时出错: {e}")
            return ""

    def rotate_pages(self, input_pdf: str, rotation: int, page_ranges: List[str],
                     output_file: str = "rotated.pdf") -> str:
        """
        旋转PDF中的指定页面
        
        Args:
            input_pdf: 输入PDF文件路径
            rotation: 旋转角度，必须是90的倍数
            page_ranges: 页面范围列表，格式如 ["1-5", "8", "10-12"]
            output_file: 输出的PDF文件名
            
        Returns:
            旋转页面后的PDF文件路径
        """
        try:
            # 确保旋转角度是90的倍数
            if rotation % 90 != 0:
                logger.warning(f"旋转角度必须是90的倍数，已调整为: {(rotation // 90) * 90}")
                rotation = (rotation // 90) * 90

            reader = PdfReader(input_pdf)
            writer = PdfWriter()

            total_pages = len(reader.pages)
            logger.info(f"开始旋转PDF页面: {input_pdf} (总页数: {total_pages})")

            # 解析页面范围
            pages_to_rotate = []
            for page_range in page_ranges:
                if "-" in page_range:
                    start, end = map(int, page_range.split("-"))
                    # 调整为0-索引
                    start = max(1, start) - 1
                    end = min(total_pages, end) - 1
                    pages_to_rotate.extend(range(start, end + 1))
                else:
                    page = int(page_range) - 1  # 调整为0-索引
                    if 0 <= page < total_pages:
                        pages_to_rotate.append(page)

            # 去重并排序
            pages_to_rotate = sorted(set(pages_to_rotate))

            # 处理所有页面
            for i in range(total_pages):
                page = reader.pages[i]

                # 如果页面在需要旋转的列表中，则旋转
                if i in pages_to_rotate:
                    page.rotate(rotation)
                    logger.debug(f"已旋转第 {i + 1} 页，角度: {rotation}°")

                writer.add_page(page)

            # 保存旋转后的文件
            output_path = self.output_dir / output_file
            with open(output_path, "wb") as f:
                writer.write(f)

            logger.info(f"页面旋转完成，已保存为: {output_path}")
            return str(output_path)

        except Exception as e:
            logger.error(f"旋转PDF页面时出错: {e}")
            return ""

    def add_watermark(self, input_pdf: str, watermark_text: str,
                      output_file: str = "watermarked.pdf",
                      color: str = "gray", opacity: float = 0.3,
                      angle: int = 45, size: int = 40) -> str:
        """
        给PDF添加文字水印
        
        Args:
            input_pdf: 输入PDF文件路径
            watermark_text: 水印文字
            output_file: 输出的PDF文件名
            color: 水印颜色，支持 red, blue, green, gray, black
            opacity: 水印透明度，0.0-1.0
            angle: 水印旋转角度
            size: 水印字体大小
            
        Returns:
            添加水印后的PDF文件路径
        """
        if not self.reportlab_available:
            logger.error("添加水印功能需要安装 reportlab 库，请使用 'pip install reportlab' 安装")
            return ""

        try:
            from reportlab.lib.colors import Color

            reader = PdfReader(input_pdf)
            writer = PdfWriter()

            total_pages = len(reader.pages)
            logger.info(f"开始添加水印: {input_pdf} (总页数: {total_pages})")

            # 创建临时水印PDF
            watermark_file = self.output_dir / "_temp_watermark.pdf"

            # 设置水印颜色
            colors = {
                "red": red,
                "blue": blue,
                "green": green,
                "black": black,
                "gray": Color(0.5, 0.5, 0.5, alpha=opacity)
            }
            watermark_color = colors.get(color.lower(), colors["gray"])

            # 获取第一页的尺寸，用于水印页面设置
            first_page = reader.pages[0]
            page_width = float(first_page.mediabox.width)
            page_height = float(first_page.mediabox.height)

            # 创建水印
            c = canvas.Canvas(str(watermark_file), pagesize=(page_width, page_height))
            c.setFont("Helvetica", size)
            c.setFillColor(watermark_color)

            # 在页面中心添加旋转的水印
            c.saveState()
            c.translate(page_width / 2, page_height / 2)
            c.rotate(angle)
            c.drawCentredString(0, 0, watermark_text)
            c.restoreState()

            c.save()

            # 读取水印
            watermark = PdfReader(watermark_file)
            watermark_page = watermark.pages[0]

            # 将水印应用到每一页
            for i in range(total_pages):
                page = reader.pages[i]
                page.merge_page(watermark_page)
                writer.add_page(page)

            # 保存添加水印后的文件
            output_path = self.output_dir / output_file
            with open(output_path, "wb") as f:
                writer.write(f)

            # 删除临时水印文件
            try:
                os.remove(watermark_file)
            except:
                pass

            logger.info(f"水印添加完成，已保存为: {output_path}")
            return str(output_path)

        except Exception as e:
            logger.error(f"添加水印时出错: {e}")
            return ""

    def add_page_numbers(self, input_pdf: str, output_file: str = "numbered.pdf",
                         start_number: int = 1, position: str = "bottom-center",
                         format_str: str = "%d") -> str:
        """
        给PDF添加页码
        
        Args:
            input_pdf: 输入PDF文件路径
            output_file: 输出的PDF文件名
            start_number: 起始页码
            position: 页码位置，支持 bottom-center, bottom-right, bottom-left, top-center, top-right, top-left
            format_str: 页码格式，如 "第%d页", "Page %d"
            
        Returns:
            添加页码后的PDF文件路径
        """
        if not self.reportlab_available:
            logger.error("添加页码功能需要安装 reportlab 库，请使用 'pip install reportlab' 安装")
            return ""

        try:
            reader = PdfReader(input_pdf)
            writer = PdfWriter()

            total_pages = len(reader.pages)
            logger.info(f"开始添加页码: {input_pdf} (总页数: {total_pages})")

            # 位置映射
            positions = {
                "bottom-center": (0.5, 30),
                "bottom-right": (0.9, 30),
                "bottom-left": (0.1, 30),
                "top-center": (0.5, 0.9),
                "top-right": (0.9, 0.9),
                "top-left": (0.1, 0.9)
            }
            pos_x_ratio, pos_y = positions.get(position.lower(), positions["bottom-center"])

            # 为每一页添加页码
            for i in range(total_pages):
                page = reader.pages[i]
                page_width = float(page.mediabox.width)
                page_height = float(page.mediabox.height)

                # 创建临时页码PDF
                page_num_file = self.output_dir / f"_temp_page_num_{i}.pdf"
                c = canvas.Canvas(str(page_num_file), pagesize=(page_width, page_height))
                c.setFont("Helvetica", 10)

                # 格式化页码
                page_num = format_str % (i + start_number)

                # 计算页码位置
                pos_x = page_width * pos_x_ratio

                if "top" in position.lower():
                    pos_y_actual = page_height - 30
                else:
                    pos_y_actual = pos_y

                c.drawCentredString(pos_x, pos_y_actual, page_num)
                c.save()

                # 读取页码PDF并合并
                page_num_pdf = PdfReader(page_num_file)
                page.merge_page(page_num_pdf.pages[0])
                writer.add_page(page)

                # 删除临时文件
                try:
                    os.remove(page_num_file)
                except:
                    pass

            # 保存添加页码后的文件
            output_path = self.output_dir / output_file
            with open(output_path, "wb") as f:
                writer.write(f)

            logger.info(f"页码添加完成，已保存为: {output_path}")
            return str(output_path)

        except Exception as e:
            logger.error(f"添加页码时出错: {e}")
            return ""

    def encrypt_pdf(self, input_pdf: str, user_password: str, owner_password: str = None,
                    output_file: str = "encrypted.pdf") -> str:
        """
        加密PDF文件
        
        Args:
            input_pdf: 输入PDF文件路径
            user_password: 用户密码，用于打开文档
            owner_password: 所有者密码，用于获取完全访问权限（如果为None，则与用户密码相同）
            output_file: 输出的PDF文件名
            
        Returns:
            加密后的PDF文件路径
        """
        try:
            reader = PdfReader(input_pdf)
            writer = PdfWriter()

            # 复制所有页面
            for page in reader.pages:
                writer.add_page(page)

            # 如果没有提供所有者密码，使用用户密码
            if owner_password is None:
                owner_password = user_password

            # 加密文档
            writer.encrypt(user_password=user_password, owner_password=owner_password)

            # 保存加密后的文件
            output_path = self.output_dir / output_file
            with open(output_path, "wb") as f:
                writer.write(f)

            logger.info(f"PDF加密完成，已保存为: {output_path}")
            return str(output_path)

        except Exception as e:
            logger.error(f"加密PDF时出错: {e}")
            return ""

    def decrypt_pdf(self, input_pdf: str, password: str, output_file: str = "decrypted.pdf") -> str:
        """
        解密PDF文件
        
        Args:
            input_pdf: 输入PDF文件路径
            password: 文档密码
            output_file: 输出的PDF文件名
            
        Returns:
            解密后的PDF文件路径
        """
        try:
            reader = PdfReader(input_pdf)

            # 检查文档是否加密
            if not reader.is_encrypted:
                logger.warning(f"文档未加密，无需解密: {input_pdf}")
                # 复制文档
                output_path = self.output_dir / output_file
                with open(input_pdf, "rb") as in_file, open(output_path, "wb") as out_file:
                    out_file.write(in_file.read())
                return str(output_path)

            # 解密文档
            if reader.decrypt(password) != 1:
                logger.error(f"密码不正确，无法解密文档: {input_pdf}")
                return ""

            # 创建一个新的PDF写入器
            writer = PdfWriter()

            # 复制所有页面
            for page in reader.pages:
                writer.add_page(page)

            # 保存解密后的文件
            output_path = self.output_dir / output_file
            with open(output_path, "wb") as f:
                writer.write(f)

            logger.info(f"PDF解密完成，已保存为: {output_path}")
            return str(output_path)

        except Exception as e:
            logger.error(f"解密PDF时出错: {e}")
            return ""

    def compress_pdf(self, input_pdf: str, output_file: str = "compressed.pdf") -> str:
        """
        压缩PDF文件(简单实现，实际压缩效果有限)
        
        Args:
            input_pdf: 输入PDF文件路径
            output_file: 输出的PDF文件名
            
        Returns:
            压缩后的PDF文件路径
        """
        try:
            reader = PdfReader(input_pdf)
            writer = PdfWriter()

            # 获取原始文件大小
            original_size = os.path.getsize(input_pdf)
            logger.info(f"开始压缩PDF: {input_pdf} (原始大小: {self._format_size(original_size)})")

            # 复制所有页面并尝试移除冗余数据
            for page in reader.pages:
                writer.add_page(page)

            # 移除PDF元数据以减小体积
            writer.add_metadata({
                "/Producer": "",
                "/Creator": ""
            })

            # 保存压缩后的文件
            output_path = self.output_dir / output_file
            with open(output_path, "wb") as f:
                writer.write(f)

            # 获取压缩后文件大小
            compressed_size = os.path.getsize(output_path)
            compression_ratio = (1 - compressed_size / original_size) * 100 if original_size > 0 else 0

            logger.info(f"PDF压缩完成，已保存为: {output_path}")
            logger.info(f"压缩前: {self._format_size(original_size)}, 压缩后: {self._format_size(compressed_size)}, "
                        f"压缩率: {compression_ratio:.1f}%")

            return str(output_path)

        except Exception as e:
            logger.error(f"压缩PDF时出错: {e}")
            return ""

    def _format_size(self, size_bytes: int) -> str:
        """格式化文件大小为人类可读形式"""
        if size_bytes < 1024:
            return f"{size_bytes} B"
        elif size_bytes < 1024 * 1024:
            return f"{size_bytes / 1024:.1f} KB"
        elif size_bytes < 1024 * 1024 * 1024:
            return f"{size_bytes / (1024 * 1024):.1f} MB"
        else:
            return f"{size_bytes / (1024 * 1024 * 1024):.1f} GB"


def parse_arguments():
    """解析命令行参数"""
    parser = argparse.ArgumentParser(
        description="PDF工具集 - 提供PDF文件处理的多种功能",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
示例:
  # 拆分PDF
  python pdf_toolkit.py split input.pdf --pages-per-file 2
  
  # 合并多个PDF
  python pdf_toolkit.py merge file1.pdf file2.pdf file3.pdf
  
  # 提取特定页面
  python pdf_toolkit.py extract input.pdf --pages 1-5,8,10-12
  
  # 旋转页面
  python pdf_toolkit.py rotate input.pdf --rotation 90 --pages 1-3
  
  # 添加水印
  python pdf_toolkit.py watermark input.pdf --text "机密文件"
  
  # 添加页码
  python pdf_toolkit.py number input.pdf --format "第%d页"
  
  # 加密PDF
  python pdf_toolkit.py encrypt input.pdf --password mypassword
  
  # 解密PDF
  python pdf_toolkit.py decrypt input.pdf --password mypassword
  
  # 压缩PDF
  python pdf_toolkit.py compress input.pdf
"""
    )

    # 输出目录参数
    parser.add_argument("-o", "--output-dir", dest="output_dir", default="./pdf_output",
                        help="处理后文件的保存目录，默认为 ./pdf_output")

    # 设置日志级别
    parser.add_argument("--debug", action="store_true",
                        help="启用调试日志")

    # 创建子命令
    subparsers = parser.add_subparsers(dest="command", help="命令")

    # 拆分PDF子命令
    split_parser = subparsers.add_parser("split", help="拆分PDF文件")
    split_parser.add_argument("input_pdf", help="输入PDF文件路径")
    split_parser.add_argument("--output-pattern", dest="output_pattern", default="split_%d.pdf",
                              help="输出文件名模式，%%d会被替换为序号，默认为 split_%%d.pdf")
    split_parser.add_argument("--pages-per-file", dest="pages_per_file", type=int, default=1,
                              help="每个文件包含的页数，默认为1")

    # 合并PDF子命令
    merge_parser = subparsers.add_parser("merge", help="合并多个PDF文件")
    merge_parser.add_argument("input_pdfs", nargs="+", help="输入PDF文件路径列表")
    merge_parser.add_argument("--output", dest="output_file", default="merged.pdf",
                              help="输出文件名，默认为 merged.pdf")

    # 提取页面子命令
    extract_parser = subparsers.add_parser("extract", help="从PDF中提取页面")
    extract_parser.add_argument("input_pdf", help="输入PDF文件路径")
    extract_parser.add_argument("--pages", dest="page_ranges", required=True,
                                help="要提取的页面范围，如 1-5,8,10-12")
    extract_parser.add_argument("--output", dest="output_file", default="extracted.pdf",
                                help="输出文件名，默认为 extracted.pdf")

    # 旋转页面子命令
    rotate_parser = subparsers.add_parser("rotate", help="旋转PDF页面")
    rotate_parser.add_argument("input_pdf", help="输入PDF文件路径")
    rotate_parser.add_argument("--rotation", type=int, required=True, choices=[90, 180, 270],
                               help="旋转角度，必须是90、180或270")
    rotate_parser.add_argument("--pages", dest="page_ranges", required=True,
                               help="要旋转的页面范围，如 1-5,8,10-12")
    rotate_parser.add_argument("--output", dest="output_file", default="rotated.pdf",
                               help="输出文件名，默认为 rotated.pdf")

    # 添加水印子命令
    watermark_parser = subparsers.add_parser("watermark", help="给PDF添加水印")
    watermark_parser.add_argument("input_pdf", help="输入PDF文件路径")
    watermark_parser.add_argument("--text", dest="watermark_text", required=True,
                                  help="水印文字")
    watermark_parser.add_argument("--color", choices=["red", "blue", "green", "gray", "black"],
                                  default="gray", help="水印颜色，默认为gray")
    watermark_parser.add_argument("--opacity", type=float, default=0.3,
                                  help="水印透明度，0.0-1.0，默认为0.3")
    watermark_parser.add_argument("--angle", type=int, default=45,
                                  help="水印旋转角度，默认为45")
    watermark_parser.add_argument("--size", type=int, default=40,
                                  help="水印字体大小，默认为40")
    watermark_parser.add_argument("--output", dest="output_file", default="watermarked.pdf",
                                  help="输出文件名，默认为 watermarked.pdf")

    # 添加页码子命令
    number_parser = subparsers.add_parser("number", help="给PDF添加页码")
    number_parser.add_argument("input_pdf", help="输入PDF文件路径")
    number_parser.add_argument("--start", dest="start_number", type=int, default=1,
                               help="起始页码，默认为1")
    number_parser.add_argument("--position", choices=["bottom-center", "bottom-right", "bottom-left",
                                                      "top-center", "top-right", "top-left"],
                               default="bottom-center", help="页码位置，默认为bottom-center")
    number_parser.add_argument("--format", dest="format_str", default="%d",
                               help="页码格式，如 '第%%d页', 默认为 %%d")
    number_parser.add_argument("--output", dest="output_file", default="numbered.pdf",
                               help="输出文件名，默认为 numbered.pdf")

    # 加密PDF子命令
    encrypt_parser = subparsers.add_parser("encrypt", help="加密PDF文件")
    encrypt_parser.add_argument("input_pdf", help="输入PDF文件路径")
    encrypt_parser.add_argument("--password", required=True, help="用户密码，用于打开文档")
    encrypt_parser.add_argument("--owner-password", dest="owner_password",
                                help="所有者密码，用于获取完全访问权限（如果未指定，则与用户密码相同）")
    encrypt_parser.add_argument("--output", dest="output_file", default="encrypted.pdf",
                                help="输出文件名，默认为 encrypted.pdf")

    # 解密PDF子命令
    decrypt_parser = subparsers.add_parser("decrypt", help="解密PDF文件")
    decrypt_parser.add_argument("input_pdf", help="输入PDF文件路径")
    decrypt_parser.add_argument("--password", required=True, help="文档密码")
    decrypt_parser.add_argument("--output", dest="output_file", default="decrypted.pdf",
                                help="输出文件名，默认为 decrypted.pdf")

    # 压缩PDF子命令
    compress_parser = subparsers.add_parser("compress", help="压缩PDF文件")
    compress_parser.add_argument("input_pdf", help="输入PDF文件路径")
    compress_parser.add_argument("--output", dest="output_file", default="compressed.pdf",
                                 help="输出文件名，默认为 compressed.pdf")

    return parser.parse_args()


def main():
    """主函数"""
    args = parse_arguments()

    # 设置日志级别
    if args.debug:
        logging.getLogger().setLevel(logging.DEBUG)

    # 初始化PDF工具集
    pdf_toolkit = PdfToolkit(output_dir=args.output_dir)

    # 根据命令执行相应功能
    if args.command == "split":
        pdf_toolkit.split_pdf(
            args.input_pdf,
            args.output_pattern,
            args.pages_per_file
        )

    elif args.command == "merge":
        pdf_toolkit.merge_pdfs(
            args.input_pdfs,
            args.output_file
        )

    elif args.command == "extract":
        # 解析页面范围
        page_ranges = args.page_ranges.split(",")
        pdf_toolkit.extract_pages(
            args.input_pdf,
            page_ranges,
            args.output_file
        )

    elif args.command == "rotate":
        # 解析页面范围
        page_ranges = args.page_ranges.split(",")
        pdf_toolkit.rotate_pages(
            args.input_pdf,
            args.rotation,
            page_ranges,
            args.output_file
        )

    elif args.command == "watermark":
        pdf_toolkit.add_watermark(
            args.input_pdf,
            args.watermark_text,
            args.output_file,
            args.color,
            args.opacity,
            args.angle,
            args.size
        )

    elif args.command == "number":
        pdf_toolkit.add_page_numbers(
            args.input_pdf,
            args.output_file,
            args.start_number,
            args.position,
            args.format_str
        )

    elif args.command == "encrypt":
        pdf_toolkit.encrypt_pdf(
            args.input_pdf,
            args.password,
            args.owner_password,
            args.output_file
        )

    elif args.command == "decrypt":
        pdf_toolkit.decrypt_pdf(
            args.input_pdf,
            args.password,
            args.output_file
        )

    elif args.command == "compress":
        pdf_toolkit.compress_pdf(
            args.input_pdf,
            args.output_file
        )

    else:
        logger.warning("请指定要执行的命令")
        return 1

    return 0


if __name__ == "__main__":
    try:
        sys.exit(main())
    except KeyboardInterrupt:
        logger.info("操作已被用户取消")
        sys.exit(130)  # 标准的SIGINT退出码
    except Exception as e:
        logger.critical(f"程序执行过程中发生致命错误: {e}")
        logger.debug("异常详情:", exc_info=True)
        sys.exit(1)
