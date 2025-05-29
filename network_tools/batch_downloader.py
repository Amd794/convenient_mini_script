#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
网络文件批量下载工具

这个脚本提供了批量下载网络文件的功能，支持并发下载、断点续传、自动重试等特性，
帮助用户高效地从互联网批量下载文件资源。
"""

import argparse
import asyncio
import csv
import json
import logging
import os
import random  # 新增随机模块
import sys
import time
import traceback  # 添加跟踪异常模块
from pathlib import Path
from typing import Dict, List, Optional, Tuple
from urllib.parse import unquote, urlparse

try:
    import httpx
except ImportError:
    print("缺少必要的依赖库: httpx, 请使用 'pip install httpx' 安装")
    sys.exit(1)

try:
    from tqdm.asyncio import tqdm_asyncio
    from tqdm import tqdm

    TQDM_AVAILABLE = True
except ImportError:
    TQDM_AVAILABLE = False
    print("提示: 安装 'tqdm' 库可以获得进度显示体验 ('pip install tqdm')")

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)
logger = logging.getLogger(__name__)


class BatchDownloader:
    """批量文件下载器类"""

    def __init__(
            self,
            output_dir: str = "./downloads",
            max_workers: int = 5,
            timeout: int = 30,
            chunk_size: int = 1024 * 1024,  # 1MB
            max_retries: int = 3,
            verify_ssl: bool = True,
            headers: Optional[Dict[str, str]] = None,
            resume: bool = True,
            overwrite: bool = False,
            default_suffix: Optional[str] = None,
            force_suffix: bool = False,
            filename_map: Optional[Dict[str, str]] = None,
            random_delay: bool = False,  # 是否启用随机延时
            min_delay: float = 1.0,  # 最小延时秒数
            max_delay: float = 5.0,  # 最大延时秒数
            state_file: Optional[str] = None,  # 状态保存文件路径
            continue_from_state: bool = False  # 是否从状态文件恢复下载
    ):
        """
        初始化下载器

        Args:
            output_dir: 文件保存目录
            max_workers: 最大并发下载数
            timeout: 连接超时时间(秒)
            chunk_size: 文件下载分块大小(字节)
            max_retries: 下载失败时最大重试次数
            verify_ssl: 是否验证SSL证书
            headers: 请求头
            resume: 是否支持断点续传
            overwrite: 是否覆盖已存在的文件
            default_suffix: 默认文件后缀，当URL无法确定文件类型时使用
            force_suffix: 是否强制使用指定的文件后缀，忽略URL中的后缀
            filename_map: URL到文件名的映射字典
            random_delay: 是否启用随机延时，避免被反爬虫机制检测
            min_delay: 随机延时的最小秒数
            max_delay: 随机延时的最大秒数
            state_file: 下载状态保存文件路径
            continue_from_state: 是否从状态文件恢复下载
        """
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)

        self.max_workers = max_workers
        self.timeout = timeout
        self.chunk_size = chunk_size
        self.max_retries = max_retries
        self.verify_ssl = verify_ssl
        self.headers = headers or {}
        self.resume = resume
        self.overwrite = overwrite
        self.default_suffix = default_suffix
        self.force_suffix = force_suffix
        self.filename_map = filename_map or {}

        # 新增随机延时相关参数
        self.random_delay = random_delay
        self.min_delay = min_delay
        self.max_delay = max_delay

        # 新增状态保存相关参数
        self.state_file = state_file or os.path.join(str(self.output_dir), ".download_state.json")
        self.continue_from_state = continue_from_state

        # 域名访问冷却时间管理
        self.domain_cooldown = {}

        # 下载统计
        self.stats = {
            "successful": 0,
            "failed": 0,
            "skipped": 0,
            "total_bytes": 0,
            "start_time": 0,
            "end_time": 0,
            "completed_urls": set()  # 记录已完成的URL
        }

        # 创建客户端
        self.client = httpx.AsyncClient(
            timeout=timeout,
            follow_redirects=True,
            verify=verify_ssl
        )

        # 进度显示
        self.use_tqdm = TQDM_AVAILABLE
        # 下载进度条字典，URL映射到对应的进度条
        self.progress_bars = {}

        # 尝试加载保存的状态
        if self.continue_from_state and os.path.exists(self.state_file):
            self._load_state()

    async def __aenter__(self):
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        await self.close()
        # 清理所有进度条
        self._cleanup_progress_bars()

    async def close(self):
        """关闭HTTP客户端"""
        if self.client:
            await self.client.aclose()

    def _cleanup_progress_bars(self):
        """清理所有进度条"""
        if self.use_tqdm:
            for url, pbar in list(self.progress_bars.items()):
                try:
                    pbar.close()
                except Exception:
                    pass
            self.progress_bars.clear()

    def _create_progress_bar(self, url: str, filename: str, total_size: int) -> Optional[tqdm]:
        """创建一个新的进度条"""
        if not self.use_tqdm:
            return None

        try:
            # 确保总大小至少为1KB
            total_size = max(total_size, 1024)
            # 创建一个带有文件名的进度条
            pbar = tqdm(
                total=total_size,
                unit='B',
                unit_scale=True,
                unit_divisor=1024,
                desc=f"下载 {filename}",
                leave=True
            )
            self.progress_bars[url] = pbar
            return pbar
        except Exception as e:
            logger.warning(f"创建进度条时出错: {url}, 错误: {e}")
            return None

    def _update_progress_bar(self, url: str, n: int = 1, total: Optional[int] = None):
        """更新进度条"""
        if not self.use_tqdm or url not in self.progress_bars:
            return

        try:
            pbar = self.progress_bars[url]
            # 如果提供了新的总大小，更新进度条总大小
            if total is not None and total > 0:
                current_total = max(pbar.total, total)
                pbar.total = current_total

            # 更新进度
            pbar.update(n)
        except Exception as e:
            logger.debug(f"更新进度条时出错: {url}, 错误: {e}")

    def _close_progress_bar(self, url: str, success: bool = True):
        """关闭并移除进度条"""
        if not self.use_tqdm or url not in self.progress_bars:
            return

        try:
            pbar = self.progress_bars[url]
            # 如果成功，确保进度条显示100%
            if success and pbar.n < pbar.total:
                pbar.update(pbar.total - pbar.n)
            pbar.close()
            del self.progress_bars[url]
        except Exception as e:
            logger.debug(f"关闭进度条时出错: {url}, 错误: {e}")

    def _get_filename_from_url(self, url: str) -> str:
        """
        从URL中提取文件名
        
        如果URL在filename_map中有映射，则使用映射的文件名
        否则从URL路径提取文件名，如果无法提取则使用域名加时间戳
        """
        # 1. 先检查是否有预定义的文件名映射
        if url in self.filename_map:
            return self.filename_map[url]

        # 2. 从URL提取文件名
        parsed_url = urlparse(url)
        path = unquote(parsed_url.path)
        filename = os.path.basename(path)

        # 3. 如果URL没有明确的文件名，使用域名加时间戳
        if not filename:
            timestamp = int(time.time())
            filename = f"{parsed_url.netloc}_{timestamp}"

        # 4. 如果强制使用指定后缀，则移除原有后缀
        if self.force_suffix and self.default_suffix:
            filename = os.path.splitext(filename)[0]

        # 5. 如果有默认后缀且文件名没有后缀或强制使用后缀，添加默认后缀
        if self.default_suffix and (not os.path.splitext(filename)[1] or self.force_suffix):
            if not self.default_suffix.startswith('.'):
                filename = f"{filename}.{self.default_suffix}"
            else:
                filename = f"{filename}{self.default_suffix}"

        return filename

    def _format_bytes(self, size_bytes: int) -> str:
        """格式化字节大小为人类可读形式"""
        if size_bytes < 1024:
            return f"{size_bytes} B"
        elif size_bytes < 1024 * 1024:
            return f"{size_bytes / 1024:.1f} KB"
        elif size_bytes < 1024 * 1024 * 1024:
            return f"{size_bytes / (1024 * 1024):.1f} MB"
        else:
            return f"{size_bytes / (1024 * 1024 * 1024):.1f} GB"

    def _validate_url(self, url: str) -> bool:
        """验证URL是否有效"""
        try:
            # 基本URL格式验证
            result = urlparse(url)
            # 检查协议和域名
            if not all([result.scheme in ('http', 'https'), result.netloc]):
                logger.warning(f"无效的URL格式: {url}")
                return False

            return True
        except Exception as e:
            logger.warning(f"URL验证失败: {url}, 错误: {e}")
            return False

    async def fetch_file_size(self, url: str) -> Optional[int]:
        """获取远程文件大小"""
        try:
            # 增强请求头
            headers = self._enhance_headers(url)
            try:
                # 首先尝试HEAD请求
                response = await self.client.head(url, headers=headers, follow_redirects=True)
                response.raise_for_status()

                # 尝试从Content-Length头获取文件大小
                content_length = response.headers.get("Content-Length")
                if content_length:
                    size = int(content_length)
                    # 避免返回0，确保进度条能显示
                    return max(size, 1024)
            except Exception as head_error:
                logger.debug(f"HEAD请求获取文件大小失败: {url}, 尝试GET请求, 错误: {head_error}")

            # 如果HEAD请求失败，尝试GET请求，但只获取响应头
            try:
                async with self.client.stream("GET", url, headers=headers) as response:
                    response.raise_for_status()
                    content_length = response.headers.get("Content-Length")
                    if content_length:
                        size = int(content_length)
                        # 避免返回0，确保进度条能显示
                        return max(size, 1024)
            except Exception as get_error:
                logger.debug(f"GET请求获取文件大小也失败: {url}, 错误: {get_error}")

            # 两种方法都失败，返回一个默认值以便显示进度
            logger.debug(f"无法获取文件大小，使用默认大小: {url}")
            return 1024 * 1024  # 默认1MB，至少能显示进度
        except (httpx.RequestError, httpx.HTTPStatusError, ValueError) as e:
            logger.debug(f"无法获取文件大小: {url}, 错误: {e}")
            return 1024 * 1024  # 默认1MB
        except Exception as e:
            logger.debug(f"获取文件大小时发生未知错误: {url}, 错误: {e}")
            return 1024 * 1024  # 默认1MB

    async def fetch_content_type(self, url: str) -> Optional[str]:
        """获取远程文件的内容类型"""
        try:
            # 增强请求头
            headers = self._enhance_headers(url)
            response = await self.client.head(url, headers=headers, follow_redirects=True)
            response.raise_for_status()

            # 尝试从Content-Type头获取内容类型
            content_type = response.headers.get("Content-Type")
            return content_type
        except (httpx.RequestError, httpx.HTTPStatusError) as e:
            logger.debug(f"无法获取内容类型: {url}, 错误: {e}")
            return None
        except Exception as e:
            logger.debug(f"获取内容类型时发生未知错误: {url}, 错误: {e}")
            return None

    def _get_extension_from_content_type(self, content_type: str) -> Optional[str]:
        """从内容类型推测文件扩展名"""
        content_type = content_type.lower()
        mime_to_ext = {
            'text/plain': '.txt',
            'text/html': '.html',
            'text/css': '.css',
            'text/javascript': '.js',
            'text/csv': '.csv',
            'text/xml': '.xml',
            'image/jpeg': '.jpg',
            'image/png': '.png',
            'image/gif': '.gif',
            'image/bmp': '.bmp',
            'image/webp': '.webp',
            'image/svg+xml': '.svg',
            'audio/mpeg': '.mp3',
            'audio/wav': '.wav',
            'audio/ogg': '.ogg',
            'video/mp4': '.mp4',
            'video/mpeg': '.mpeg',
            'video/quicktime': '.mov',
            'video/x-msvideo': '.avi',
            'video/webm': '.webm',
            'application/pdf': '.pdf',
            'application/json': '.json',
            'application/zip': '.zip',
            'application/x-rar-compressed': '.rar',
            'application/x-tar': '.tar',
            'application/x-gzip': '.gz',
            'application/msword': '.doc',
            'application/vnd.openxmlformats-officedocument.wordprocessingml.document': '.docx',
            'application/vnd.ms-excel': '.xls',
            'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet': '.xlsx',
            'application/vnd.ms-powerpoint': '.ppt',
            'application/vnd.openxmlformats-officedocument.presentationml.presentation': '.pptx',
            'application/x-bittorrent': '.torrent',
        }

        for mime, ext in mime_to_ext.items():
            if content_type.startswith(mime):
                return ext

        return None

    def _get_resume_header(self, url: str, file_path: Path) -> Dict[str, str]:
        """获取断点续传的请求头"""
        headers = self.headers.copy()

        if not self.resume or not file_path.exists():
            return headers

        file_size = file_path.stat().st_size
        if file_size > 0:
            headers["Range"] = f"bytes={file_size}-"
            logger.debug(f"断点续传: {url}, 从字节 {file_size} 开始")

        return headers

    def _load_state(self):
        """从文件加载下载状态"""
        try:
            with open(self.state_file, 'r', encoding='utf-8') as f:
                saved_state = json.load(f)
                # 恢复已完成的URL列表
                self.stats["completed_urls"] = set(saved_state.get("completed_urls", []))
                logger.info(f"从状态文件恢复下载状态，已完成 {len(self.stats['completed_urls'])} 个文件")
        except Exception as e:
            logger.warning(f"加载状态文件失败: {e}")

    def _save_state(self):
        """保存下载状态到文件"""
        try:
            state = {
                "timestamp": time.time(),
                "completed_urls": list(self.stats["completed_urls"]),
                "stats": {
                    "successful": self.stats["successful"],
                    "failed": self.stats["failed"],
                    "skipped": self.stats["skipped"],
                    "total_bytes": self.stats["total_bytes"]
                }
            }
            with open(self.state_file, 'w', encoding='utf-8') as f:
                json.dump(state, f, indent=2)
            logger.debug(f"下载状态已保存到 {self.state_file}")
        except Exception as e:
            logger.warning(f"保存状态文件失败: {e}")

    async def _check_domain_cooldown(self, url: str):
        """检查域名冷却时间，必要时等待"""
        domain = urlparse(url).netloc

        if domain in self.domain_cooldown:
            last_access, cooldown = self.domain_cooldown[domain]
            current_time = time.time()
            elapsed = current_time - last_access

            if elapsed < cooldown:
                wait_time = cooldown - elapsed
                logger.debug(f"域名冷却中: {domain}, 等待 {wait_time:.2f} 秒")
                await asyncio.sleep(wait_time)

        # 更新域名访问时间和冷却时间（随机值，但对经常访问的域名增加冷却时间）
        base_cooldown = random.uniform(self.min_delay if self.random_delay else 0,
                                       self.max_delay if self.random_delay else 0.5)

        # 如果该域名被频繁访问，增加冷却时间
        if domain in self.domain_cooldown:
            _, prev_cooldown = self.domain_cooldown[domain]
            # 逐渐增加冷却时间，但最大不超过30秒
            cooldown = min(prev_cooldown * 1.2, 30.0)
        else:
            cooldown = base_cooldown

        self.domain_cooldown[domain] = (time.time(), cooldown)

    def _enhance_headers(self, url: str) -> Dict[str, str]:
        """增强HTTP请求头，模拟真实浏览器"""
        enhanced_headers = self.headers.copy()

        # 如果用户没有指定User-Agent，添加一个常见浏览器的User-Agent
        if 'User-Agent' not in enhanced_headers:
            user_agents = [
                "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
                "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.0.0 Safari/537.36",
                "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:109.0) Gecko/20100101 Firefox/119.0",
                "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/16.6 Safari/605.1.15"
            ]
            enhanced_headers['User-Agent'] = random.choice(user_agents)

        # 添加常见请求头
        if 'Accept' not in enhanced_headers:
            enhanced_headers['Accept'] = '*/*'

        if 'Accept-Language' not in enhanced_headers:
            enhanced_headers['Accept-Language'] = 'en-US,en;q=0.9'

        if 'Accept-Encoding' not in enhanced_headers:
            enhanced_headers['Accept-Encoding'] = 'gzip, deflate, br'

        # 根据URL设置合理的Referer
        if 'Referer' not in enhanced_headers:
            parsed_url = urlparse(url)
            referer = f"{parsed_url.scheme}://{parsed_url.netloc}"
            enhanced_headers['Referer'] = referer

        return enhanced_headers

    async def download_file(self, url: str, filename: Optional[str] = None,
                            update_progress: bool = True) -> Tuple[bool, str, int]:
        """
        下载单个文件

        Args:
            url: 文件URL
            filename: 自定义文件名，如果为None则从URL提取
            update_progress: 是否更新进度条

        Returns:
            (成功状态, 文件路径, 下载字节数)的元组
        """
        # 验证URL格式
        if not self._validate_url(url):
            logger.error(f"跳过无效URL: {url}")
            self.stats["failed"] += 1
            return False, "", 0

        try:
            # 如果URL已经完成，直接跳过
            if url in self.stats["completed_urls"]:
                logger.info(f"URL已完成下载，跳过: {url}")
                self.stats["skipped"] += 1
                file_path = self.output_dir / (filename or self._get_filename_from_url(url))
                return True, str(file_path), 0

            # 检查域名冷却时间
            try:
                await self._check_domain_cooldown(url)
            except Exception as e:
                logger.warning(f"域名冷却检查失败: {url}, 错误: {e}")
                # 继续执行，不影响下载

            # 在请求前添加随机延时
            if self.random_delay:
                try:
                    delay = random.uniform(self.min_delay, self.max_delay)
                    logger.debug(f"随机延时 {delay:.2f} 秒")
                    await asyncio.sleep(delay)
                except Exception as e:
                    logger.warning(f"随机延时失败: {url}, 错误: {e}")

            # 获取文件名
            try:
                if filename is None:
                    filename = self._get_filename_from_url(url)
                elif self.force_suffix and self.default_suffix:
                    # 如果提供了文件名但强制使用后缀，则替换文件后缀
                    name_without_ext = os.path.splitext(filename)[0]
                    suffix = self.default_suffix if self.default_suffix.startswith(
                        '.') else f".{self.default_suffix}"
                    filename = f"{name_without_ext}{suffix}"

                # 如果文件名没有后缀，且不是强制使用指定后缀，尝试通过Content-Type获取
                if not os.path.splitext(filename)[1] and not self.force_suffix:
                    content_type = await self.fetch_content_type(url)
                    if content_type:
                        ext = self._get_extension_from_content_type(content_type)
                        if ext:
                            filename = f"{filename}{ext}"
                            logger.debug(f"根据内容类型 {content_type} 添加后缀 {ext}")

                    # 如果仍然没有后缀且设置了默认后缀，则使用默认后缀
                    if not os.path.splitext(filename)[1] and self.default_suffix:
                        suffix = self.default_suffix if self.default_suffix.startswith(
                            '.') else f".{self.default_suffix}"
                        filename = f"{filename}{suffix}"
            except Exception as e:
                logger.warning(f"处理文件名时出错: {url}, 错误: {e}")
                # 使用一个安全的默认文件名
                if filename is None:
                    filename = f"download_{int(time.time())}_{random.randint(1000, 9999)}"
                    if self.default_suffix:
                        suffix = self.default_suffix if self.default_suffix.startswith(
                            '.') else f".{self.default_suffix}"
                        filename = f"{filename}{suffix}"

            file_path = self.output_dir / filename
            temp_path = file_path.with_suffix(file_path.suffix + ".part")
            downloaded_bytes = 0
            retry_count = 0
            mode = "ab" if self.resume and temp_path.exists() else "wb"

            # 如果文件已存在且不覆盖，则跳过
            if file_path.exists() and not self.overwrite:
                logger.info(f"文件已存在，跳过下载: {file_path}")
                self.stats["skipped"] += 1
                self.stats["completed_urls"].add(url)
                try:
                    self._save_state()  # 保存状态
                except Exception as e:
                    logger.warning(f"保存状态时出错: {url}, 错误: {e}")
                return True, str(file_path), 0

            # 尝试获取远程文件大小用于进度显示
            try:
                file_size = await self.fetch_file_size(url)
                if file_size is None or file_size <= 0:
                    file_size = 1024 * 1024  # 默认1MB
            except Exception as e:
                logger.warning(f"获取文件大小失败: {url}, 错误: {e}")
                file_size = 1024 * 1024  # 默认1MB

            # 创建进度条
            if update_progress and self.use_tqdm and url not in self.progress_bars:
                self._create_progress_bar(url, filename, file_size)

            # 如果使用断点续传，获取已下载的字节数
            if self.resume and temp_path.exists():
                try:
                    downloaded_bytes = temp_path.stat().st_size

                    # 更新进度条显示已下载的部分
                    if update_progress and self.use_tqdm:
                        self._update_progress_bar(url, downloaded_bytes)

                    if file_size and downloaded_bytes >= file_size:
                        # 文件已经完成下载，重命名临时文件
                        temp_path.rename(file_path)
                        # 关闭进度条
                        if update_progress and self.use_tqdm:
                            self._close_progress_bar(url, True)

                        logger.info(f"文件已完成下载: {file_path}")
                        self.stats["successful"] += 1
                        self.stats["completed_urls"].add(url)
                        try:
                            self._save_state()  # 保存状态
                        except Exception as e:
                            logger.warning(f"保存状态时出错: {url}, 错误: {e}")
                        return True, str(file_path), file_size
                except Exception as e:
                    logger.warning(f"处理断点续传时出错: {url}, 错误: {e}")
                    downloaded_bytes = 0
                    mode = "wb"  # 改为覆写模式

            while retry_count <= self.max_retries:
                try:
                    # 获取请求头，包括断点续传和增强的请求头
                    try:
                        headers = self._get_resume_header(url, temp_path)
                        headers = self._enhance_headers(url)
                    except Exception as e:
                        logger.warning(f"获取请求头时出错: {url}, 错误: {e}")
                        headers = self.headers.copy()

                    # 开始下载
                    async with self.client.stream("GET", url, headers=headers) as response:
                        response.raise_for_status()

                        # 更新文件大小信息
                        content_length = response.headers.get("Content-Length")
                        if content_length:
                            try:
                                total = int(content_length)
                                if total > 0:
                                    file_size = total + downloaded_bytes
                                    # 更新进度条总大小
                                    if update_progress and self.use_tqdm:
                                        self._update_progress_bar(url, 0, file_size)
                            except (ValueError, TypeError):
                                # 如果转换失败，保持原有大小
                                pass

                        # 确保文件大小至少为1KB，以避免除零错误
                        if file_size <= 0:
                            file_size = 1024  # 默认1KB
                            # 更新进度条总大小
                            if update_progress and self.use_tqdm:
                                self._update_progress_bar(url, 0, file_size)

                        # 确保输出目录存在
                        try:
                            os.makedirs(os.path.dirname(temp_path), exist_ok=True)
                        except Exception as e:
                            logger.warning(f"创建目录时出错: {os.path.dirname(temp_path)}, 错误: {e}")

                        with open(temp_path, mode) as f:
                            try:
                                # 初始化上次更新时间，避免过于频繁的进度更新
                                last_update = time.time()
                                update_interval = 0.2  # 最小更新间隔(秒)

                                async for chunk in response.aiter_bytes(chunk_size=self.chunk_size):
                                    if chunk:
                                        f.write(chunk)
                                        chunk_size = len(chunk)
                                        downloaded_bytes += chunk_size
                                        self.stats["total_bytes"] += chunk_size

                                        # 控制更新频率，避免过于频繁的进度更新
                                        current_time = time.time()
                                        if update_progress and self.use_tqdm and (
                                                current_time - last_update > update_interval):
                                            self._update_progress_bar(url, chunk_size)
                                            last_update = current_time

                            except Exception as e:
                                logger.error(f"下载数据块时出错: {url}, 错误: {e}")
                                # 如果是在下载过程中出错，下次尝试断点续传
                                mode = "ab"
                                raise

                    # 下载完成，重命名临时文件
                    try:
                        temp_path.rename(file_path)
                    except Exception as e:
                        logger.error(f"重命名文件时出错: {temp_path} -> {file_path}, 错误: {e}")
                        # 尝试复制文件后删除临时文件
                        try:
                            import shutil
                            shutil.copy2(str(temp_path), str(file_path))
                            os.remove(str(temp_path))
                        except Exception as e2:
                            logger.error(f"备用文件复制方法也失败: {e2}")
                            # 如果复制也失败，至少保留临时文件
                            return True, str(temp_path), downloaded_bytes

                    # 确保进度条显示100%并关闭
                    if update_progress and self.use_tqdm:
                        self._close_progress_bar(url, True)

                    logger.info(f"下载成功: {file_path} ({self._format_bytes(downloaded_bytes)})")
                    self.stats["successful"] += 1
                    self.stats["completed_urls"].add(url)
                    try:
                        self._save_state()  # 保存状态
                    except Exception as e:
                        logger.warning(f"保存状态时出错: {url}, 错误: {e}")
                    return True, str(file_path), downloaded_bytes

                except (httpx.RequestError, httpx.HTTPStatusError) as e:
                    retry_count += 1

                    # 特殊处理403 Forbidden或429 Too Many Requests错误
                    if isinstance(e, httpx.HTTPStatusError) and e.response.status_code in (403, 429):
                        # 增加冷却时间
                        try:
                            domain = urlparse(url).netloc
                            self.domain_cooldown[domain] = (time.time(), min(30 + retry_count * 10, 300))
                            logger.warning(f"访问受限: {url}, HTTP {e.response.status_code}，增加冷却时间")
                        except Exception as e2:
                            logger.warning(f"处理访问限制时出错: {url}, 错误: {e2}")

                    if retry_count > self.max_retries:
                        logger.error(f"下载失败: {url}, 错误: {e}, 已达到最大重试次数")
                        self.stats["failed"] += 1

                        # 关闭进度条
                        if update_progress and self.use_tqdm:
                            self._close_progress_bar(url, False)

                        return False, str(file_path), downloaded_bytes

                    # 使用指数退避策略，但添加随机因子避免同步重试
                    delay = 2 ** retry_count + random.uniform(0, 2)
                    logger.warning(f"下载出错: {url}, 错误: {e}, {retry_count}/{self.max_retries}次重试, "
                                   f"等待{delay:.2f}秒后重试...")
                    try:
                        await asyncio.sleep(delay)
                    except Exception as e2:
                        logger.warning(f"延时等待时出错: {url}, 错误: {e2}")

                except Exception as e:
                    retry_count += 1
                    logger.error(f"下载时发生意外错误: {url}, 类型: {type(e).__name__}, 错误: {e}")

                    if retry_count > self.max_retries:
                        logger.error(f"下载失败: {url}, 已达到最大重试次数")
                        self.stats["failed"] += 1

                        # 关闭进度条
                        if update_progress and self.use_tqdm:
                            self._close_progress_bar(url, False)

                        return False, str(file_path), downloaded_bytes

                    delay = 2 ** retry_count + random.uniform(0, 2)
                    logger.warning(
                        f"下载出错，将重试: {url}, {retry_count}/{self.max_retries}次重试, 等待{delay:.2f}秒...")
                    try:
                        await asyncio.sleep(delay)
                    except Exception as e2:
                        logger.warning(f"延时等待时出错: {url}, 错误: {e2}")

        except Exception as e:
            logger.error(f"下载过程中发生未捕获的异常: {url}, 错误: {e}")
            logger.debug(f"异常详情: {traceback.format_exc()}")
            self.stats["failed"] += 1

            # 关闭进度条
            if update_progress and self.use_tqdm:
                self._close_progress_bar(url, False)

            return False, "", 0

    async def download_batch(self, urls: List[str], filenames: Optional[List[str]] = None) -> Dict[str, str]:
        """
        批量下载文件

        Args:
            urls: 要下载的URL列表
            filenames: 自定义文件名列表，如果为None则从URL提取或使用映射

        Returns:
            URL到本地文件路径的映射
        """
        if not urls:
            logger.warning("没有提供下载URL")
            return {}

        # 过滤无效URL
        valid_urls = []
        valid_filenames = []
        for i, url in enumerate(urls):
            if self._validate_url(url):
                valid_urls.append(url)
                if filenames and i < len(filenames):
                    valid_filenames.append(filenames[i])

        if len(valid_urls) < len(urls):
            logger.warning(f"过滤掉 {len(urls) - len(valid_urls)} 个无效URL，剩余 {len(valid_urls)} 个有效URL")
            urls = valid_urls
            filenames = valid_filenames if filenames else None

        if not urls:
            logger.error("没有有效的URL需要下载")
            return {}

        if filenames and len(urls) != len(filenames):
            logger.warning("URL数量与文件名数量不匹配，将使用URL中的文件名")
            filenames = None

        # 如果继续上次下载，则需要过滤掉已完成的URL
        try:
            if self.continue_from_state:
                original_count = len(urls)
                remaining_urls = []
                remaining_filenames = []

                for i, url in enumerate(urls):
                    if url not in self.stats["completed_urls"]:
                        remaining_urls.append(url)
                        if filenames and i < len(filenames):
                            remaining_filenames.append(filenames[i])

                if len(remaining_urls) < original_count:
                    logger.info(f"从状态文件中恢复，跳过 {original_count - len(remaining_urls)} 个已完成的URL，"
                                f"剩余 {len(remaining_urls)} 个URL需要下载")
                    urls = remaining_urls
                    filenames = remaining_filenames if filenames else None
        except Exception as e:
            logger.warning(f"处理继续下载状态时出错: {e}")
            # 继续使用原始URL列表

        # 初始化统计信息
        try:
            if not self.continue_from_state:
                self.stats["successful"] = 0
                self.stats["failed"] = 0
                self.stats["skipped"] = 0
                self.stats["total_bytes"] = 0
                self.stats["completed_urls"] = set()

            self.stats["start_time"] = time.time()
        except Exception as e:
            logger.warning(f"初始化统计信息时出错: {e}")

        results = {}

        # 使用信号量限制并发数
        sem = asyncio.Semaphore(self.max_workers)

        # 创建一个总进度条显示总体下载进度
        total_pbar = None
        if self.use_tqdm:
            try:
                total_pbar = tqdm(total=len(urls), unit='个', desc="总进度", position=0, leave=True)
            except Exception as e:
                logger.warning(f"创建总进度条时出错: {e}")
                total_pbar = None

        try:
            # 定义下载函数
            async def limited_download(url, file_name=None):
                async with sem:
                    try:
                        logger.debug(f"开始下载: {url}")
                        success, file_path, downloaded_bytes = await self.download_file(url, file_name,
                                                                                        update_progress=True)
                        return url, success, file_path, downloaded_bytes
                    except Exception as e:
                        logger.error(f"下载出现未处理异常: {url}, 错误: {e}")
                        logger.debug(f"异常详情: {traceback.format_exc()}")
                        self.stats["failed"] += 1
                        # 确保即使失败也清理进度条
                        if self.use_tqdm:
                            self._close_progress_bar(url, False)
                        return url, False, "", 0

            # 创建下载任务
            tasks = []
            for i, url in enumerate(urls):
                file_name = filenames[i] if filenames and i < len(filenames) else None
                # 使用asyncio.create_task创建异步任务
                task = asyncio.create_task(limited_download(url, file_name))
                tasks.append(task)

            # 使用tqdm_asyncio处理任务，避免输出混乱
            completed_tasks = 0
            total_tasks = len(tasks)

            # 逐个等待任务完成
            for future in asyncio.as_completed(tasks):
                try:
                    url, success, file_path, downloaded_bytes = await future
                    completed_tasks += 1

                    # 更新总进度条
                    if total_pbar:
                        total_pbar.update(1)

                    # 更新进度信息
                    if success:
                        results[url] = file_path
                        logger.info(
                            f"下载进度: [{completed_tasks}/{total_tasks}] {file_path} - 大小: {self._format_bytes(downloaded_bytes)}")
                    else:
                        logger.warning(f"下载进度: [{completed_tasks}/{total_tasks}] 下载失败: {url}")

                    # 定期保存状态
                    if completed_tasks % 10 == 0 or completed_tasks == total_tasks:
                        try:
                            self._save_state()
                            logger.info(
                                f"当前总进度: {completed_tasks}/{total_tasks} ({completed_tasks / total_tasks * 100:.1f}%)")
                        except Exception as e:
                            logger.warning(f"保存状态时出错: {e}")
                except Exception as e:
                    logger.error(f"处理下载任务结果时出错: {e}")
                    completed_tasks += 1
                    # 更新总进度条
                    if total_pbar:
                        total_pbar.update(1)
        except Exception as e:
            logger.error(f"批量下载处理失败: {e}")
            logger.debug(f"异常详情: {traceback.format_exc()}")
        finally:
            # 关闭总进度条
            if total_pbar:
                total_pbar.close()

            # 清理所有进度条
            self._cleanup_progress_bars()

        # 更新统计信息
        try:
            self.stats["end_time"] = time.time()
            self._print_stats()

            # 最终保存状态
            self._save_state()
        except Exception as e:
            logger.warning(f"更新最终统计信息时出错: {e}")

        return results

    def _print_stats(self):
        """打印下载统计信息"""
        duration = self.stats["end_time"] - self.stats["start_time"]
        total_files = self.stats["successful"] + self.stats["failed"] + self.stats["skipped"]

        logger.info("=" * 50)
        logger.info("下载统计:")
        logger.info(f"总文件数: {total_files}")
        logger.info(f"成功: {self.stats['successful']}")
        logger.info(f"失败: {self.stats['failed']}")
        logger.info(f"跳过: {self.stats['skipped']}")
        logger.info(f"总下载大小: {self._format_bytes(self.stats['total_bytes'])}")
        logger.info(f"总耗时: {duration:.2f}秒")
        if duration > 0:
            avg_speed = self.stats["total_bytes"] / duration
            logger.info(f"平均速度: {self._format_bytes(int(avg_speed))}/s")
        logger.info("=" * 50)


def parse_arguments():
    """解析命令行参数"""
    parser = argparse.ArgumentParser(
        description="网络文件批量下载工具",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
示例:
  # 下载单个文件
  python batch_downloader.py https://example.com/file.zip

  # 从文本文件批量下载URL
  python batch_downloader.py -f urls.txt -o ./downloads

  # 使用10个并发连接下载
  python batch_downloader.py -f urls.txt -w 10

  # 下载时不验证SSL证书
  python batch_downloader.py -f urls.txt --no-verify

  # 为所有无后缀文件添加默认后缀
  python batch_downloader.py -f urls.txt --suffix mp4

  # 强制使用指定的后缀，忽略URL中的后缀
  python batch_downloader.py -f urls.txt --suffix torrent --force-suffix
  
  # 添加随机延时避免被检测为爬虫
  python batch_downloader.py -f urls.txt --random-delay

  # 使用映射文件指定文件名
  python batch_downloader.py -f urls.txt --name-map mappings.json
  
  # 断点续传，继续上次未完成的下载
  python batch_downloader.py -f urls.txt --continue
"""
    )

    # 基本参数
    parser.add_argument("urls", nargs="*",
                        help="要下载的文件URL列表")
    parser.add_argument("-f", "--file", dest="url_file",
                        help="包含URL列表的文件，每行一个URL")
    parser.add_argument("-o", "--output-dir", dest="output_dir", default="./downloads",
                        help="下载文件保存目录，默认为 ./downloads")

    # 下载选项
    parser.add_argument("-w", "--workers", type=int, default=5,
                        help="最大并发下载数，默认为5")
    parser.add_argument("-t", "--timeout", type=int, default=30,
                        help="连接超时时间(秒)，默认为30秒")
    parser.add_argument("-c", "--chunk-size", type=int, default=1024 * 1024,
                        help="文件下载分块大小(字节)，默认为1MB")
    parser.add_argument("-r", "--retries", type=int, default=3,
                        help="下载失败时最大重试次数，默认为3次")
    parser.add_argument("--no-verify", action="store_true",
                        help="不验证SSL证书")
    parser.add_argument("--no-resume", action="store_true",
                        help="禁用断点续传")
    parser.add_argument("--overwrite", action="store_true",
                        help="覆盖已存在的文件")

    # 文件名选项
    parser.add_argument("-s", "--suffix", dest="default_suffix",
                        help="默认文件后缀，当URL无法确定文件类型时使用")
    parser.add_argument("--force-suffix", action="store_true",
                        help="强制使用指定的文件后缀，忽略URL中的后缀")
    parser.add_argument("--name-map", dest="name_map_file",
                        help="URL到文件名映射文件(JSON或CSV格式)")

    # 请求头
    parser.add_argument("--header", dest="headers", action="append",
                        help="添加HTTP头，格式为 'Name: Value'")

    # 日志选项
    parser.add_argument("--debug", action="store_true",
                        help="启用调试日志")
    parser.add_argument("--no-progress", action="store_true",
                        help="不显示进度条")

    # 新增随机延时选项
    parser.add_argument("--random-delay", action="store_true",
                        help="启用随机延时，避免被检测为爬虫")
    parser.add_argument("--min-delay", type=float, default=1.0,
                        help="随机延时的最小秒数 (默认: 1.0)")
    parser.add_argument("--max-delay", type=float, default=5.0,
                        help="随机延时的最大秒数 (默认: 5.0)")

    # 状态保存选项
    parser.add_argument("--continue", dest="continue_download", action="store_true",
                        help="继续上次未完成的下载")
    parser.add_argument("--state-file", dest="state_file",
                        help="下载状态保存文件路径 (默认: <output_dir>/.download_state.json)")

    return parser.parse_args()


