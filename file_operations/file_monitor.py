#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
文件监控工具

这个脚本用于实时监控指定目录中的文件变化（创建、修改、删除、重命名等），
并可以在文件发生变化时记录或执行指定操作。适用于自动备份、开发监控、日志跟踪等场景。
"""

import argparse
import datetime
import json
import logging
import os
import re
import shutil
import signal
import subprocess
import sys
import threading
import time
from enum import Enum
from queue import Queue
from typing import Dict, List, Optional

try:
    from watchdog.observers import Observer
    from watchdog.events import (
        FileSystemEventHandler,
        FileSystemEvent,
        FileCreatedEvent,
        FileModifiedEvent,
        FileDeletedEvent,
        FileMovedEvent,
        DirCreatedEvent,
        DirModifiedEvent,
        DirDeletedEvent,
        DirMovedEvent
    )
except ImportError:
    print("错误: 缺少必要的依赖库 watchdog")
    print("请运行以下命令安装: pip install watchdog")
    sys.exit(1)

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)
logger = logging.getLogger(__name__)


class EventType(Enum):
    """事件类型枚举"""
    CREATED = "created"
    MODIFIED = "modified"
    DELETED = "deleted"
    MOVED = "moved"
    ALL = "all"  # 用于过滤所有类型


class FileType(Enum):
    """文件类型枚举"""
    FILE = "file"
    DIRECTORY = "directory"
    ALL = "all"  # 用于过滤所有类型


class ActionType(Enum):
    """操作类型枚举"""
    LOG = "log"  # 记录到日志
    BACKUP = "backup"  # 备份修改的文件
    EXECUTE = "execute"  # 执行命令
    NOTIFY = "notify"  # 发送通知
    CUSTOM = "custom"  # 自定义操作（Python函数）


class MonitorConfig:
    """监控配置类"""

    def __init__(
            self,
            paths: List[str],
            recursive: bool = True,
            include_patterns: Optional[List[str]] = None,
            exclude_patterns: Optional[List[str]] = None,
            include_hidden: bool = False,
            event_types: Optional[List[EventType]] = None,
            file_types: Optional[List[FileType]] = None,
            actions: Optional[Dict[str, Dict]] = None,
            min_size: int = 0,
            max_size: Optional[int] = None,
            cooldown: int = 1,
            batch_mode: bool = False,
            batch_timeout: int = 5
    ):
        """
        初始化监控配置

        Args:
            paths: 要监控的路径列表
            recursive: 是否递归监控子目录
            include_patterns: 要包含的文件模式列表（如 ['*.txt', '*.log']）
            exclude_patterns: 要排除的文件模式列表（如 ['*.tmp', '*.bak']）
            include_hidden: 是否包含隐藏文件
            event_types: 要监控的事件类型列表
            file_types: 要监控的文件类型列表
            actions: 要执行的操作配置
            min_size: 最小文件大小限制（字节）
            max_size: 最大文件大小限制（字节）
            cooldown: 相同文件两次事件间的最小冷却时间（秒）
            batch_mode: 是否批处理模式（收集一段时间内的事件后一次处理）
            batch_timeout: 批处理模式下的超时时间（秒）
        """
        self.paths = [os.path.abspath(p) for p in paths]
        self.recursive = recursive
        self.include_patterns = include_patterns or []
        self.exclude_patterns = exclude_patterns or []
        self.include_hidden = include_hidden
        self.event_types = event_types or [EventType.ALL]
        self.file_types = file_types or [FileType.ALL]
        self.actions = actions or {"log": {"target": "console"}}
        self.min_size = min_size
        self.max_size = max_size
        self.cooldown = cooldown
        self.batch_mode = batch_mode
        self.batch_timeout = batch_timeout

        # 编译正则表达式
        self.include_regex = self._compile_patterns(self.include_patterns)
        self.exclude_regex = self._compile_patterns(self.exclude_patterns)

        # 最近处理的文件事件缓存（用于防止重复处理）
        self.recent_events = {}

    @staticmethod
    def _compile_patterns(patterns: List[str]) -> List[re.Pattern]:
        """将glob模式编译为正则表达式"""
        result = []
        for pattern in patterns:
            # 转换glob模式到正则表达式
            regex = pattern.replace(".", "\\.")
            regex = regex.replace("*", ".*")
            regex = regex.replace("?", ".")
            regex = f"^{regex}$"
            result.append(re.compile(regex, re.IGNORECASE))
        return result

    def should_process(self, event_path: str, event_type: EventType, file_type: FileType) -> bool:
        """
        判断是否应该处理此事件

        Args:
            event_path: 事件路径
            event_type: 事件类型
            file_type: 文件类型

        Returns:
            是否应该处理
        """
        # 检查事件类型
        if EventType.ALL not in self.event_types and event_type not in self.event_types:
            return False

        # 检查文件类型
        if FileType.ALL not in self.file_types and file_type not in self.file_types:
            return False

        # 检查隐藏文件
        if not self.include_hidden and os.path.basename(event_path).startswith('.'):
            return False

        # 检查冷却时间
        current_time = time.time()
        if event_path in self.recent_events:
            last_time = self.recent_events[event_path]
            if current_time - last_time < self.cooldown:
                return False

        # 更新最近处理时间
        self.recent_events[event_path] = current_time

        # 检查文件大小（仅对文件有效）
        if file_type == FileType.FILE and os.path.exists(event_path):
            try:
                file_size = os.path.getsize(event_path)
                if file_size < self.min_size:
                    return False
                if self.max_size is not None and file_size > self.max_size:
                    return False
            except (FileNotFoundError, PermissionError):
                # 如果文件已被删除或无权访问，则跳过大小检查
                pass

        # 检查包含和排除模式
        filename = os.path.basename(event_path)

        # 如果有包含模式，文件必须匹配至少一个
        if self.include_regex:
            include_match = any(regex.match(filename) for regex in self.include_regex)
            if not include_match:
                return False

        # 如果有排除模式，文件不能匹配任何一个
        if self.exclude_regex:
            exclude_match = any(regex.match(filename) for regex in self.exclude_regex)
            if exclude_match:
                return False

        return True


class FileMonitor:
    """文件监控类"""

    def __init__(self, config: MonitorConfig):
        """
        初始化文件监控器

        Args:
            config: 监控配置
        """
        self.config = config
        self.observer = Observer()
        self.event_handler = MonitorEventHandler(self)

        # 用于批处理模式
        self.event_queue = Queue()
        self.batch_processor = None
        self.stop_flag = threading.Event()

        # 统计信息
        self.stats = {
            "started_at": datetime.datetime.now().isoformat(),
            "events_processed": 0,
            "events_by_type": {
                "created": 0,
                "modified": 0,
                "deleted": 0,
                "moved": 0
            },
            "actions_executed": 0,
            "errors": 0
        }

        # 确保备份目录存在
        if "backup" in self.config.actions:
            backup_dir = self.config.actions["backup"].get("target", "file_monitor_backups")
            os.makedirs(backup_dir, exist_ok=True)
            logger.info(f"备份目录: {os.path.abspath(backup_dir)}")

    def start(self):
        """启动监控"""
        for path in self.config.paths:
            if not os.path.exists(path):
                logger.warning(f"路径不存在: {path}")
                continue

            logger.info(f"开始监控: {path}" + (" (递归)" if self.config.recursive else ""))
            self.observer.schedule(
                self.event_handler,
                path,
                recursive=self.config.recursive
            )

        self.observer.start()

        # 批处理模式下启动处理线程
        if self.config.batch_mode:
            self.batch_processor = threading.Thread(
                target=self._process_event_batch,
                daemon=True
            )
            self.batch_processor.start()
            logger.info(f"批处理模式已启动，超时: {self.config.batch_timeout} 秒")

    def stop(self):
        """停止监控"""
        if self.config.batch_mode:
            self.stop_flag.set()
            if self.batch_processor:
                self.batch_processor.join(timeout=3)

        self.observer.stop()
        self.observer.join()
        logger.info("监控已停止")
        self._log_stats()

    def handle_event(self, event: FileSystemEvent):
        """
        处理文件系统事件

        Args:
            event: 文件系统事件
        """
        # 解析事件信息
        event_info = self._parse_event(event)
        if not event_info:
            return

        # 判断是否应该处理
        should_process = self.config.should_process(
            event_info["path"],
            event_info["event_type"],
            event_info["file_type"]
        )

        if not should_process:
            return

        # 批处理模式下，将事件加入队列
        if self.config.batch_mode:
            self.event_queue.put(event_info)
            return

        # 立即处理事件
        self._process_event(event_info)

    def _process_event(self, event_info: Dict):
        """处理单个事件"""
        self._update_stats(event_info["event_type"])

        # 执行配置的操作
        for action_name, action_config in self.config.actions.items():
            try:
                self._execute_action(action_name, action_config, event_info)
                self.stats["actions_executed"] += 1
            except Exception as e:
                logger.error(f"执行操作时出错: {action_name} - {e}")
                self.stats["errors"] += 1

    def _process_event_batch(self):
        """批处理事件队列"""
        while not self.stop_flag.is_set():
            # 收集一批事件
            batch = []
            batch_start = time.time()

            # 等待第一个事件
            try:
                first_event = self.event_queue.get(timeout=0.5)
                batch.append(first_event)
                self.event_queue.task_done()
            except:
                continue

            # 收集超时时间内的所有事件
            batch_timeout = time.time() + self.config.batch_timeout
            while time.time() < batch_timeout:
                try:
                    event = self.event_queue.get(timeout=0.1)
                    batch.append(event)
                    self.event_queue.task_done()
                except:
                    break

                if self.stop_flag.is_set():
                    break

            # 去重并处理批处理事件
            unique_events = self._deduplicate_events(batch)

            if unique_events:
                logger.info(f"处理批次: {len(unique_events)} 个事件 (原始: {len(batch)})")
                for event_info in unique_events:
                    self._process_event(event_info)

    @staticmethod
    def _deduplicate_events(events: List[Dict]) -> List[Dict]:
        """
        对事件列表去重，保留每个路径的最后一个事件
        
        Args:
            events: 事件列表
            
        Returns:
            去重后的事件列表
        """
        path_to_event = {}

        # 保留每个路径的最后一个事件
        for event in events:
            path = event["path"]
            path_to_event[path] = event

        # 返回去重后的事件列表
        return list(path_to_event.values())

    def _parse_event(self, event: FileSystemEvent) -> Optional[Dict]:
        """解析文件系统事件"""
        # 处理不同类型的事件
        if isinstance(event, (FileCreatedEvent, DirCreatedEvent)):
            event_type = EventType.CREATED
        elif isinstance(event, (FileModifiedEvent, DirModifiedEvent)):
            event_type = EventType.MODIFIED
        elif isinstance(event, (FileDeletedEvent, DirDeletedEvent)):
            event_type = EventType.DELETED
        elif isinstance(event, (FileMovedEvent, DirMovedEvent)):
            event_type = EventType.MOVED
        else:
            return None

        # 确定文件类型
        is_directory = getattr(event, "is_directory", False)
        file_type = FileType.DIRECTORY if is_directory else FileType.FILE

        # 准备事件信息
        event_info = {
            "path": event.src_path,
            "event_type": event_type,
            "file_type": file_type,
            "time": datetime.datetime.now().isoformat()
        }

        # 对于移动事件，添加目标路径
        if event_type == EventType.MOVED:
            event_info["dest_path"] = event.dest_path

        return event_info

    def _execute_action(self, action_name: str, action_config: Dict, event_info: Dict):
        """
        执行配置的操作
        
        Args:
            action_name: 操作名称
            action_config: 操作配置
            event_info: 事件信息
        """
        action_type = ActionType(action_name)

        if action_type == ActionType.LOG:
            self._log_action(action_config, event_info)
        elif action_type == ActionType.BACKUP:
            self._backup_action(action_config, event_info)
        elif action_type == ActionType.EXECUTE:
            self._execute_command(action_config, event_info)
        elif action_type == ActionType.NOTIFY:
            self._send_notification(action_config, event_info)
        elif action_type == ActionType.CUSTOM and "callback" in action_config:
            callback = action_config["callback"]
            if callable(callback):
                callback(event_info, action_config)

    def _log_action(self, config: Dict, event_info: Dict):
        """记录事件到日志"""
        target = config.get("target", "console")

        # 格式化事件信息
        filename = os.path.basename(event_info["path"])
        event_str = f"{event_info['event_type'].value.upper()} {event_info['file_type'].value}: {filename}"

        if event_info["event_type"] == EventType.MOVED:
            dest_filename = os.path.basename(event_info["dest_path"])
            event_str += f" -> {dest_filename}"

        # 根据目标输出
        if target == "console":
            logger.info(event_str)

        elif target.startswith("file:"):
            log_file = target[5:]
            with open(log_file, "a", encoding="utf-8") as f:
                log_entry = f"{event_info['time']} - {event_str}\n"
                f.write(log_entry)

        elif target == "json" and "file" in config:
            json_file = config["file"]
            try:
                # 读取现有数据
                if os.path.exists(json_file) and os.path.getsize(json_file) > 0:
                    with open(json_file, "r", encoding="utf-8") as f:
                        try:
                            log_data = json.load(f)
                        except json.JSONDecodeError:
                            log_data = {"events": []}
                else:
                    log_data = {"events": []}

                # 添加新事件
                log_data["events"].append(event_info)

                # 写回文件
                with open(json_file, "w", encoding="utf-8") as f:
                    json.dump(log_data, f, indent=2)

            except Exception as e:
                logger.error(f"写入JSON日志时错误: {e}")

    def _backup_action(self, config: Dict, event_info: Dict):
        """备份修改的文件"""
        # 忽略删除的文件和目录事件
        if (event_info["event_type"] == EventType.DELETED or
                event_info["file_type"] == FileType.DIRECTORY):
            return

        source_path = event_info["path"]
        if not os.path.exists(source_path):
            return

        # 确定备份目录
        backup_dir = config.get("target", "file_monitor_backups")
        os.makedirs(backup_dir, exist_ok=True)

        # 创建备份文件名
        filename = os.path.basename(source_path)
        timestamp = datetime.datetime.now().strftime("%Y%m%d%H%M%S")
        backup_name = f"{filename}.{timestamp}"

        # 确保备份路径不存在
        backup_path = os.path.join(backup_dir, backup_name)
        counter = 1
        while os.path.exists(backup_path):
            backup_name = f"{filename}.{timestamp}_{counter}"
            backup_path = os.path.join(backup_dir, backup_name)
            counter += 1

        # 复制文件
        try:
            shutil.copy2(source_path, backup_path)
            logger.info(f"已备份: {source_path} -> {backup_path}")
        except Exception as e:
            logger.error(f"备份失败: {source_path} - {e}")

    def _execute_command(self, config: Dict, event_info: Dict):
        """执行命令"""
        command_template = config.get("command", "")
        if not command_template:
            return

        # 替换占位符
        command = command_template
        command = command.replace("{path}", event_info["path"])
        command = command.replace("{filename}", os.path.basename(event_info["path"]))
        command = command.replace("{event_type}", event_info["event_type"].value)
        command = command.replace("{file_type}", event_info["file_type"].value)

        if event_info["event_type"] == EventType.MOVED:
            command = command.replace("{dest_path}", event_info["dest_path"])
            command = command.replace("{dest_filename}", os.path.basename(event_info["dest_path"]))

        # 执行命令
        try:
            logger.info(f"执行命令: {command}")
            result = subprocess.run(
                command,
                shell=True,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True
            )

            if result.returncode == 0:
                logger.debug(f"命令执行成功: {result.stdout}")
            else:
                logger.error(f"命令执行失败 (代码: {result.returncode}): {result.stderr}")

        except Exception as e:
            logger.error(f"执行命令时出错: {e}")

    def _send_notification(self, config: Dict, event_info: Dict):
        """发送通知"""
        notification_type = config.get("type", "console")

        # 创建通知消息
        filename = os.path.basename(event_info["path"])
        message = f"文件变化: {event_info['event_type'].value} {filename}"

        if notification_type == "console":
            print("\n" + "=" * 50)
            print(f"通知: {message}")
            print("=" * 50)

        elif notification_type == "desktop" and config.get("enabled", True):
            try:
                self._send_desktop_notification(message, config)
            except Exception as e:
                logger.error(f"发送桌面通知失败: {e}")

        # 可以扩展其他通知类型，如邮件、API等

    @staticmethod
    def _send_desktop_notification(message, config):
        """发送桌面通知"""
        title = config.get("title", "文件监控通知")

        # 尝试使用不同平台的通知方式
        if sys.platform == "win32":
            try:
                from win10toast import ToastNotifier
                toaster = ToastNotifier()
                toaster.show_toast(title, message, duration=5)
                return
            except ImportError:
                # 尝试使用Powershell
                ps_cmd = f'powershell -command "New-BurntToastNotification -Text \'{title}\', \'{message}\'"'
                subprocess.run(ps_cmd, shell=True)

        elif sys.platform == "darwin":  # macOS
            cmd = f'''osascript -e 'display notification "{message}" with title "{title}"' '''
            subprocess.run(cmd, shell=True)

        elif sys.platform.startswith("linux"):
            cmd = f'notify-send "{title}" "{message}"'
            subprocess.run(cmd, shell=True)

    def _update_stats(self, event_type: EventType):
        """更新统计信息"""
        self.stats["events_processed"] += 1
        self.stats["events_by_type"][event_type.value] += 1

    def _log_stats(self):
        """记录统计信息"""
        self.stats["ended_at"] = datetime.datetime.now().isoformat()
        runtime = (datetime.datetime.fromisoformat(self.stats["ended_at"]) -
                   datetime.datetime.fromisoformat(self.stats["started_at"])).total_seconds()
        self.stats["runtime_seconds"] = runtime

        logger.info(f"监控统计: 处理了 {self.stats['events_processed']} 个事件，运行时间 {runtime:.1f} 秒")
        logger.info(f"事件类型: 创建={self.stats['events_by_type']['created']}, "
                    f"修改={self.stats['events_by_type']['modified']}, "
                    f"删除={self.stats['events_by_type']['deleted']}, "
                    f"移动={self.stats['events_by_type']['moved']}")


class MonitorEventHandler(FileSystemEventHandler):
    """文件系统事件处理器类"""

    def __init__(self, monitor: FileMonitor):
        self.monitor = monitor
        super().__init__()

    def on_any_event(self, event):
        """处理任何类型的文件系统事件"""
        self.monitor.handle_event(event)


def parse_size(size_str: str) -> int:
    """解析大小字符串为字节数"""
    if not size_str:
        return 0

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


def parse_arguments():
    """解析命令行参数"""
    parser = argparse.ArgumentParser(description="文件监控工具")

    # 基本参数
    parser.add_argument('paths', nargs='+', help='要监控的路径列表')
    parser.add_argument('-r', '--recursive', action='store_true', default=True,
                        help='递归监控子目录（默认启用）')
    parser.add_argument('--no-recursive', action='store_false', dest='recursive',
                        help='不递归监控子目录')
    parser.add_argument('-t', '--timeout', type=int, default=0,
                        help='监控超时时间（秒），0表示一直运行（默认）')

    # 过滤选项
    filter_group = parser.add_argument_group('过滤选项')
    filter_group.add_argument('-i', '--include', nargs='+',
                              help='要包含的文件模式列表（如 *.txt *.log）')
    filter_group.add_argument('-e', '--exclude', nargs='+',
                              help='要排除的文件模式列表（如 *.tmp *.bak）')
    filter_group.add_argument('--include-hidden', action='store_true',
                              help='包括隐藏文件')
    filter_group.add_argument('--event-types', nargs='+',
                              choices=['created', 'modified', 'deleted', 'moved', 'all'],
                              default=['all'], help='要监控的事件类型列表')
    filter_group.add_argument('--file-types', nargs='+',
                              choices=['file', 'directory', 'all'],
                              default=['all'], help='要监控的文件类型列表')
    filter_group.add_argument('--min-size', type=str, default='0',
                              help='最小文件大小，如 1KB、2MB（默认: 0）')
    filter_group.add_argument('--max-size', type=str,
                              help='最大文件大小，如 10MB、1GB')
    filter_group.add_argument('--cooldown', type=int, default=1,
                              help='相同文件两次事件间的最小冷却时间（秒）（默认: 1）')

    # 批处理选项
    batch_group = parser.add_argument_group('批处理选项')
    batch_group.add_argument('--batch', action='store_true',
                             help='批处理模式，收集一段时间内的事件后一次处理')
    batch_group.add_argument('--batch-timeout', type=int, default=5,
                             help='批处理超时时间（秒）（默认: 5）')

    # 操作选项
    action_group = parser.add_argument_group('操作选项')
    action_group.add_argument('-l', '--log', choices=['console', 'file'], default='console',
                              help='日志输出目标（默认: console）')
    action_group.add_argument('--log-file',
                              help='日志文件路径（当--log=file时使用）')
    action_group.add_argument('--json-log',
                              help='JSON格式日志文件路径')
    action_group.add_argument('-b', '--backup', action='store_true',
                              help='备份修改的文件')
    action_group.add_argument('--backup-dir',
                              help='备份目录路径（默认: file_monitor_backups）')
    action_group.add_argument('-c', '--command',
                              help='文件变化时执行的命令，可使用{path}、{filename}等占位符')
    action_group.add_argument('-n', '--notify', action='store_true',
                              help='启用桌面通知')

    # 其他选项
    other_group = parser.add_argument_group('其他选项')
    other_group.add_argument('-q', '--quiet', action='store_true',
                             help='静默模式，减少输出')
    other_group.add_argument('-v', '--verbose', action='store_true',
                             help='详细模式，显示更多信息')

    return parser.parse_args()


def main():
    """主函数"""
    args = parse_arguments()

    # 配置日志级别
    if args.quiet:
        logging.getLogger().setLevel(logging.WARNING)
    elif args.verbose:
        logging.getLogger().setLevel(logging.DEBUG)

    # 准备事件类型
    event_types = [EventType(et) for et in args.event_types]

    # 准备文件类型
    file_types = [FileType(ft) for ft in args.file_types]

    # 准备操作配置
    actions = {}

    # 日志操作
    if args.log == 'console':
        actions["log"] = {"target": "console"}
    elif args.log == 'file':
        log_file = args.log_file or "file_monitor.log"
        actions["log"] = {"target": f"file:{log_file}"}

    # JSON日志
    if args.json_log:
        actions["log"] = {"target": "json", "file": args.json_log}

    # 备份操作
    if args.backup:
        backup_dir = args.backup_dir or "file_monitor_backups"
        actions["backup"] = {"target": backup_dir}

    # 命令执行操作
    if args.command:
        actions["execute"] = {"command": args.command}

    # 通知操作
    if args.notify:
        actions["notify"] = {"type": "desktop", "title": "文件监控通知"}

    # 解析文件大小
    min_size = parse_size(args.min_size)
    max_size = parse_size(args.max_size) if args.max_size else None

    # 创建监控配置
    config = MonitorConfig(
        paths=args.paths,
        recursive=args.recursive,
        include_patterns=args.include,
        exclude_patterns=args.exclude,
        include_hidden=args.include_hidden,
        event_types=event_types,
        file_types=file_types,
        actions=actions,
        min_size=min_size,
        max_size=max_size,
        cooldown=args.cooldown,
        batch_mode=args.batch,
        batch_timeout=args.batch_timeout
    )

    # 创建并启动监控器
    monitor = FileMonitor(config)

    # 设置信号处理
    def signal_handler(sig, frame):
        logger.info("接收到停止信号，正在停止监控...")
        monitor.stop()
        sys.exit(0)

    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)

    try:
        # 启动监控
        monitor.start()

        # 如果设置了超时，则在指定时间后停止
        if args.timeout > 0:
            logger.info(f"监控将在 {args.timeout} 秒后自动停止")
            time.sleep(args.timeout)
            monitor.stop()
        else:
            # 否则一直运行，直到被中断
            logger.info("监控中... 按Ctrl+C停止")
            while True:
                time.sleep(1)

    except Exception as e:
        logger.error(f"监控过程中发生错误: {e}")
        if args.verbose:
            import traceback
            traceback.print_exc()
        return 1
    finally:
        # 确保监控停止
        monitor.stop()

    return 0


if __name__ == "__main__":
    sys.exit(main())
