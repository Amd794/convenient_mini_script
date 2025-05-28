<p align="center">
  <a href="./README_EN.md">English</a> |
  <a href="./README.md">简体中文</a> 
</p>

----

# 系统工具集

这个目录包含了用于系统监控和管理的实用工具脚本。

## system_monitor.py - 系统资源监控工具

这个脚本可以实时监控系统资源使用情况，包括CPU、内存、磁盘和网络等，并支持将监控数据导出到CSV文件。

### 功能特点

- 实时显示系统资源使用情况（CPU、内存、磁盘、网络）
- 支持按核心显示CPU使用率
- 支持导出监控数据到CSV文件
- 支持自定义监控间隔和持续时间
- 提供静默模式，可在后台收集数据

### 使用依赖

使用此脚本需要安装以下Python库：

```bash
pip install psutil tabulate
```

### 使用方法

基本用法（实时监控系统资源）：
```bash
python system_monitor.py
```

指定数据刷新间隔（单位：秒）：
```bash
python system_monitor.py -i 5
```

设置监控持续时间（单位：秒）：
```bash
python system_monitor.py -d 3600  # 监控1小时后自动停止
```

导出监控数据到CSV文件：
```bash
python system_monitor.py -e system_stats.csv
```

静默模式，不显示输出但记录数据：
```bash
python system_monitor.py -q -e system_stats.csv
```

### 完整命令行参数

```
usage: system_monitor.py [-h] [-i INTERVAL] [-d DURATION] [-e EXPORT] [-q]

系统资源监控工具

options:
  -h, --help            显示帮助信息并退出
  -i INTERVAL, --interval INTERVAL
                        监控数据刷新间隔（秒），默认为2秒
  -d DURATION, --duration DURATION
                        监控持续时间（秒），默认无限制
  -e EXPORT, --export EXPORT
                        导出监控数据到CSV文件
  -q, --quiet           静默模式，不在控制台显示数据
```

### CSV输出格式

导出的CSV文件包含以下列：
- 时间 - 数据记录时间戳
- CPU使用率(%) - 总体CPU使用百分比
- 内存使用率(%) - 内存使用百分比
- 已用内存(GB) - 已使用内存大小
- 总内存(GB) - 总内存大小
- 磁盘使用率(%) - 磁盘使用百分比
- 已用空间(GB) - 已使用磁盘空间
- 总空间(GB) - 总磁盘空间
- 网络发送(KB/s) - 网络发送速率
- 网络接收(KB/s) - 网络接收速率 