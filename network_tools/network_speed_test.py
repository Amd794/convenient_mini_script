#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
网络速度测试工具

这个脚本可以测试网络连接的各项性能指标，包括下载速度、上传速度、延迟(ping)等，
可以指定测试服务器，并支持结果可视化和历史数据记录。
"""

import argparse
import datetime
import json
import logging
import os
import socket
import statistics
import sys
import time

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)

# 默认配置
DEFAULT_CONFIG = {
    "servers": [
        {
            "name": "Cloudflare",
            "url": "https://speed.cloudflare.com/__down?bytes=100000000",
            "ping_host": "1.1.1.1"
        },
        {
            "name": "Google",
            "url": "https://speed.cloudflare.com/__down?bytes=100000000",  # 替代Google服务器，因为Google没有开放速度测试API
            "ping_host": "8.8.8.8"
        }
    ],
    "download_size": 10,  # MB
    "upload_size": 5,  # MB
    "ping_count": 10,
    "history_file": "~/.network_speed_history.json"
}


class NetworkSpeedTest:
    """网络速度测试类，提供测试和结果处理功能"""

    def __init__(self, config=None):
        """
        初始化网络速度测试工具
        
        Args:
            config (dict): 配置字典，包含测试参数和服务器列表
        """
        self.config = config or DEFAULT_CONFIG
        self.results = {}
        self.history = []

        # 扩展历史文件路径
        self.history_file = os.path.expanduser(self.config.get('history_file'))

        # 加载历史数据
        self._load_history()

    def _load_history(self):
        """加载历史测试数据"""
        if os.path.exists(self.history_file):
            try:
                with open(self.history_file, 'r') as f:
                    self.history = json.load(f)
            except Exception as e:
                logging.warning(f"无法加载历史数据: {str(e)}")

    def _save_history(self):
        """保存历史测试数据"""
        try:
            # 确保目录存在
            os.makedirs(os.path.dirname(os.path.abspath(self.history_file)), exist_ok=True)

            with open(self.history_file, 'w') as f:
                json.dump(self.history, f, ensure_ascii=False, indent=2)
        except Exception as e:
            logging.error(f"无法保存历史数据: {str(e)}")

    def test_ping(self, host, count=10, timeout=2):
        """
        测试网络延迟(ping)
        
        Args:
            host (str): 目标主机名或IP
            count (int): ping次数
            timeout (int): 超时时间(秒)
            
        Returns:
            dict: 包含最小、最大、平均延迟和丢包率的字典
        """
        results = []
        lost = 0

        for i in range(count):
            try:
                start_time = time.time()

                # 创建socket连接来测试延迟，替代系统ping命令
                s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                s.settimeout(timeout)

                connect_start = time.time()
                s.connect((host, 80))
                connect_time = (time.time() - connect_start) * 1000  # 毫秒

                s.close()
                results.append(connect_time)

                # 适当的间隔
                time.sleep(0.2)

            except socket.error:
                lost += 1

        # 计算结果
        if not results:
            return {
                "min": None,
                "max": None,
                "avg": None,
                "loss": 100.0
            }

        return {
            "min": min(results),
            "max": max(results),
            "avg": sum(results) / len(results),
            "mdev": statistics.stdev(results) if len(results) > 1 else 0,
            "loss": (lost / count) * 100
        }

    def test_download_speed(self, url, size_mb=10):
        """
        测试下载速度
        
        Args:
            url (str): 测试下载的URL
            size_mb (int): 下载的大小(MB)
            
        Returns:
            float: 下载速度(MB/s)
        """
        try:
            # 在URL中指定下载大小(如果API支持)
            adjusted_url = url

            start_time = time.time()

            # 发送请求并获取响应
            response = requests.get(adjusted_url, stream=True, timeout=30)
            downloaded = 0

            # 分块读取响应
            for chunk in response.iter_content(chunk_size=1024 * 1024):  # 1MB
                downloaded += len(chunk)

                # 如果已达到目标大小，则停止
                if downloaded >= size_mb * 1024 * 1024:
                    break

            # 计算下载时间和速度
            download_time = time.time() - start_time
            speed_mbps = downloaded / (1024 * 1024) / download_time  # MB/s

            return speed_mbps

        except Exception as e:
            logging.error(f"下载测试失败: {str(e)}")
            return None

    def test_upload_speed(self, url, size_mb=5):
        """
        测试上传速度
        
        Args:
            url (str): 测试上传的URL
            size_mb (int): 上传的数据大小(MB)
            
        Returns:
            float: 上传速度(MB/s)
        """
        try:
            # 创建测试数据
            data = b'0' * (size_mb * 1024 * 1024)  # 指定大小的数据

            start_time = time.time()

            # 发送POST请求上传数据
            response = requests.post(url, data=data, timeout=30)

            # 计算上传时间和速度
            upload_time = time.time() - start_time
            speed_mbps = size_mb / upload_time  # MB/s

            return speed_mbps

        except Exception as e:
            logging.error(f"上传测试失败: {str(e)}")
            return None

    def run_tests(self, servers=None, download=True, upload=False, ping=True):
        """
        运行网络测试
        
        Args:
            servers (list): 服务器配置列表，None表示使用默认服务器
            download (bool): 是否测试下载速度
            upload (bool): 是否测试上传速度
            ping (bool): 是否测试网络延迟
        """
        servers = servers or self.config.get('servers', [])
        results = {}

        # 测试每个服务器
        for server in servers:
            server_name = server.get('name', '未知服务器')
            print(f"\n正在测试 {server_name}...")

            server_results = {}

            # 测试PING
            if ping and 'ping_host' in server:
                print(f"测试网络延迟(ping) {server['ping_host']}...")
                ping_result = self.test_ping(
                    server['ping_host'],
                    count=self.config.get('ping_count', 10)
                )
                server_results['ping'] = ping_result

                if ping_result['avg'] is not None:
                    print(f"平均延迟: {ping_result['avg']:.2f}ms, "
                          f"丢包率: {ping_result['loss']:.1f}%")
                else:
                    print("PING测试失败")

            # 测试下载速度
            if download and 'url' in server:
                print(f"测试下载速度...")
                down_speed = self.test_download_speed(
                    server['url'],
                    size_mb=self.config.get('download_size', 10)
                )
                server_results['download'] = down_speed

                if down_speed is not None:
                    print(f"下载速度: {down_speed:.2f} MB/s "
                          f"({down_speed * 8:.2f} Mbps)")
                else:
                    print("下载测试失败")

            # 测试上传速度
            if upload and 'upload_url' in server:
                print(f"测试上传速度...")
                up_speed = self.test_upload_speed(
                    server['upload_url'],
                    size_mb=self.config.get('upload_size', 5)
                )
                server_results['upload'] = up_speed

                if up_speed is not None:
                    print(f"上传速度: {up_speed:.2f} MB/s "
                          f"({up_speed * 8:.2f} Mbps)")
                else:
                    print("上传测试失败")

            # 记录服务器结果
            results[server_name] = server_results

        self.results = {
            'timestamp': datetime.datetime.now().isoformat(),
            'servers': results
        }

        # 添加到历史记录
        self.history.append(self.results)

        # 保留最近的100条记录
        if len(self.history) > 100:
            self.history = self.history[-100:]

        # 保存历史记录
        self._save_history()

        return self.results

    def display_results(self):
        """在控制台显示测试结果"""
        if not self.results:
            print("没有测试结果可显示")
            return

        timestamp = datetime.datetime.fromisoformat(self.results['timestamp'])
        print(f"\n=== 网络速度测试结果 ({timestamp.strftime('%Y-%m-%d %H:%M:%S')}) ===")

        # 准备表格数据
        table_data = []

        for server_name, server_results in self.results['servers'].items():
            row = [server_name]

            # PING结果
            if 'ping' in server_results:
                ping = server_results['ping']
                if ping['avg'] is not None:
                    row.append(f"{ping['avg']:.2f} ms")
                    row.append(f"{ping['loss']:.1f}%")
                else:
                    row.append("失败")
                    row.append("100%")
            else:
                row.append("未测试")
                row.append("-")

            # 下载速度
            if 'download' in server_results:
                if server_results['download'] is not None:
                    row.append(f"{server_results['download']:.2f} MB/s")
                    row.append(f"{server_results['download'] * 8:.2f} Mbps")
                else:
                    row.append("失败")
                    row.append("-")
            else:
                row.append("未测试")
                row.append("-")

            # 上传速度
            if 'upload' in server_results:
                if server_results['upload'] is not None:
                    row.append(f"{server_results['upload']:.2f} MB/s")
                    row.append(f"{server_results['upload'] * 8:.2f} Mbps")
                else:
                    row.append("失败")
                    row.append("-")
            else:
                row.append("未测试")
                row.append("-")

            table_data.append(row)

        headers = ['服务器', '延迟', '丢包率', '下载速度', '下载(Mbps)', '上传速度', '上传(Mbps)']
        print(tabulate(table_data, headers=headers, tablefmt="fancy_grid"))

    def plot_history(self, metric='download', last_n=10):
        """
        绘制历史数据图表
        
        Args:
            metric (str): 要绘制的指标，可选值：'download', 'upload', 'ping'
            last_n (int): 显示最近的N条记录
        """
        if not self.history:
            print("没有历史数据可绘制")
            return

        try:
            import matplotlib.pyplot as plt

            # 准备数据
            timestamps = []
            values = {server['name']: [] for server in self.config['servers']}

            # 从历史记录提取数据
            for record in self.history[-last_n:]:
                timestamps.append(datetime.datetime.fromisoformat(record['timestamp']))

                for server_name, server_results in record['servers'].items():
                    if server_name in values:
                        if metric == 'ping' and 'ping' in server_results:
                            ping_result = server_results['ping']['avg']
                            values[server_name].append(ping_result if ping_result is not None else float('nan'))
                        elif metric == 'download' and 'download' in server_results:
                            values[server_name].append(server_results['download'] or float('nan'))
                        elif metric == 'upload' and 'upload' in server_results:
                            values[server_name].append(server_results['upload'] or float('nan'))
                        else:
                            values[server_name].append(float('nan'))

            # 创建图表
            plt.figure(figsize=(10, 6))

            for server_name, data in values.items():
                if any(not math.isnan(x) for x in data):  # 至少有一个有效数据
                    plt.plot(timestamps, data, marker='o', label=server_name)

            # 设置图表属性
            metric_labels = {
                'download': '下载速度 (MB/s)',
                'upload': '上传速度 (MB/s)',
                'ping': '网络延迟 (ms)'
            }

            plt.title(f"网络{metric_labels.get(metric, metric)}历史记录")
            plt.xlabel('时间')
            plt.ylabel(metric_labels.get(metric, metric))
            plt.grid(True)
            plt.legend()

            # 调整x轴日期格式
            plt.gcf().autofmt_xdate()

            # 显示图表
            plt.tight_layout()
            plt.show()

        except ImportError:
            print("绘制图表需要安装matplotlib库: pip install matplotlib")
        except Exception as e:
            logging.error(f"绘制图表失败: {str(e)}")


def main():
    """主函数"""
    parser = argparse.ArgumentParser(description="网络速度测试工具")
    parser.add_argument("-d", "--download", action="store_true", help="测试下载速度")
    parser.add_argument("-u", "--upload", action="store_true", help="测试上传速度")
    parser.add_argument("-p", "--ping", action="store_true", help="测试网络延迟(ping)")
    parser.add_argument("-a", "--all", action="store_true", help="测试全部指标")
    parser.add_argument("--history", action="store_true", help="显示历史测试结果")
    parser.add_argument("--plot", choices=['download', 'upload', 'ping'],
                        help="绘制历史数据图表")
    parser.add_argument("--last", type=int, default=10,
                        help="显示最近N条历史记录(用于--history和--plot)")

    args = parser.parse_args()

    # 默认测试下载和ping
    if not (args.download or args.upload or args.ping or args.all or args.history or args.plot):
        args.download = True
        args.ping = True

    if args.all:
        args.download = True
        args.upload = True
        args.ping = True

    # 实例化测试工具
    tester = NetworkSpeedTest()

    # 显示历史记录
    if args.history:
        if not tester.history:
            print("没有可用的历史记录")
        else:
            print(f"\n显示最近 {min(args.last, len(tester.history))} 条测试记录:\n")
            for record in tester.history[-args.last:]:
                timestamp = datetime.datetime.fromisoformat(record['timestamp'])
                print(f"测试时间: {timestamp.strftime('%Y-%m-%d %H:%M:%S')}")

                for server_name, results in record['servers'].items():
                    print(f"  服务器: {server_name}")

                    if 'ping' in results:
                        ping = results['ping']
                        if ping['avg'] is not None:
                            print(f"    延迟: {ping['avg']:.2f} ms, 丢包率: {ping['loss']:.1f}%")

                    if 'download' in results and results['download'] is not None:
                        print(f"    下载速度: {results['download']:.2f} MB/s "
                              f"({results['download'] * 8:.2f} Mbps)")

                    if 'upload' in results and results['upload'] is not None:
                        print(f"    上传速度: {results['upload']:.2f} MB/s "
                              f"({results['upload'] * 8:.2f} Mbps)")
                print()
        return

    # 绘制历史图表
    if args.plot:
        tester.plot_history(metric=args.plot, last_n=args.last)
        return

    # 运行测试
    tester.run_tests(download=args.download, upload=args.upload, ping=args.ping)

    # 显示结果
    tester.display_results()


if __name__ == "__main__":
    # 检查依赖
    try:
        import requests
        import tabulate
    except ImportError:
        print("\n错误: 缺少必要的依赖。")
        print("请安装所需的依赖包:")
        print("pip install requests tabulate\n")
        print("如果需要绘制历史图表，还需安装:")
        print("pip install matplotlib\n")
        sys.exit(1)

    try:
        import math  # 用于图表绘制时检查NaN值
    except ImportError:
        # math是Python标准库的一部分，一般不会导入失败
        pass

    main()