def read_urls_from_file(file_path: str) -> List[str]:
    """从文件读取URL列表，每行一个URL"""
    urls = []
    encoding_list = ['utf-8', 'gbk', 'latin-1', 'cp1252']

    for encoding in encoding_list:
        try:
            with open(file_path, "r", encoding=encoding) as f:
                urls = [line.strip() for line in f.readlines()]

            logger.info(f"使用 {encoding} 编码成功读取URL文件 {file_path}")
            break
        except UnicodeDecodeError:
            # 尝试下一种编码
            logger.debug(f"使用 {encoding} 编码读取URL文件失败，尝试其他编码")
            continue
        except Exception as e:
            logger.error(f"读取URL文件出错: {e}")
            return []
    else:
        # 所有编码都尝试失败
        logger.error(f"无法使用任何支持的编码读取URL文件: {file_path}")
        return []

    logger.info(f"从文件 {file_path} 读取了 {len(urls)} 个URL")
    return urls


def read_name_map_file(file_path: str) -> Dict[str, str]:
    """读取URL到文件名的映射文件"""
    if not os.path.exists(file_path):
        logger.error(f"映射文件不存在: {file_path}")
        return {}

    try:
        ext = os.path.splitext(file_path)[1].lower()

        if ext == '.json':
            # JSON格式: {"url1": "filename1", "url2": "filename2"}
            with open(file_path, 'r', encoding='utf-8') as f:
                return json.load(f)

        elif ext == '.csv':
            # CSV格式: url,filename
            name_map = {}
            with open(file_path, 'r', encoding='utf-8') as f:
                reader = csv.reader(f)
                for row in reader:
                    if len(row) >= 2:
                        name_map[row[0].strip()] = row[1].strip()
            return name_map

        else:
            logger.error(f"不支持的映射文件格式: {ext}，请使用JSON或CSV格式")
            return {}

    except Exception as e:
        logger.error(f"读取映射文件出错: {e}")
        return {}


