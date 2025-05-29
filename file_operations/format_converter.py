#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
文件格式转换工具

这个脚本提供了在不同文件格式之间进行转换的功能，
支持多种文件类型的转换，如文档、图像、音频、视频等格式的相互转换，
帮助用户在不同应用程序和平台之间共享文件。
"""

import argparse
import logging
import os
import shutil
from concurrent.futures import ThreadPoolExecutor, as_completed
from enum import Enum
from typing import List, Dict, Optional

# 设置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)
logger = logging.getLogger(__name__)


# 定义支持的文件格式类别
class FileCategory(Enum):
    """文件类别枚举"""
    DOCUMENT = "文档"
    IMAGE = "图像"
    AUDIO = "音频"
    VIDEO = "视频"
    DATA = "数据"
    OTHER = "其他"


class FormatConverter:
    """文件格式转换器类，提供不同文件格式之间的转换功能"""

    # 格式分类映射
    FORMAT_CATEGORIES = {
        FileCategory.DOCUMENT: ["pdf", "docx", "doc", "odt", "rtf", "txt", "md", "html", "tex", "epub"],
        FileCategory.IMAGE: ["jpg", "jpeg", "png", "gif", "bmp", "tiff", "webp", "svg"],
        FileCategory.AUDIO: ["mp3", "wav", "ogg", "flac", "aac"],
        FileCategory.VIDEO: ["mp4", "avi", "mkv", "mov", "webm"],
        FileCategory.DATA: ["csv", "xlsx", "xls", "ods", "json", "xml"],
        FileCategory.OTHER: []
    }

    # 格式间转换矩阵
    # 键: (源格式, 目标格式), 值: 转换方法名
    CONVERSION_MATRIX = {}

    def __init__(self,
                 quality: int = 80,
                 parallel: int = 1,
                 preserve_metadata: bool = True,
                 overwrite: bool = False):
        """
        初始化格式转换器
        
        Args:
            quality: 转换质量，用于图像和音视频转换(0-100)
            parallel: 并行处理的线程数
            preserve_metadata: 是否保留元数据
            overwrite: 是否覆盖已存在的文件
        """
        self.quality = quality
        self.parallel = max(1, parallel)
        self.preserve_metadata = preserve_metadata
        self.overwrite = overwrite

        # 转换统计信息
        self.stats = {
            "successful": 0,
            "failed": 0,
            "skipped": 0,
            "total_time": 0
        }

        # 初始化转换矩阵
        self._init_conversion_matrix()

        # 加载需要的Python库
        self.available_libraries = self._load_libraries()

        logger.debug(f"可用的转换库: {', '.join(self.available_libraries.keys())}")

    def _init_conversion_matrix(self):
        """初始化转换矩阵"""
        # 图像转换
        for src in ["jpg", "jpeg", "png", "gif", "bmp", "tiff", "webp"]:
            for dst in ["jpg", "jpeg", "png", "gif", "bmp", "tiff", "webp"]:
                if src != dst:
                    self.CONVERSION_MATRIX[(src, dst)] = "_convert_image"

        # 文档转换
        doc_formats = ["docx", "doc", "odt", "rtf", "txt", "pdf"]
        for src in doc_formats:
            for dst in doc_formats:
                if src != dst:
                    self.CONVERSION_MATRIX[(src, dst)] = "_convert_document"

        # Markdown和HTML转换
        self.CONVERSION_MATRIX[("md", "html")] = "_convert_markdown"
        self.CONVERSION_MATRIX[("html", "md")] = "_convert_markdown"
        self.CONVERSION_MATRIX[("md", "pdf")] = "_convert_markdown_to_pdf"
        self.CONVERSION_MATRIX[("md", "docx")] = "_convert_markdown_to_docx"

        # CSV和电子表格转换
        for src in ["csv", "xlsx", "xls"]:
            for dst in ["csv", "xlsx"]:
                if src != dst:
                    self.CONVERSION_MATRIX[(src, dst)] = "_convert_spreadsheet"

    def _load_libraries(self) -> Dict[str, bool]:
        """加载需要的Python库"""
        available_libraries = {}

        # 图像处理库
        try:
            from PIL import Image, ImageFilter
            available_libraries["pillow"] = True
            logger.debug("已加载Pillow库，可用于图像转换")
        except ImportError:
            available_libraries["pillow"] = False
            logger.warning("未找到Pillow库，图像转换功能受限，请使用pip install Pillow安装")

        # 文档处理库
        try:
            import pypdf
            available_libraries["pypdf"] = True
            logger.debug("已加载PyPDF库，可用于PDF处理")
        except ImportError:
            available_libraries["pypdf"] = False
            logger.warning("未找到PyPDF库，PDF转换功能受限，请使用pip install pypdf安装")

        try:
            import docx
            available_libraries["python-docx"] = True
            logger.debug("已加载python-docx库，可用于Word文档处理")
        except ImportError:
            available_libraries["python-docx"] = False
            logger.warning("未找到python-docx库，Word文档转换功能受限，请使用pip install python-docx安装")

        # Markdown处理库
        try:
            import markdown
            available_libraries["markdown"] = True
            logger.debug("已加载markdown库，可用于Markdown转HTML转换")
        except ImportError:
            available_libraries["markdown"] = False
            logger.warning("未找到markdown库，Markdown转换功能受限，请使用pip install markdown安装")

        try:
            import weasyprint
            available_libraries["weasyprint"] = True
            logger.debug("已加载WeasyPrint库，可用于HTML转PDF转换")
        except ImportError:
            available_libraries["weasyprint"] = False
            logger.warning("未找到WeasyPrint库，HTML/Markdown转PDF功能受限，请使用pip install weasyprint安装")

        # CSV和电子表格处理库
        try:
            import pandas as pd
            available_libraries["pandas"] = True
            logger.debug("已加载pandas库，可用于CSV/Excel转换")
        except ImportError:
            available_libraries["pandas"] = False
            logger.warning("未找到pandas库，CSV/Excel转换功能受限，请使用pip install pandas openpyxl安装")

        return available_libraries

    def convert_file(self, source_file: str, target_format: str, output_file: Optional[str] = None) -> Optional[str]:
        """
        转换单个文件格式
        
        Args:
            source_file: 源文件路径
            target_format: 目标格式(不含点，如'pdf'而非'.pdf')
            output_file: 输出文件路径，如果为None则自动生成
            
        Returns:
            转换后文件的路径，如果转换失败则返回None
        """
        # 检查源文件是否存在
        if not os.path.exists(source_file):
            logger.error(f"源文件不存在: {source_file}")
            self.stats["failed"] += 1
            return None

        # 获取源文件格式
        source_format = self._get_file_format(source_file).lower()
        target_format = target_format.lower()

        # 如果源格式和目标格式相同，则直接复制
        if source_format == target_format:
            logger.warning(f"源格式和目标格式相同: {source_format}，将复制文件")
            if output_file:
                shutil.copy2(source_file, output_file)
                logger.info(f"文件已复制到: {output_file}")
                return output_file
            else:
                self.stats["skipped"] += 1
                return source_file

        # 检查是否支持此转换
        conversion_key = (source_format, target_format)
        if conversion_key not in self.CONVERSION_MATRIX:
            logger.error(f"不支持从 {source_format} 到 {target_format} 的转换")
            self.stats["failed"] += 1
            return None

        # 获取转换方法
        conversion_method_name = self.CONVERSION_MATRIX[conversion_key]
        conversion_method = getattr(self, conversion_method_name)

        # 检查所需库是否可用
        required_libs = self._get_required_libraries(source_format, target_format)
        missing_libs = [lib for lib in required_libs if not self.available_libraries.get(lib)]

        if missing_libs:
            logger.error(f"缺少必要的库 {', '.join(missing_libs)} 用于 {source_format} 到 {target_format} 的转换")
            self.stats["failed"] += 1
            return None

        # 如果输出路径未指定，则自动生成
        if not output_file:
            source_base = os.path.splitext(source_file)[0]
            output_file = f"{source_base}.{target_format}"

        # 检查输出文件是否已存在
        if os.path.exists(output_file) and not self.overwrite:
            logger.warning(f"输出文件已存在: {output_file}，跳过转换")
            self.stats["skipped"] += 1
            return None

        try:
            # 执行转换
            logger.info(f"正在将 {source_file} 从 {source_format} 转换为 {target_format}")
            result = conversion_method(source_file, output_file)

            if result and os.path.exists(output_file):
                logger.info(f"转换成功: {output_file}")
                self.stats["successful"] += 1
                return output_file
            else:
                logger.error(f"转换失败: {source_file}")
                self.stats["failed"] += 1
                return None

        except Exception as e:
            logger.error(f"转换时出错: {e}")
            self.stats["failed"] += 1
            return None

    def _get_required_libraries(self, source_format: str, target_format: str) -> List[str]:
        """获取特定转换所需的Python库"""
        source_format = source_format.lower()
        target_format = target_format.lower()

        if source_format in ["jpg", "jpeg", "png", "gif", "bmp", "tiff", "webp"] and \
                target_format in ["jpg", "jpeg", "png", "gif", "bmp", "tiff", "webp"]:
            return ["pillow"]

        elif source_format in ["pdf", "docx", "doc"] and target_format in ["pdf", "txt"]:
            if source_format == "pdf":
                return ["pypdf"]
            elif source_format in ["docx", "doc"]:
                return ["python-docx"]

        elif source_format == "md" and target_format == "html":
            return ["markdown"]

        elif source_format == "html" and target_format == "md":
            return ["markdown"]

        elif (source_format == "md" or source_format == "html") and target_format == "pdf":
            return ["markdown", "weasyprint"]

        elif source_format in ["csv", "xlsx", "xls"] and target_format in ["csv", "xlsx"]:
            return ["pandas"]

        return []

    def batch_convert(self, sources: List[str], target_format: str,
                      output_dir: Optional[str] = None,
                      recursive: bool = False) -> Dict[str, str]:
        """
        批量转换文件格式
        
        Args:
            sources: 源文件或目录路径列表
            target_format: 目标格式
            output_dir: 输出目录，如果为None则输出到源文件同目录
            recursive: 是否递归处理子目录
            
        Returns:
            转换结果字典，键为源文件路径，值为输出文件路径或None(转换失败)
        """
        # 重置统计信息
        self.stats = {
            "successful": 0,
            "failed": 0,
            "skipped": 0,
            "total_time": 0
        }

        # 准备文件列表
        files_to_convert = []
        for source in sources:
            if os.path.isfile(source):
                files_to_convert.append(source)
            elif os.path.isdir(source):
                if recursive:
                    for root, _, files in os.walk(source):
                        for file in files:
                            files_to_convert.append(os.path.join(root, file))
                else:
                    for item in os.listdir(source):
                        item_path = os.path.join(source, item)
                        if os.path.isfile(item_path):
                            files_to_convert.append(item_path)
            else:
                logger.warning(f"路径不存在: {source}")

        # 如果没有文件可转换
        if not files_to_convert:
            logger.warning("没有文件需要转换")
            return {}

        # 创建输出目录（如果指定）
        if output_dir:
            os.makedirs(output_dir, exist_ok=True)

        results = {}
        import time
        start_time = time.time()

        if self.parallel <= 1:
            # 串行处理
            for file in files_to_convert:
                output_file = self._prepare_output_path(file, target_format, output_dir)
                results[file] = self.convert_file(file, target_format, output_file)
        else:
            # 并行处理
            with ThreadPoolExecutor(max_workers=self.parallel) as executor:
                future_to_file = {}
                for file in files_to_convert:
                    output_file = self._prepare_output_path(file, target_format, output_dir)
                    future = executor.submit(self.convert_file, file, target_format, output_file)
                    future_to_file[future] = file

                for future in as_completed(future_to_file):
                    file = future_to_file[future]
                    try:
                        results[file] = future.result()
                    except Exception as e:
                        logger.error(f"处理文件 {file} 时发生异常: {e}")
                        results[file] = None
                        self.stats["failed"] += 1

        # 更新总时间
        self.stats["total_time"] = time.time() - start_time

        # 输出统计信息
        self._print_stats()

        return results

    def _prepare_output_path(self, source_file: str, target_format: str,
                             output_dir: Optional[str] = None) -> str:
        """准备输出文件路径"""
        # 获取基础文件名
        base_name = os.path.splitext(os.path.basename(source_file))[0]

        # 如果指定了输出目录，则使用它
        if output_dir:
            return os.path.join(output_dir, f"{base_name}.{target_format}")
        else:
            # 否则输出到源文件所在目录
            source_dir = os.path.dirname(source_file)
            return os.path.join(source_dir, f"{base_name}.{target_format}")

    def _get_file_format(self, file_path: str) -> str:
        """获取文件格式（扩展名）"""
        return os.path.splitext(file_path)[1][1:].lower()

    def get_supported_formats(self, input_format: Optional[str] = None) -> List[str]:
        """
        获取支持的格式列表
        
        Args:
            input_format: 如果提供，则返回从该格式可转换到的目标格式列表
            
        Returns:
            支持的格式列表
        """
        # 根据当前可用的库过滤转换矩阵
        filtered_matrix = {}
        for (src, dst), method in self.CONVERSION_MATRIX.items():
            required_libs = self._get_required_libraries(src, dst)
            if not required_libs or all(self.available_libraries.get(lib) for lib in required_libs):
                filtered_matrix[(src, dst)] = method

        if input_format:
            # 返回可转换到的目标格式
            supported_targets = []
            for src, dst in filtered_matrix.keys():
                if src == input_format.lower():
                    supported_targets.append(dst)
            return sorted(supported_targets)
        else:
            # 返回所有支持的格式
            all_formats = set()
            for src, dst in filtered_matrix.keys():
                all_formats.add(src)
                all_formats.add(dst)
            return sorted(all_formats)

    def _convert_document(self, source_file: str, output_file: str) -> bool:
        """使用Python库转换文档格式"""
        source_format = self._get_file_format(source_file)
        target_format = self._get_file_format(output_file)

        # PDF转TXT
        if source_format == "pdf" and target_format == "txt":
            return self._convert_pdf_to_text(source_file, output_file)

        # DOCX转TXT
        elif source_format == "docx" and target_format == "txt":
            return self._convert_docx_to_text(source_file, output_file)

        # 其他文档转换暂不支持
        logger.warning(f"暂不支持从{source_format}到{target_format}的转换，需要外部库")
        return False

    def _convert_pdf_to_text(self, source_file: str, output_file: str) -> bool:
        """将PDF转换为文本"""
        try:
            import pypdf

            text = []
            with open(source_file, 'rb') as file:
                reader = pypdf.PdfReader(file)
                for page in reader.pages:
                    text.append(page.extract_text())

            # 写入提取的文本
            with open(output_file, 'w', encoding='utf-8') as file:
                file.write('\n\n'.join(text))

            return True

        except Exception as e:
            logger.error(f"PDF转文本出错: {e}")
            return False

    def _convert_docx_to_text(self, source_file: str, output_file: str) -> bool:
        """将DOCX转换为文本"""
        try:
            import docx

            doc = docx.Document(source_file)
            text = []
            for para in doc.paragraphs:
                text.append(para.text)

            # 写入提取的文本
            with open(output_file, 'w', encoding='utf-8') as file:
                file.write('\n\n'.join(text))

            return True

        except Exception as e:
            logger.error(f"DOCX转文本出错: {e}")
            return False

    def _convert_image(self, source_file: str, output_file: str) -> bool:
        """使用Pillow转换图像格式"""
        try:
            from PIL import Image

            # 打开源图像
            with Image.open(source_file) as img:
                # 如果不保留元数据，创建一个新的干净图像
                if not self.preserve_metadata:
                    # 创建一个新的RGB图像（如果是RGBA，则保持RGBA）
                    if img.mode == 'RGBA':
                        clean_img = Image.new('RGBA', img.size)
                    else:
                        clean_img = Image.new('RGB', img.size)
                    clean_img.paste(img)
                    img = clean_img

                # 保存为目标格式，指定质量参数（仅对JPEG和WebP等有效）
                target_format = self._get_file_format(output_file).upper()
                # 对于PNG，使用不同的压缩参数
                if target_format == "PNG":
                    img.save(output_file, format=target_format, compress_level=min(9, max(0, 10 - self.quality // 10)))
                else:
                    img.save(output_file, format=target_format, quality=self.quality)

            return True

        except Exception as e:
            logger.error(f"图像转换出错: {e}")
            return False

    def _convert_markdown(self, source_file: str, output_file: str) -> bool:
        """转换Markdown和HTML格式"""
        source_format = self._get_file_format(source_file)
        target_format = self._get_file_format(output_file)

        try:
            # MD转HTML
            if source_format == "md" and target_format == "html":
                import markdown

                with open(source_file, 'r', encoding='utf-8') as file:
                    md_content = file.read()

                html_content = markdown.markdown(
                    md_content,
                    extensions=['tables', 'fenced_code', 'codehilite']
                )

                # 添加基本的HTML结构
                html_doc = f"""<!DOCTYPE html>
