#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
媒体文件组织器

这个脚本用于智能地组织媒体文件（照片、视频），根据文件的元数据（如日期、GPS位置等）
将它们自动分类到有意义的文件夹结构中。

功能包括:
- 按日期组织（年/月/日结构）
- 按位置组织（国家/城市/区域）
- 按事件自动分组
- 智能重命名
- 生成组织报告
"""

import argparse
import concurrent.futures
import datetime
import json
import logging
import os
import shutil
import sys
import time
from collections import defaultdict
from typing import List, Dict, Tuple, Any

try:
    from exif import Image as ExifImage

    HAVE_EXIF = True
except ImportError:
    HAVE_EXIF = False

try:
    import piexif

    HAVE_PIEXIF = True
except ImportError:
    HAVE_PIEXIF = False

try:
    from PIL import Image
    import PIL.ExifTags

    HAVE_PIL = True
except ImportError:
    HAVE_PIL = False

try:
    import hachoir.parser
    import hachoir.metadata

    HAVE_HACHOIR = True
except ImportError:
    HAVE_HACHOIR = False

try:
    import geopy
    from geopy.geocoders import Nominatim

    HAVE_GEOPY = True
except ImportError:
    HAVE_GEOPY = False

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)

logger = logging.getLogger(__name__)

# 支持的文件类型
IMAGE_EXTENSIONS = {'.jpg', '.jpeg', '.png', '.gif', '.bmp', '.tiff', '.webp', '.heic', '.heif'}
VIDEO_EXTENSIONS = {'.mp4', '.mov', '.avi', '.wmv', '.mkv', '.webm', '.m4v', '.3gp', '.flv'}
RAW_IMAGE_EXTENSIONS = {'.raw', '.arw', '.cr2', '.nef', '.orf', '.rw2', '.dng'}

ALL_SUPPORTED_EXTENSIONS = IMAGE_EXTENSIONS | VIDEO_EXTENSIONS | RAW_IMAGE_EXTENSIONS


class MediaOrganizer:
    """媒体文件组织器类"""

    def __init__(self, input_dir: str, output_dir: str = None, organization_type: str = 'date',
                 recursive: bool = True, dry_run: bool = False, rename_template: str = None,
                 copy_files: bool = False, max_workers: int = 4,
                 create_event_folders: bool = False, min_files_per_event: int = 5,
                 event_time_gap: int = 3600, geo_db_path: str = None,
                 file_types: List[str] = None):
        """
        初始化媒体文件组织器
        
        Args:
            input_dir: 输入目录路径
            output_dir: 输出目录路径，如果不指定则使用重命名模式
            organization_type: 组织类型，'date'|'location'|'event'|'flat'
            recursive: 是否递归处理子目录
            dry_run: 预览模式，不实际移动文件
            rename_template: 重命名模板，例如 '{date}_{counter}'
            copy_files: 是否复制而不是移动文件
            max_workers: 最大并行工作线程数
            create_event_folders: 是否创建事件文件夹
            min_files_per_event: 每个事件至少需要的文件数
            event_time_gap: 定义事件的时间间隔（秒）
            geo_db_path: 地理位置数据库路径
            file_types: 要处理的文件类型列表，例如 ['image', 'video', 'raw']
        """
        self.input_dir = os.path.abspath(input_dir)
        self.output_dir = os.path.abspath(output_dir) if output_dir else None
        self.organization_type = organization_type
        self.recursive = recursive
        self.dry_run = dry_run
        self.rename_template = rename_template
        self.copy_files = copy_files
        self.max_workers = max_workers
        self.create_event_folders = create_event_folders
        self.min_files_per_event = min_files_per_event
        self.event_time_gap = event_time_gap
        self.geo_db_path = geo_db_path

        # 文件类型过滤
        self.file_types = set()
        if file_types:
            if 'image' in file_types:
                self.file_types |= IMAGE_EXTENSIONS
            if 'video' in file_types:
                self.file_types |= VIDEO_EXTENSIONS
            if 'raw' in file_types:
                self.file_types |= RAW_IMAGE_EXTENSIONS
        else:
            self.file_types = ALL_SUPPORTED_EXTENSIONS

        # 初始化地理位置编码器
        self.geocoder = None
        if HAVE_GEOPY and self.organization_type == 'location':
            try:
                self.geocoder = Nominatim(user_agent="media_organizer")
                logger.info("已初始化地理位置编码器")
            except Exception as e:
                logger.warning(f"初始化地理位置编码器失败: {e}")

        # 统计信息
        self.stats = {
            'processed': 0,
            'moved': 0,
            'skipped': 0,
            'errors': 0,
            'no_metadata': 0,
            'by_extension': defaultdict(int),
            'by_year': defaultdict(int),
            'by_location': defaultdict(int)
        }

        # 文件计数器（用于重命名）
        self.file_counters = defaultdict(int)

        # 位置缓存
        self.location_cache = {}

    def scan_media_files(self) -> List[str]:
        """
        扫描指定目录下的媒体文件
        
        Returns:
            媒体文件路径列表
        """
        media_files = []

        if self.recursive:
            for root, _, files in os.walk(self.input_dir):
                for file in files:
                    file_path = os.path.join(root, file)
                    file_ext = os.path.splitext(file_path)[1].lower()
                    if file_ext in self.file_types:
                        media_files.append(file_path)
                        self.stats['by_extension'][file_ext] += 1
        else:
            for file in os.listdir(self.input_dir):
                file_path = os.path.join(self.input_dir, file)
                if os.path.isfile(file_path):
                    file_ext = os.path.splitext(file_path)[1].lower()
                    if file_ext in self.file_types:
                        media_files.append(file_path)
                        self.stats['by_extension'][file_ext] += 1

        logger.info(f"找到 {len(media_files)} 个媒体文件")
        return media_files

    def extract_metadata(self, file_path: str) -> Dict[str, Any]:
        """
        从媒体文件中提取元数据
        
        Args:
            file_path: 文件路径
            
        Returns:
            包含元数据的字典
        """
        metadata = {
            'date_taken': None,
            'gps_lat': None,
            'gps_lon': None,
            'location': None,
            'camera_make': None,
            'camera_model': None
        }

        file_ext = os.path.splitext(file_path)[1].lower()

        # 使用文件修改时间作为后备
        try:
            file_mtime = os.path.getmtime(file_path)
            metadata['date_taken'] = datetime.datetime.fromtimestamp(file_mtime)
        except Exception:
            pass

        # 对于图片文件，尝试读取EXIF数据
        if file_ext in IMAGE_EXTENSIONS:
            # 尝试使用exif库
            if HAVE_EXIF:
                try:
                    with open(file_path, 'rb') as f:
                        exif_image = ExifImage(f)

                    # 提取拍摄日期
                    if hasattr(exif_image, 'datetime_original'):
                        date_str = exif_image.datetime_original
                        metadata['date_taken'] = datetime.datetime.strptime(date_str, '%Y:%m:%d %H:%M:%S')

                    # 提取GPS信息
                    if hasattr(exif_image, 'gps_latitude') and hasattr(exif_image, 'gps_longitude'):
                        metadata['gps_lat'] = float(exif_image.gps_latitude[0]) + \
                                              float(exif_image.gps_latitude[1]) / 60 + \
                                              float(exif_image.gps_latitude[2]) / 3600

                        metadata['gps_lon'] = float(exif_image.gps_longitude[0]) + \
                                              float(exif_image.gps_longitude[1]) / 60 + \
                                              float(exif_image.gps_longitude[2]) / 3600

                        # 处理南纬和西经
                        if hasattr(exif_image, 'gps_latitude_ref') and exif_image.gps_latitude_ref == 'S':
                            metadata['gps_lat'] = -metadata['gps_lat']

                        if hasattr(exif_image, 'gps_longitude_ref') and exif_image.gps_longitude_ref == 'W':
                            metadata['gps_lon'] = -metadata['gps_lon']

                    # 提取相机信息
                    if hasattr(exif_image, 'make'):
                        metadata['camera_make'] = exif_image.make

                    if hasattr(exif_image, 'model'):
                        metadata['camera_model'] = exif_image.model
                except Exception as e:
                    logger.debug(f"使用exif库提取元数据失败: {file_path}, 错误: {e}")

            # 如果exif库失败，尝试使用PIL
            if HAVE_PIL and metadata['date_taken'] is None:
                try:
                    with Image.open(file_path) as img:
                        exif_data = img._getexif()
                        if exif_data:
                            # 提取拍摄日期
                            if 36867 in exif_data:  # EXIF日期时间原始值的标签
                                date_str = exif_data[36867]
                                metadata['date_taken'] = datetime.datetime.strptime(date_str, '%Y:%m:%d %H:%M:%S')

                            # 提取GPS信息
                            if 34853 in exif_data:  # GPS信息标签
                                gps_info = exif_data[34853]

                                if 2 in gps_info and 4 in gps_info:  # 纬度和经度值
                                    lat = gps_info[2]
                                    lon = gps_info[4]

                                    # 计算度分秒到十进制度
                                    metadata['gps_lat'] = float(lat[0]) + float(lat[1]) / 60 + float(lat[2]) / 3600
                                    metadata['gps_lon'] = float(lon[0]) + float(lon[1]) / 60 + float(lon[2]) / 3600

                                    # 处理南纬和西经
                                    if 1 in gps_info and gps_info[1] == 'S':  # 纬度参考
                                        metadata['gps_lat'] = -metadata['gps_lat']

                                    if 3 in gps_info and gps_info[3] == 'W':  # 经度参考
                                        metadata['gps_lon'] = -metadata['gps_lon']

                            # 提取相机信息
                            if 271 in exif_data:  # 制造商标签
                                metadata['camera_make'] = exif_data[271]

                            if 272 in exif_data:  # 型号标签
                                metadata['camera_model'] = exif_data[272]
                except Exception as e:
                    logger.debug(f"使用PIL提取元数据失败: {file_path}, 错误: {e}")

        # 对于视频文件，尝试使用hachoir
        elif file_ext in VIDEO_EXTENSIONS and HAVE_HACHOIR:
            try:
                parser = hachoir.parser.createParser(file_path)
                if parser:
                    metadata_extractor = hachoir.metadata.extractMetadata(parser)
                    if metadata_extractor:
                        # 提取创建日期
                        if metadata_extractor.has('creation_date'):
                            metadata['date_taken'] = metadata_extractor.get('creation_date')

                        # 提取GPS信息 (如果有)
                        if metadata_extractor.has('latitude') and metadata_extractor.has('longitude'):
                            metadata['gps_lat'] = float(metadata_extractor.get('latitude'))
                            metadata['gps_lon'] = float(metadata_extractor.get('longitude'))

                        # 提取设备信息
                        if metadata_extractor.has('producer'):
                            metadata['camera_make'] = metadata_extractor.get('producer')

                        if metadata_extractor.has('model'):
                            metadata['camera_model'] = metadata_extractor.get('model')
            except Exception as e:
                logger.debug(f"使用hachoir提取视频元数据失败: {file_path}, 错误: {e}")

        # 如果有GPS坐标，尝试获取位置信息
        if metadata['gps_lat'] is not None and metadata['gps_lon'] is not None and self.geocoder:
            cache_key = f"{metadata['gps_lat']:.5f},{metadata['gps_lon']:.5f}"
            if cache_key in self.location_cache:
                metadata['location'] = self.location_cache[cache_key]
            else:
                try:
                    location = self.geocoder.reverse((metadata['gps_lat'], metadata['gps_lon']), language='zh')
                    if location:
                        address = location.raw.get('address', {})
                        country = address.get('country', 'Unknown')
                        city = address.get('city', address.get('town', address.get('county', 'Unknown')))
                        district = address.get('suburb', address.get('district', 'Unknown'))

                        metadata['location'] = {
                            'country': country,
                            'city': city,
                            'district': district,
                            'address': location.address
                        }

                        # 缓存位置信息
                        self.location_cache[cache_key] = metadata['location']
                except Exception as e:
                    logger.debug(f"地理编码失败: {e}")

        return metadata

    def get_destination_path(self, file_path: str, metadata: Dict[str, Any]) -> str:
        """
        根据元数据和组织类型确定目标路径
        
        Args:
            file_path: 源文件路径
            metadata: 元数据信息
            
        Returns:
            目标文件路径
        """
        # 提取文件名和扩展名
        file_name = os.path.basename(file_path)
        file_base, file_ext = os.path.splitext(file_name)

        # 无法提取日期时使用文件修改日期
        if metadata['date_taken'] is None:
            file_mtime = os.path.getmtime(file_path)
            date_taken = datetime.datetime.fromtimestamp(file_mtime)
        else:
            date_taken = metadata['date_taken']

        # 根据组织类型确定目录结构
        if self.organization_type == 'date':
            rel_dir = os.path.join(
                str(date_taken.year),
                f"{date_taken.month:02d}",
                f"{date_taken.day:02d}"
            )
            self.stats['by_year'][str(date_taken.year)] += 1

        elif self.organization_type == 'location':
            if metadata['location']:
                country = str(metadata['location']['country'])
                city = str(metadata['location']['city'])
                district = str(metadata['location']['district'])
                rel_dir = os.path.join(country, city, district)
                self.stats['by_location'][country] += 1
            else:
                rel_dir = "Unknown_Location"
                self.stats['by_location']['Unknown'] += 1

        elif self.organization_type == 'event':
            # 使用日期作为基础目录
            event_date = f"{date_taken.year}-{date_taken.month:02d}-{date_taken.day:02d}"
            rel_dir = event_date
            self.stats['by_year'][str(date_taken.year)] += 1

        else:  # 'flat'组织模式
            rel_dir = ""
            self.stats['by_year'][str(date_taken.year)] += 1

        # 构建新文件名
        if self.rename_template:
            # 日期格式化
            date_str = date_taken.strftime("%Y%m%d_%H%M%S")

            # 相机信息格式化
            camera = "unknown"
            if metadata['camera_make'] and metadata['camera_model']:
                camera = f"{metadata['camera_make']}_{metadata['camera_model']}".replace(" ", "_")
            elif metadata['camera_make']:
                camera = metadata['camera_make'].replace(" ", "_")
            elif metadata['camera_model']:
                camera = metadata['camera_model'].replace(" ", "_")

            # 位置信息格式化
            location = "unknown"
            if metadata['location'] and metadata['location'].get('city'):
                location = metadata['location']['city'].replace(" ", "_")

            # 创建计数器键
            counter_key = f"{date_taken.year}{date_taken.month:02d}{date_taken.day:02d}"
            self.file_counters[counter_key] += 1
            counter = self.file_counters[counter_key]

            # 应用模板
            new_file_name = self.rename_template.format(
                date=date_str,
                year=date_taken.year,
                month=f"{date_taken.month:02d}",
                day=f"{date_taken.day:02d}",
                hour=f"{date_taken.hour:02d}",
                minute=f"{date_taken.minute:02d}",
                second=f"{date_taken.second:02d}",
                camera=camera,
                location=location,
                counter=f"{counter:04d}",
                original=file_base
            )
            new_file_name = f"{new_file_name}{file_ext}"
        else:
            new_file_name = file_name

        # 构建完整目标路径
        if self.output_dir:
            dest_dir = os.path.join(str(self.output_dir), str(rel_dir))
            dest_path = os.path.join(str(dest_dir), str(new_file_name))
        else:
            dest_dir = os.path.join(str(os.path.dirname(file_path)), str(rel_dir))
            dest_path = os.path.join(str(dest_dir), str(new_file_name))

        return dest_path

    def process_file(self, file_path: str) -> tuple[str, bool] | tuple[None, bool]:
        """
        处理单个媒体文件
        
        Args:
            file_path: 文件路径
            
        Returns:
            (目标路径, 是否成功)
        """
        try:
            # 提取元数据
            metadata = self.extract_metadata(file_path)

            if not metadata['date_taken']:
                logger.warning(f"无法从文件获取日期: {file_path}")
                self.stats['no_metadata'] += 1

            # 获取目标路径
            dest_path = self.get_destination_path(file_path, metadata)
            dest_dir = os.path.dirname(dest_path)

            # 创建目标目录
            if not self.dry_run and dest_dir:
                os.makedirs(dest_dir, exist_ok=True)

            # 如果文件已经存在，添加计数后缀
            if os.path.exists(dest_path) and file_path != dest_path:
                file_base, file_ext = os.path.splitext(dest_path)
                counter = 1
                while os.path.exists(f"{file_base}_{counter}{file_ext}"):
                    counter += 1
                dest_path = f"{file_base}_{counter}{file_ext}"

            # 移动或复制文件
            if not self.dry_run:
                if file_path != dest_path:
                    if self.copy_files:
                        shutil.copy2(file_path, dest_path)
                        logger.debug(f"已复制: {file_path} -> {dest_path}")
                    else:
                        shutil.move(file_path, dest_path)
                        logger.debug(f"已移动: {file_path} -> {dest_path}")

                    self.stats['moved'] += 1
                else:
                    logger.debug(f"文件不需要移动: {file_path}")
                    self.stats['skipped'] += 1
            else:
                # 在预览模式下模拟操作
                if file_path != dest_path:
                    logger.info(f"[DRY RUN] 将{'复制' if self.copy_files else '移动'}: {file_path} -> {dest_path}")
                    self.stats['moved'] += 1
                else:
                    logger.debug(f"[DRY RUN] 文件不需要移动: {file_path}")
                    self.stats['skipped'] += 1

            return dest_path, True

        except Exception as e:
            logger.error(f"处理文件时出错: {file_path}, 错误: {e}")
            self.stats['errors'] += 1
            return None, False

    def organize_files(self) -> Dict[str, Any]:
        """
        组织媒体文件
        
        Returns:
            包含处理结果统计的字典
        """
        start_time = time.time()

        # 扫描媒体文件
        media_files = self.scan_media_files()
        self.stats['total'] = len(media_files)

        if not media_files:
            logger.info("未找到媒体文件")
            return self.stats

        # 使用线程池处理文件
        processed_files = []
        with concurrent.futures.ThreadPoolExecutor(max_workers=self.max_workers) as executor:
            future_to_file = {executor.submit(self.process_file, file): file for file in media_files}

            for i, future in enumerate(concurrent.futures.as_completed(future_to_file)):
                file = future_to_file[future]
                try:
                    dest_path, success = future.result()
                    processed_files.append((file, dest_path, success))

                    # 更新进度
                    self.stats['processed'] += 1
                    if i % 10 == 0 or i == len(media_files) - 1:
                        progress = (i + 1) / len(media_files) * 100
                        logger.info(f"进度: {progress:.1f}% ({i + 1}/{len(media_files)})")

                except Exception as e:
                    logger.error(f"处理文件时出错: {file}, 错误: {e}")
                    self.stats['errors'] += 1

        # 如果需要创建事件文件夹，对已处理的文件进行事件分组
        if self.organization_type == 'event' and self.create_event_folders and not self.dry_run:
            logger.info("创建事件文件夹...")
            self._create_event_folders(processed_files)

        # 记录统计信息
        end_time = time.time()
        self.stats['duration'] = end_time - start_time

        # 显示统计信息
        logger.info("=========== 处理完成 ===========")
        logger.info(f"总计处理: {self.stats['processed']} 个文件")
        logger.info(f"移动/复制: {self.stats['moved']} 个文件")
        logger.info(f"跳过: {self.stats['skipped']} 个文件")
        logger.info(f"错误: {self.stats['errors']} 个文件")
        logger.info(f"无元数据: {self.stats['no_metadata']} 个文件")
        logger.info(f"用时: {self.stats['duration']:.1f} 秒")

        return self.stats

    def _create_event_folders(self, processed_files: List[Tuple[str, str, bool]]):
        """
        基于时间间隔创建事件文件夹
        
        Args:
            processed_files: 处理过的文件列表(源路径, 目标路径, 成功标志)
        """
        # 首先按日期分组文件
        files_by_date = defaultdict(list)
        for _, dest_path, success in processed_files:
            if success and dest_path:
                date_dir = os.path.dirname(dest_path)
                files_by_date[date_dir].append(dest_path)

        # 对每个日期目录分析事件
        for date_dir, files in files_by_date.items():
            if len(files) < self.min_files_per_event:
                continue

            # 获取每个文件的时间戳
            file_timestamps = []
            for file_path in files:
                try:
                    metadata = self.extract_metadata(file_path)
                    if metadata['date_taken']:
                        timestamp = int(metadata['date_taken'].timestamp())
                        file_timestamps.append((file_path, timestamp))
                except Exception as e:
                    logger.debug(f"无法获取文件时间戳: {file_path}, 错误: {e}")

            # 按时间排序
            file_timestamps.sort(key=lambda x: x[1])

            if not file_timestamps:
                continue

            # 分析时间间隔，识别事件边界
            events = []
            current_event = [file_timestamps[0]]

            for i in range(1, len(file_timestamps)):
                curr_file, curr_time = file_timestamps[i]
                prev_time = file_timestamps[i - 1][1]

                # 如果时间间隔超过阈值，认为是新事件
                if curr_time - prev_time > self.event_time_gap:
                    if len(current_event) >= self.min_files_per_event:
                        events.append(current_event)
                    current_event = [(curr_file, curr_time)]
                else:
                    current_event.append((curr_file, curr_time))

            # 添加最后一个事件
            if len(current_event) >= self.min_files_per_event:
                events.append(current_event)

            # 创建事件文件夹并移动文件
            for event_index, event_files in enumerate(events, 1):
                # 创建事件文件夹
                event_date = datetime.datetime.fromtimestamp(event_files[0][1])
                event_start_time = datetime.datetime.fromtimestamp(event_files[0][1]).strftime('%H%M')
                event_end_time = datetime.datetime.fromtimestamp(event_files[-1][1]).strftime('%H%M')
                event_dir_name = f"事件_{event_index:02d}_{event_start_time}-{event_end_time}"
                event_dir = os.path.join(date_dir, event_dir_name)

                try:
                    os.makedirs(event_dir, exist_ok=True)

                    # 移动文件
                    for file_path, _ in event_files:
                        file_name = os.path.basename(file_path)
                        dest_path = os.path.join(event_dir, file_name)

                        # 如果目标路径已存在，添加计数
                        if os.path.exists(dest_path):
                            file_base, file_ext = os.path.splitext(dest_path)
                            counter = 1
                            while os.path.exists(f"{file_base}_{counter}{file_ext}"):
                                counter += 1
                            dest_path = f"{file_base}_{counter}{file_ext}"

                        shutil.move(file_path, dest_path)
                        logger.debug(f"移动到事件文件夹: {file_path} -> {dest_path}")
                except Exception as e:
                    logger.error(f"创建事件文件夹失败: {event_dir}, 错误: {e}")

    def generate_report(self, report_path: str = None):
        """
        生成处理报告

        Args:
            report_path: 报告文件路径
        """
        # 创建报告内容
        report = {
            "统计信息": {
                "总文件数": self.stats.get('total', 0),
                "处理文件数": self.stats['processed'],
                "移动/复制文件数": self.stats['moved'],
                "跳过文件数": self.stats['skipped'],
                "错误文件数": self.stats['errors'],
                "无元数据文件数": self.stats['no_metadata'],
                "处理时间(秒)": round(self.stats.get('duration', 0), 2)
            },
            "文件类型统计": dict(self.stats['by_extension']),
            "年份统计": dict(self.stats['by_year'])
        }

        if self.organization_type == 'location':
            report["位置统计"] = dict(self.stats['by_location'])

        # 如果提供了报告路径，则写入文件
        if report_path:
            try:
                with open(report_path, 'w', encoding='utf-8') as f:
                    json.dump(report, f, ensure_ascii=False, indent=4)
                logger.info(f"报告已保存至: {report_path}")
            except Exception as e:
                logger.error(f"保存报告失败: {e}")

        return report


def parse_arguments():
    """解析命令行参数"""
    parser = argparse.ArgumentParser(description="媒体文件组织器 - 根据日期、位置等信息组织照片和视频")

    parser.add_argument('input_dir', help="要处理的输入目录")
    parser.add_argument('-o', '--output-dir', help="输出目录，默认将在原位置组织")
    parser.add_argument('-t', '--type', choices=['date', 'location', 'event', 'flat'],
                        default='date', help="组织类型: date(按日期), location(按位置), event(按事件), flat(平坦结构)")
    parser.add_argument('-r', '--recursive', action='store_true', help="递归处理子目录")
    parser.add_argument('--rename',
                        help="重命名模板，例如: '{date}_{counter}'. 可用变量: {date}, {year}, {month}, {day}, {hour}, {minute}, {second}, {camera}, {location}, {counter}, {original}")
    parser.add_argument('--copy', action='store_true', help="复制而不是移动文件")
    parser.add_argument('--dry-run', action='store_true', help="预览模式，不实际移动文件")
    parser.add_argument('--file-types', choices=['image', 'video', 'raw'], nargs='+', help="要处理的文件类型")
    parser.add_argument('--events', action='store_true', help="创建事件文件夹")
    parser.add_argument('--event-gap', type=int, default=3600, help="定义事件的时间间隔(秒)")
    parser.add_argument('--min-event-files', type=int, default=5, help="每个事件的最小文件数量")
    parser.add_argument('--threads', type=int, default=4, help="并行处理的线程数")
    parser.add_argument('--report', help="生成报告文件路径")
    parser.add_argument('-v', '--verbose', action='store_true', help="详细输出模式")
    parser.add_argument('--debug', action='store_true', help="调试模式")

    return parser.parse_args()


def check_dependencies():
    """检查依赖库"""
    missing = []

    if not HAVE_PIL:
        missing.append("PIL (使用 'pip install pillow' 安装)")

    if not HAVE_EXIF:
        missing.append("exif (使用 'pip install exif' 安装)")

    if not HAVE_HACHOIR:
        missing.append("hachoir (使用 'pip install hachoir' 安装)")

    if not HAVE_GEOPY:
        missing.append("geopy (使用 'pip install geopy' 安装)")

    return missing


def main():
    """主函数"""
    args = parse_arguments()

    # 配置日志级别
    if args.debug:
        logger.setLevel(logging.DEBUG)
    elif args.verbose:
        logger.setLevel(logging.INFO)
    else:
        logger.setLevel(logging.WARNING)

    # 检查依赖
    missing_deps = check_dependencies()
    if missing_deps:
        logger.warning("以下依赖库缺失，某些功能可能不可用:")
        for dep in missing_deps:
            logger.warning(f"  - {dep}")

    # 检查必要的参数
    if args.type == 'location' and not HAVE_GEOPY:
        logger.error("组织类型为'location'，但缺少geopy库。请安装: pip install geopy")
        return 1

    # 创建媒体组织器实例
    organizer = MediaOrganizer(
        input_dir=args.input_dir,
        output_dir=args.output_dir,
        organization_type=args.type,
        recursive=args.recursive,
        dry_run=args.dry_run,
        rename_template=args.rename,
        copy_files=args.copy,
        max_workers=args.threads,
        create_event_folders=args.events,
        min_files_per_event=args.min_event_files,
        event_time_gap=args.event_gap,
        file_types=args.file_types
    )

    # 组织文件
    stats = organizer.organize_files()

    # 生成报告
    if args.report:
        organizer.generate_report(args.report)

    return 0


if __name__ == "__main__":
    sys.exit(main())