def parse_headers(header_strings: List[str]) -> Dict[str, str]:
    """解析HTTP头字符串"""
    if not header_strings:
        return {}

    headers = {}
    for header in header_strings:
        try:
            name, value = header.split(":", 1)
            headers[name.strip()] = value.strip()
        except ValueError:
            logger.warning(f"无效的HTTP头格式: {header}")

    return headers


async def main():
    """主函数"""
    try:
        args = parse_arguments()

        # 设置日志级别
        if args.debug:
            logging.getLogger().setLevel(logging.DEBUG)

        # 获取下载URL列表
        urls = []
        if args.urls:
            urls.extend(args.urls)
        if args.url_file:
            file_urls = read_urls_from_file(args.url_file)
            urls.extend(file_urls)

        if not urls:
            logger.error("没有URL可下载，请提供URL参数或URL列表文件")
            return

        logger.info(f"准备下载 {len(urls)} 个URL")

        # 解析HTTP头
        headers = parse_headers(args.headers or [])

        # 添加常用的HTTP头，如果用户没有指定
        if 'User-Agent' not in headers:
            headers[
                'User-Agent'] = 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'

        # 读取名称映射文件
        filename_map = {}
        if args.name_map_file:
            try:
                filename_map = read_name_map_file(args.name_map_file)
                logger.info(f"从映射文件加载了 {len(filename_map)} 个URL到文件名的映射")
            except Exception as e:
                logger.error(f"读取名称映射文件失败: {e}")

        # 如果不想使用tqdm进度条
        global TQDM_AVAILABLE
        if args.no_progress:
            TQDM_AVAILABLE = False

        # 如果设置了强制后缀但没有设置后缀，给出警告
        if args.force_suffix and not args.default_suffix:
            logger.warning("设置了--force-suffix但未设置--suffix，强制后缀选项将被忽略")

        try:
            # 创建下载器
            async with BatchDownloader(
                    output_dir=args.output_dir,
                    max_workers=args.workers,
                    timeout=args.timeout,
                    chunk_size=args.chunk_size,
                    max_retries=args.retries,
                    verify_ssl=not args.no_verify,
                    headers=headers,
                    resume=not args.no_resume,
                    overwrite=args.overwrite,
                    default_suffix=args.default_suffix,
                    force_suffix=args.force_suffix and bool(args.default_suffix),
                    filename_map=filename_map,
                    random_delay=args.random_delay,
                    min_delay=args.min_delay,
                    max_delay=args.max_delay,
                    state_file=args.state_file,
                    continue_from_state=args.continue_download
            ) as downloader:
                # 执行批量下载
                result = await downloader.download_batch(urls)

                # 输出下载结果
                successful = sum(1 for url in urls if url in result)
                logger.info(f"下载完成: 成功 {successful}/{len(urls)}")
        except Exception as e:
            logger.error(f"批量下载过程中发生未捕获的异常: {e}")
            logger.debug(f"异常详情: {traceback.format_exc()}")
            return 1

        return 0
    except Exception as e:
        logger.critical(f"程序执行过程中发生致命错误: {e}")
        logger.debug(f"异常详情: {traceback.format_exc()}")
        return 1


if __name__ == "__main__":
    try:
        exit_code = asyncio.run(main())
        sys.exit(exit_code)
    except KeyboardInterrupt:
        logger.info("下载已被用户取消")
        sys.exit(130)  # 标准的SIGINT退出码
    except Exception as e:
        logger.critical(f"程序启动过程中发生异常: {e}")
        logger.debug(f"异常详情: {traceback.format_exc()}")
        sys.exit(1)
