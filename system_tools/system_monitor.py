#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
系统资源监控工具

这个脚本可以实时监控并显示系统资源使用情况，包括CPU、内存、磁盘和网络等。
可以通过命令行参数自定义监控行为，并支持导出监控数据到文件。
"""

import psutil
import time
import argparse
import os
import sys
import datetime
import platform
import logging
import csv
from tabulate import tabulate
from pathlib import Path

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)

class SystemMonitor:
    """系统监控类，负责收集和显示系统资源信息"""
    
    def __init__(self, interval=1.0, log_file=None, export_csv=None):
        """
        初始化系统监控器
        
        Args:
            interval (float): 监控信息刷新间隔（秒）
            log_file (str): 日志文件路径，None表示不记录日志
            export_csv (str): CSV导出文件路径，None表示不导出数据
        """
        self.interval = interval
        self.log_file = log_file
        self.export_csv = export_csv
        self.csv_file = None
        self.csv_writer = None
        
        # 如果指定了CSV导出，则初始化CSV文件
        if export_csv:
            try:
                self.csv_file = open(export_csv, 'w', newline='', encoding='utf-8')
                self.csv_writer = csv.writer(self.csv_file)
                self.csv_writer.writerow([
                    '时间', 'CPU使用率(%)', '内存使用率(%)', '已用内存(GB)', '总内存(GB)',
                    '磁盘使用率(%)', '已用空间(GB)', '总空间(GB)', '网络发送(KB/s)', '网络接收(KB/s)'
                ])
            except Exception as e:
                logging.error(f"无法创建CSV文件: {str(e)}")
                self.export_csv = None
        
        # 系统信息
        self.system_info = self.get_system_info()
        
        # 获取初始网络数据，用于计算速率
        self.last_net_io = psutil.net_io_counters()
        self.last_net_time = time.time()
    
    def __del__(self):
        """析构函数，关闭文件句柄"""
        if self.csv_file:
            self.csv_file.close()
    
    def get_system_info(self):
        """获取系统基本信息"""
        info = {}
        info['系统'] = platform.system()
        info['发行版'] = platform.release()
        info['架构'] = platform.machine()
        info['处理器'] = platform.processor()
        info['主机名'] = platform.node()
        info['Python版本'] = platform.python_version()
        
        # CPU信息
        info['CPU核心数(物理)'] = psutil.cpu_count(logical=False)
        info['CPU核心数(逻辑)'] = psutil.cpu_count(logical=True)
        
        # 内存信息
        mem = psutil.virtual_memory()
        info['总内存'] = f"{mem.total / (1024**3):.2f} GB"
        
        # 磁盘信息
        disks = []
        for part in psutil.disk_partitions(all=False):
            if os.name == 'nt':
                if 'cdrom' in part.opts or part.fstype == '':
                    # 跳过光驱
                    continue
            
            usage = psutil.disk_usage(part.mountpoint)
            disks.append({
                '设备': part.device,
                '挂载点': part.mountpoint,
                '文件系统': part.fstype,
                '总容量': f"{usage.total / (1024**3):.2f} GB"
            })
        info['磁盘'] = disks
        
        return info
    
    def get_cpu_info(self):
        """获取CPU使用情况"""
        return {
            'cpu_percent': psutil.cpu_percent(interval=0.1),
            'cpu_per_core': psutil.cpu_percent(interval=0.1, percpu=True)
        }
    
    def get_memory_info(self):
        """获取内存使用情况"""
        mem = psutil.virtual_memory()
        return {
            'total': mem.total,
            'available': mem.available,
            'used': mem.used,
            'percent': mem.percent
        }
    
    def get_disk_info(self):
        """获取磁盘使用情况"""
        # 获取指定路径的磁盘使用情况，默认为根目录
        root_path = "C:\\" if os.name == 'nt' else "/"
        disk = psutil.disk_usage(root_path)
        return {
            'total': disk.total,
            'used': disk.used,
            'free': disk.free,
            'percent': disk.percent
        }
    
    def get_network_info(self):
        """获取网络使用情况"""
        current_net_io = psutil.net_io_counters()
        current_time = time.time()
        
        # 计算时间差
        time_diff = current_time - self.last_net_time
        
        # 避免除零错误
        if time_diff <= 0:
            return {'sent': 0, 'recv': 0}
        
        # 计算速率（KB/s）
        sent_rate = (current_net_io.bytes_sent - self.last_net_io.bytes_sent) / time_diff / 1024
        recv_rate = (current_net_io.bytes_recv - self.last_net_io.bytes_recv) / time_diff / 1024
        
        # 更新上次数据
        self.last_net_io = current_net_io
        self.last_net_time = current_time
        
        return {
            'sent': sent_rate,
            'recv': recv_rate
        }
    
    def print_system_info(self):
        """打印系统基本信息"""
        print("\n=== 系统信息 ===")
        for key, value in self.system_info.items():
            if key == '磁盘':
                print(f"\n{key}:")
                for disk in value:
                    for dk, dv in disk.items():
                        print(f"  {dk}: {dv}")
                    print()
            else:
                print(f"{key}: {value}")
    
    def collect_data(self):
        """收集当前系统资源使用数据"""
        cpu_info = self.get_cpu_info()
        mem_info = self.get_memory_info()
        disk_info = self.get_disk_info()
        net_info = self.get_network_info()
        
        data = {
            'timestamp': datetime.datetime.now(),
            'cpu': cpu_info,
            'memory': mem_info,
            'disk': disk_info,
            'network': net_info
        }
        
        return data
    
    def format_data(self, data):
        """格式化监控数据用于显示"""
        timestamp = data['timestamp'].strftime('%H:%M:%S')
        cpu_percent = data['cpu']['cpu_percent']
        mem_percent = data['memory']['percent']
        mem_used_gb = data['memory']['used'] / (1024**3)
        mem_total_gb = data['memory']['total'] / (1024**3)
        disk_percent = data['disk']['percent']
        disk_used_gb = data['disk']['used'] / (1024**3)
        disk_total_gb = data['disk']['total'] / (1024**3)
        net_sent = data['network']['sent']
        net_recv = data['network']['recv']
        
        return {
            'timestamp': timestamp,
            'cpu_percent': f"{cpu_percent:.1f}%",
            'mem_percent': f"{mem_percent:.1f}%",
            'mem_used_gb': f"{mem_used_gb:.2f}GB",
            'mem_total_gb': f"{mem_total_gb:.2f}GB",
            'disk_percent': f"{disk_percent:.1f}%",
            'disk_used_gb': f"{disk_used_gb:.2f}GB",
            'disk_total_gb': f"{disk_total_gb:.2f}GB",
            'net_sent': f"{net_sent:.2f}KB/s",
            'net_recv': f"{net_recv:.2f}KB/s"
        }
    
    def export_data(self, data):
        """导出监控数据到CSV文件"""
        if not self.csv_writer:
            return
            
        try:
            self.csv_writer.writerow([
                data['timestamp'].strftime('%Y-%m-%d %H:%M:%S'),
                f"{data['cpu']['cpu_percent']:.1f}",
                f"{data['memory']['percent']:.1f}",
                f"{data['memory']['used'] / (1024**3):.2f}",
                f"{data['memory']['total'] / (1024**3):.2f}",
                f"{data['disk']['percent']:.1f}",
                f"{data['disk']['used'] / (1024**3):.2f}",
                f"{data['disk']['total'] / (1024**3):.2f}",
                f"{data['network']['sent']:.2f}",
                f"{data['network']['recv']:.2f}"
            ])
            self.csv_file.flush()
        except Exception as e:
            logging.error(f"导出数据失败: {str(e)}")
    
    def display_data(self, data):
        """在控制台显示格式化的监控数据"""
        formatted = self.format_data(data)
        
        # 准备表格数据
        headers = ['时间', 'CPU使用率', '内存使用率', '内存使用', '磁盘使用率', '磁盘使用', '网络发送', '网络接收']
        row = [
            formatted['timestamp'],
            formatted['cpu_percent'],
            formatted['mem_percent'],
            f"{formatted['mem_used_gb']}/{formatted['mem_total_gb']}",
            formatted['disk_percent'],
            f"{formatted['disk_used_gb']}/{formatted['disk_total_gb']}",
            formatted['net_sent'],
            formatted['net_recv']
        ]
        
        # 清屏并显示
        os.system('cls' if os.name == 'nt' else 'clear')
        print("\n=== 系统资源监控 ===")
        print(tabulate([row], headers=headers, tablefmt="pretty"))
        
        # 显示CPU核心详情
        cpu_per_core = data['cpu']['cpu_per_core']
        print("\nCPU核心使用率:")
        core_data = []
        for i in range(0, len(cpu_per_core), 4):
            # 每行显示4个核心
            row = []
            for j in range(i, min(i + 4, len(cpu_per_core))):
                row.append(f"核心{j}: {cpu_per_core[j]:.1f}%")
            core_data.append(row)
        print(tabulate(core_data, tablefmt="plain"))
    
    def run(self, duration=None, display=True):
        """
        运行监控
        
        Args:
            duration (int): 监控持续时间（秒）, None表示持续运行直到用户中断
            display (bool): 是否在控制台显示监控数据
        """
        if display:
            self.print_system_info()
            print("\n按 Ctrl+C 停止监控...")
        
        start_time = time.time()
        try:
            while True:
                # 收集数据
                data = self.collect_data()
                
                # 显示数据
                if display:
                    self.display_data(data)
                
                # 导出数据
                if self.export_csv:
                    self.export_data(data)
                
                # 检查是否达到指定运行时间
                if duration and (time.time() - start_time) >= duration:
                    break
                
                time.sleep(self.interval)
                
        except KeyboardInterrupt:
            print("\n监控已停止")
        finally:
            if self.export_csv:
                print(f"\n监控数据已保存至: {self.export_csv}")


def main():
    """主函数"""
    parser = argparse.ArgumentParser(description="系统资源监控工具")
    parser.add_argument("-i", "--interval", type=float, default=2.0,
                      help="监控数据刷新间隔（秒），默认为2秒")
    parser.add_argument("-d", "--duration", type=int, help="监控持续时间（秒），默认无限制")
    parser.add_argument("-e", "--export", help="导出监控数据到CSV文件")
    parser.add_argument("-q", "--quiet", action="store_true", help="静默模式，不在控制台显示数据")
    
    args = parser.parse_args()
    
    # 简单的参数检查
    if args.interval < 0.5:
        logging.warning("刷新间隔过短可能导致性能问题，已自动调整为0.5秒")
        args.interval = 0.5
    
    # 创建和运行监控器
    monitor = SystemMonitor(interval=args.interval, export_csv=args.export)
    monitor.run(duration=args.duration, display=not args.quiet)


if __name__ == "__main__":
    # 检查是否安装了必要的依赖
    try:
        import psutil
        import tabulate
    except ImportError:
        print("\n错误: 缺少必要的依赖。")
        print("请安装所需的依赖包:")
        print("pip install psutil tabulate\n")
        sys.exit(1)
    
    main() 