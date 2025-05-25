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

## batch_rename.py - 批量文件重命名工具

这个脚本提供了多种方式来批量重命名文件，支持多种重命名模式、文件筛选、预览和撤销功能。

### 功能特点

- **多种重命名模式**:
  - 添加前缀/后缀
  - 添加序列号
  - 添加日期时间（文件修改时间或当前时间）
  - 正则表达式替换
  - 更改文件名大小写
  - 替换空格为指定字符
- **高级文件筛选**:
  - 按文件扩展名筛选
  - 按文件大小范围筛选
  - 使用正则表达式排除文件
- **安全操作**:
  - 预览重命名效果
  - 检测和提示命名冲突
  - 自动备份被覆盖的文件
- **操作历史**:
  - 保存重命名操作历史
  - 支持撤销之前的重命名操作

### 基本使用方法

添加前缀：
```bash
python batch_rename.py --add-prefix "New_" 
```

添加后缀（在扩展名前）：
```bash
python batch_rename.py --add-suffix "_edited" --before-ext
```

添加序列号：
```bash
python batch_rename.py --add-sequence --start-num 1 --padding 3
```

按修改日期重命名：
```bash
python batch_rename.py --add-date --use-file-time
```

正则表达式替换：
```bash
python batch_rename.py --replace "(\d+)" "num_$1"
```

更改文件名大小写：
```bash
python batch_rename.py --change-case upper
```

替换文件名中的空格：
```bash
python batch_rename.py --replace-spaces "_"
```

### 高级用法示例

仅处理特定扩展名：
```bash
python batch_rename.py --add-prefix "Image_" -e jpg png gif
```

递归处理子目录：
```bash
python batch_rename.py --add-date -r
```

预览而不实际重命名：
```bash
python batch_rename.py --add-sequence --dry-run
```

筛选大小范围的文件：
```bash
python batch_rename.py --add-prefix "Large_" --min-size 1048576
```

查看历史重命名操作：
```bash
python batch_rename.py --list-history
```

撤销之前的重命名操作：
```bash
python batch_rename.py --undo 1
```

### 完整命令行参数

```
usage: batch_rename.py [-h] [-r] [--dry-run] [-e EXTENSIONS [EXTENSIONS ...]]
                      [--min-size MIN_SIZE] [--max-size MAX_SIZE]
                      [--exclude EXCLUDE] [--add-prefix PREFIX | --add-suffix SUFFIX |
                      --add-sequence | --add-date | --replace PATTERN REPLACEMENT |
                      --change-case {upper,lower,title,capitalize} |
                      --replace-spaces [CHAR] | --list-history | --undo ID]
                      [--before-ext] [--start-num START_NUM]
                      [--padding PADDING] [--seq-position {prefix,suffix}]
                      [--date-format DATE_FORMAT] [--use-file-time]
                      [--date-position {prefix,suffix}]
                      [directory]

批量文件重命名工具

positional arguments:
  directory             要处理的目录路径，默认为当前目录

options:
  -h, --help            显示帮助信息并退出
  -r, --recursive       递归处理子目录
  --dry-run             模拟运行，不实际重命名文件

文件筛选选项:
  -e, --extensions EXTENSIONS [EXTENSIONS ...]
                        要处理的文件扩展名列表，如 '.jpg .png'
  --min-size MIN_SIZE   最小文件大小（字节）
  --max-size MAX_SIZE   最大文件大小（字节）
  --exclude EXCLUDE     排除的文件名模式（正则表达式）

重命名操作（仅选择一种）:
  --add-prefix PREFIX   添加前缀
  --add-suffix SUFFIX   添加后缀
  --before-ext          在扩展名前添加后缀，与--add-suffix一起使用
  --add-sequence        添加序列号
  --start-num START_NUM 序列号起始值
  --padding PADDING     序列号位数（补零）
  --seq-position {prefix,suffix}
                        序列号位置，前缀或后缀
  --add-date            添加日期时间
  --date-format DATE_FORMAT
                        日期时间格式
  --use-file-time       使用文件修改时间（否则使用当前时间）
  --date-position {prefix,suffix}
                        日期位置，前缀或后缀
  --replace PATTERN REPLACEMENT
                        替换文件名中的内容（使用正则表达式）
  --change-case {upper,lower,title,capitalize}
                        更改文件名大小写
  --replace-spaces [CHAR]
                        替换文件名中的空格（默认替换为下划线）
  --list-history        显示历史重命名记录
  --undo ID             撤销指定的重命名操作（使用--list-history查看可用ID）
``` 