<p align="center">
  <a href="./README_EN.md">English</a> |
  <a href="./README.md">简体中文</a> 
</p>

----

# 开发辅助工具集

这个目录包含了用于辅助软件开发的实用工具脚本。

## code_analyzer.py - 代码分析工具

这个脚本可以分析代码库的结构、统计代码量、评估复杂度等，支持多种编程语言，可生成可视化报告，帮助开发者了解代码库情况。

### 功能特点

- 支持多种编程语言（Python、JavaScript、Java、C/C++、HTML、CSS等）
- 统计代码行数、注释行数和空行数
- 计算注释率和代码复杂度
- 检测过长的代码行
- 生成详细的HTML分析报告（包含交互式图表）
- 可选生成可视化图表
- 可自定义排除目录和文件类型

### 使用依赖

基本功能需要的依赖：
```bash
pip install tabulate
```

可视化图表功能需要的依赖：
```bash
pip install matplotlib numpy
```

### 使用方法

基本用法（分析当前目录）：
```bash
python code_analyzer.py
```

分析指定目录：
```bash
python code_analyzer.py /path/to/your/project
```

生成HTML报告并指定输出文件：
```bash
python code_analyzer.py -o report.html
```

生成可视化图表：
```bash
python code_analyzer.py -c
```

排除指定目录：
```bash
python code_analyzer.py -e node_modules build dist
```

排除指定文件模式：
```bash
python code_analyzer.py -f "*.min.js" "*.generated.*"
```

自定义最大行长度（超过视为过长）：
```bash
python code_analyzer.py -l 80
```

### 完整命令行参数

```
usage: code_analyzer.py [-h] [-o OUTPUT] [-e EXCLUDE_DIRS [EXCLUDE_DIRS ...]]
                        [-f EXCLUDE_FILES [EXCLUDE_FILES ...]] [-l LINE_LENGTH] [-c]
                        [path]

代码分析工具 - 分析代码库结构和统计

positional arguments:
  path                  要分析的代码库路径，默认为当前目录

options:
  -h, --help            显示帮助信息并退出
  -o OUTPUT, --output OUTPUT
                        输出报告的文件路径
  -e EXCLUDE_DIRS [EXCLUDE_DIRS ...], --exclude-dirs EXCLUDE_DIRS [EXCLUDE_DIRS ...]
                        要排除的目录名列表
  -f EXCLUDE_FILES [EXCLUDE_FILES ...], --exclude-files EXCLUDE_FILES [EXCLUDE_FILES ...]
                        要排除的文件模式列表
  -l LINE_LENGTH, --line-length LINE_LENGTH
                        最大行长度，超过视为过长
  -c, --charts          生成可视化图表
```

### 分析报告示例

生成的HTML报告包含：
- 代码库的总体统计信息（总文件数、代码行数、注释行数等）
- 各编程语言的详细统计数据
- 代码组成分析图表（代码行、注释行、空行的比例）
- 各语言代码行数分布图表
- 各语言复杂度评分图表