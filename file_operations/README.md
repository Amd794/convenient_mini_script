# 文件操作脚本集

这个目录包含了用于文件操作的实用脚本。

## organize_files.py - 文件整理工具

这个脚本可以帮助你自动整理杂乱的文件夹，将文件按类型分类到不同的子文件夹中。

### 功能特点

- 支持多种常见文件类型的自动分类（图片、文档、音频、视频等）
- 生成详细的整理报告
- 可选择只生成报告而不移动文件
- 支持排除指定目录
- 可选择是否处理隐藏文件

### 使用方法

基本用法（整理当前目录）：
```bash
python organize_files.py
```

整理指定目录：
```bash
python organize_files.py D:\Downloads
```

仅生成报告而不移动文件：
```bash
python organize_files.py -r
```

排除某些目录：
```bash
python organize_files.py -e 图片 文档
```

包含隐藏文件：
```bash
python organize_files.py --include-hidden
```

### 完整命令行参数

```
usage: organize_files.py [-h] [-r] [-e EXCLUDE [EXCLUDE ...]] [--include-hidden] [directory]

文件整理工具 - 按类型整理文件

positional arguments:
  directory             要整理的目录路径，默认为当前目录

options:
  -h, --help            显示帮助信息并退出
  -r, --report-only     仅生成报告，不移动文件
  -e EXCLUDE [EXCLUDE ...], --exclude EXCLUDE [EXCLUDE ...]
                        排除的目录名列表
  --include-hidden      包括隐藏文件
``` 