<html>
<head>
    <meta charset="utf-8">
    <title>{os.path.basename(source_file)}</title>
    <style>
        body {{ font-family: Arial, sans-serif; margin: 40px; line-height: 1.6; }}
        pre {{ background: #f4f4f4; padding: 10px; border: 1px solid #ddd; overflow: auto; }}
        code {{ background: #f4f4f4; padding: 2px 4px; }}
        img {{ max-width: 100%; }}
    </style>
</head>
<body>
{html_content}
</body>
</html>
"""

                with open(output_file, 'w', encoding='utf-8') as file:
                    file.write(html_doc)

                return True

            # HTML转MD
            elif source_format == "html" and target_format == "md":
                logger.warning("HTML转MD功能需要专门的库，建议使用html2text库")
                return False

            else:
                logger.error(f"不支持的转换: {source_format} 到 {target_format}")
                return False

        except Exception as e:
            logger.error(f"Markdown/HTML转换出错: {e}")
            return False

    def _convert_markdown_to_pdf(self, source_file: str, output_file: str) -> bool:
        """使用WeasyPrint将Markdown转换为PDF"""
        try:
            import markdown
            from weasyprint import HTML

            # 先转换为HTML
            with open(source_file, 'r', encoding='utf-8') as file:
                md_content = file.read()

            html_content = markdown.markdown(
                md_content,
                extensions=['tables', 'fenced_code', 'codehilite']
            )

            # 添加基本的HTML结构和样式
            html_doc = f"""<!DOCTYPE html>
<html>
<head>
    <meta charset="utf-8">
    <title>{os.path.basename(source_file)}</title>
    <style>
        @page {{ margin: 1cm; }}
        body {{ font-family: Arial, sans-serif; margin: 0; padding: 0; line-height: 1.6; }}
        pre {{ background: #f4f4f4; padding: 10px; border: 1px solid #ddd; overflow: auto; }}
        code {{ background: #f4f4f4; padding: 2px 4px; }}
        img {{ max-width: 100%; }}
    </style>
</head>
<body>
{html_content}
</body>
</html>
"""

            # 使用WeasyPrint将HTML转换为PDF
            html = HTML(string=html_doc)
            html.write_pdf(output_file)

            return True

        except Exception as e:
            logger.error(f"Markdown转PDF出错: {e}")
            return False

    def _convert_markdown_to_docx(self, source_file: str, output_file: str) -> bool:
        """将Markdown转换为DOCX"""
        logger.warning("Markdown转DOCX功能需要专门的库，建议使用pypandoc")
        return False

    def _convert_spreadsheet(self, source_file: str, output_file: str) -> bool:
        """转换电子表格格式"""
        try:
            import pandas as pd

            source_format = self._get_file_format(source_file).lower()
            target_format = self._get_file_format(output_file).lower()

            # 读取源文件
            if source_format == 'csv':
                df = pd.read_csv(source_file)
            elif source_format in ['xlsx', 'xls']:
                df = pd.read_excel(source_file)
            else:
                logger.error(f"不支持的源格式: {source_format}")
                return False

            # 保存为目标格式
            if target_format == 'csv':
                df.to_csv(output_file, index=False)
            elif target_format == 'xlsx':
                df.to_excel(output_file, index=False)
            else:
                logger.error(f"不支持的目标格式: {target_format}")
                return False

            return True

        except Exception as e:
            logger.error(f"电子表格转换出错: {e}")
            return False

    def _print_stats(self):
        """打印转换统计信息"""
        logger.info("转换统计:")
        logger.info(f"成功: {self.stats['successful']} 文件")
        logger.info(f"失败: {self.stats['failed']} 文件")
        logger.info(f"跳过: {self.stats['skipped']} 文件")
        logger.info(f"总时间: {self.stats['total_time']:.2f} 秒")


def parse_arguments():
    """解析命令行参数"""
    parser = argparse.ArgumentParser(
        description="文件格式转换工具 - 在不同文件格式之间进行转换",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
示例:
  # 转换单个文件
  python format_converter.py document.docx -t pdf
  
  # 批量转换整个目录中的所有Excel文件为CSV
  python format_converter.py -r -f xlsx -t csv ./documents
  
  # 使用4个线程批量转换图片
  python format_converter.py -r -f jpg -t png -p 4 ./images
  
  # 列出支持转换的格式
  python format_converter.py --list-formats
  
  # 查看特定格式可以转换到哪些格式
  python format_converter.py --list-formats docx
"""
    )

    # 基本参数
    parser.add_argument("sources", nargs="*",
                        help="要转换的源文件或目录路径")
    parser.add_argument("-t", "--to", dest="target_format",
                        help="目标文件格式(如pdf, jpg等)")
    parser.add_argument("-o", "--output", dest="output",
                        help="输出文件或目录，适用于转换单个文件或指定输出目录")

    # 批量转换参数
    parser.add_argument("-f", "--from", dest="source_format",
                        help="源文件格式，用于批处理时只转换特定格式的文件")
    parser.add_argument("-r", "--recursive", action="store_true",
                        help="递归处理子目录")

    # 转换选项
    parser.add_argument("-q", "--quality", type=int, default=80,
                        help="转换质量(0-100)，影响图像和音视频转换质量")
    parser.add_argument("-p", "--parallel", type=int, default=1,
                        help="并行处理的线程数")
    parser.add_argument("--no-metadata", action="store_true",
                        help="不保留元数据")
    parser.add_argument("--overwrite", action="store_true",
                        help="覆盖已存在的文件")

    # 信息选项
    parser.add_argument("--list-formats", nargs="?", const="all",
                        help="列出支持的文件格式，可选择特定输入格式查看其支持的转换目标格式")
    parser.add_argument("-v", "--verbose", action="store_true",
                        help="输出详细日志")

    return parser.parse_args()


def main():
    """主函数"""
    args = parse_arguments()

    # 设置日志级别
    if args.verbose:
        logging.getLogger().setLevel(logging.DEBUG)

    # 创建转换器实例
    converter = FormatConverter(
        quality=args.quality,
        parallel=args.parallel,
        preserve_metadata=not args.no_metadata,
        overwrite=args.overwrite
    )

    # 如果是列出支持的格式
    if args.list_formats:
        if args.list_formats == "all":
            formats = converter.get_supported_formats()
            logger.info("支持的文件格式:")
            for category in FileCategory:
                category_formats = [fmt for fmt in formats if fmt in
                                    [f.lower() for f_list in converter.FORMAT_CATEGORIES.get(category, [])
                                     for f in (f_list if isinstance(f_list, list) else [f_list])]]
                if category_formats:
                    logger.info(f"{category.value}: {', '.join(category_formats)}")
        else:
            formats = converter.get_supported_formats(args.list_formats)
            logger.info(f"可以将 {args.list_formats} 转换为: {', '.join(formats)}")
        return

    # 检查参数
    if not args.sources:
        logger.error("请指定要转换的源文件或目录")
        return

    if not args.target_format:
        logger.error("请指定目标文件格式，使用 -t 或 --to 参数")
        return

    # 单文件转换
    if len(args.sources) == 1 and os.path.isfile(args.sources[0]) and args.output and not os.path.isdir(args.output):
        result = converter.convert_file(args.sources[0], args.target_format, args.output)
        if result:
            logger.info(f"转换成功: {result}")
        else:
            logger.error("转换失败")
    # 批量转换
    else:
        # 如果指定了源格式，先过滤文件
        filtered_sources = []
        if args.source_format:
            for source in args.sources:
                if os.path.isfile(source) and converter._get_file_format(source) == args.source_format:
                    filtered_sources.append(source)
                elif os.path.isdir(source):
                    filtered_sources.append(source)  # 目录会在批处理中进一步过滤
        else:
            filtered_sources = args.sources

        results = converter.batch_convert(
            sources=filtered_sources,
            target_format=args.target_format,
            output_dir=args.output if args.output and os.path.isdir(args.output) else None,
            recursive=args.recursive
        )

        # 统计并输出结果
        success_count = len([r for r in results.values() if r])
        fail_count = len([r for r in results.values() if r is None])
        logger.info(f"批量转换完成: 成功 {success_count} 个，失败 {fail_count} 个")


if __name__ == "__main__":
    main()
