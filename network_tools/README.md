<p align="center">
  <a href="./README_EN.md">English</a> |
  <a href="./README.md">简体中文</a> 
</p>

----

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

## 网络文件批量下载工具 (batch_downloader.py)

此工具用于批量下载网络文件，支持并发下载、断点续传、自动重试等功能。

### 功能特性

- 批量下载多个URL
- 支持并发下载提升效率
- 断点续传功能
- 下载失败自动重试
- 详细的进度显示
- 支持从文件读取URL列表
- 自定义HTTP头
- 详细的下载统计信息
- 支持自定义文件名和后缀
- 根据Content-Type自动添加文件扩展名
- 强制使用指定文件后缀，忽略URL中的后缀
- 支持随机延时，避免被网站识别为爬虫
- 支持保存下载状态，断开后继续下载

### 使用方法

```bash
python batch_downloader.py [URL...] [选项]

选项:
  -f, --file FILE         包含URL列表的文件，每行一个URL
  -o, --output-dir DIR    下载文件保存目录 (默认: ./downloads)
  -w, --workers NUMBER    并发下载数 (默认: 5)
  -t, --timeout SECONDS   连接超时时间 (默认: 30秒)
  -r, --retries NUMBER    下载失败重试次数 (默认: 3)
  -s, --suffix EXT        默认文件后缀，当URL无法确定文件类型时使用
  --force-suffix          强制使用指定的文件后缀，忽略URL中的后缀
  --name-map FILE         URL到文件名映射文件(JSON或CSV格式)
  --no-verify             不验证SSL证书
  --no-resume             禁用断点续传
  --overwrite             覆盖已存在的文件
  --header HEADER         添加HTTP头，格式为 'Name: Value'
  --debug                 启用调试日志
  --no-progress           不显示进度条
  --random-delay          启用随机延时，避免被检测为爬虫
  --min-delay SECONDS     随机延时的最小秒数 (默认: 1.0)
  --max-delay SECONDS     随机延时的最大秒数 (默认: 5.0)
  --continue              继续上次未完成的下载
  --state-file FILE       下载状态保存文件路径
```

### 示例

```bash
# 下载单个文件
python batch_downloader.py https://example.com/file.zip

# 从文本文件批量下载URL
python batch_downloader.py -f urls.txt -o ./downloads

# 使用10个并发连接下载
python batch_downloader.py -f urls.txt -w 10

# 为所有无后缀文件添加.mp4后缀
python batch_downloader.py -f urls.txt -s mp4

# 强制将所有文件保存为.torrent格式，忽略URL中的后缀
python batch_downloader.py -f urls.txt -s torrent --force-suffix

# 使用映射文件指定文件名
python batch_downloader.py -f urls.txt --name-map mappings.json

# 添加自定义HTTP头并启用随机延时
python batch_downloader.py -f urls.txt --header "Referer: https://example.com" --random-delay

# 继续上次未完成的下载
python batch_downloader.py -f urls.txt --continue
```

### 文件名映射

您可以使用JSON或CSV格式的映射文件来为每个URL指定自定义文件名：

- **JSON格式**：
```json
{
  "https://example.com/file1": "自定义文件名1.mp4",
  "https://example.com/file2": "自定义文件名2.pdf"
}
```

- **CSV格式**：
```csv
https://example.com/file1,自定义文件名1.mp4
https://example.com/file2,自定义文件名2.pdf
```

### 依赖

- Python 3.7+
- httpx
- tqdm (可选，用于进度显示)

安装依赖：
```bash
pip install httpx tqdm
``` 