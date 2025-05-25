# 网络工具集

这个目录包含了用于网络测试和管理的实用工具脚本。

## network_speed_test.py - 网络速度测试工具

这个脚本可以测试网络连接的各项性能指标，包括下载速度、上传速度、延迟(ping)等，并支持结果可视化和历史数据记录。

### 功能特点

- 测试网络下载速度、延迟(ping)和丢包率
- 支持多服务器测试（默认使用Cloudflare和Google DNS服务器）
- 记录历史测试结果，方便追踪网络性能变化
- 支持以表格形式显示测试结果
- 支持绘制历史数据趋势图表
- 可自定义测试参数（如测试大小、次数等）

### 使用依赖

使用此脚本需要安装以下Python库：

```bash
pip install requests tabulate
```

如果需要绘制历史数据图表，还需要安装：

```bash
pip install matplotlib
```

### 使用方法

基本用法（测试下载速度和延迟）：
```bash
python network_speed_test.py
```

测试全部指标（包括上传速度）：
```bash
python network_speed_test.py -a
```

只测试网络延迟：
```bash
python network_speed_test.py -p
```

查看历史测试记录：
```bash
python network_speed_test.py --history
```

绘制下载速度历史趋势图：
```bash
python network_speed_test.py --plot download
```

查看最近5条历史记录：
```bash
python network_speed_test.py --history --last 5
```

### 完整命令行参数

```
usage: network_speed_test.py [-h] [-d] [-u] [-p] [-a] [--history]
                            [--plot {download,upload,ping}] [--last LAST]

网络速度测试工具

options:
  -h, --help            显示帮助信息并退出
  -d, --download        测试下载速度
  -u, --upload          测试上传速度
  -p, --ping            测试网络延迟(ping)
  -a, --all             测试全部指标
  --history             显示历史测试结果
  --plot {download,upload,ping}
                        绘制历史数据图表
  --last LAST           显示最近N条历史记录(用于--history和--plot)
```

### 历史数据存储

测试结果将保存在用户主目录的 `.network_speed_history.json` 文件中，方便追踪网络性能变化。 