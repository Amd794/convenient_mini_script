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

## file_finder.py - 文件搜索工具

这个脚本提供了强大的文件搜索功能，支持按多种条件查找文件，并可以对结果进行排序和格式化输出。

### 功能特点

- **多条件搜索**:
  - 按文件名搜索（支持通配符和正则表达式）
  - 按文件扩展名搜索
  - 按文件大小范围搜索
  - 按文件日期范围搜索（修改日期、创建日期、访问日期）
  - 按文件内容搜索（支持文本模式和正则表达式）
- **高级过滤**:
  - 包含/排除隐藏文件
  - 仅文件或仅目录过滤
  - 结果数量限制
- **结果处理**:
  - 多种排序方式（名称、大小、日期、扩展名、路径）
  - 多种输出格式（列表、表格、CSV）
  - 内容匹配行显示（带上下文）
  - 结果保存到文件

### 基本使用方法

按文件名搜索（支持通配符）：
```bash
python file_finder.py -n "*.txt"
```

按文件扩展名搜索：
```bash
python file_finder.py -e jpg png gif
```

按文件内容搜索：
```bash
python file_finder.py -c "搜索文本"
```

按文件大小搜索：
```bash
python file_finder.py --min-size 1MB --max-size 10MB
```

按修改日期搜索：
```bash
python file_finder.py --min-date "2023-01-01" --max-date "2023-12-31"
```

### 高级用法示例

使用正则表达式搜索文件名：
```bash
python file_finder.py -n ".*[0-9]{4}.*\.jpg" --regex
```

搜索特定内容并显示上下文行：
```bash
python file_finder.py -c "import os" --context-lines 2
```

搜索大文件并按大小排序：
```bash
python file_finder.py --min-size 100MB --sort-by size --reverse
```

搜索最近修改的文件：
```bash
python file_finder.py --min-date "2023-12-01" --sort-by modified --reverse
```

以表格格式显示详细结果：
```bash
python file_finder.py -n "*.py" --format table -d
```

保存搜索结果到CSV文件：
```bash
python file_finder.py -n "*.doc*" -o results.csv --format csv -d
```

### 完整命令行参数

```
usage: file_finder.py [-h] [-r] [--no-recursive] [-n NAME] [--regex] [-i]
                     [-e EXTENSION [EXTENSION ...]] [--min-size MIN_SIZE]
                     [--max-size MAX_SIZE] [--min-date MIN_DATE]
                     [--max-date MAX_DATE]
                     [--time-type {modified,created,accessed}]
                     [-c CONTENT] [--max-content-size MAX_CONTENT_SIZE]
                     [--include-binary] [--context-lines CONTEXT_LINES]
                     [--include-hidden] [--only-files] [--only-dirs]
                     [--limit LIMIT]
                     [--sort-by {name,size,modified,created,extension,path}]
                     [--reverse] [--format {list,table,csv}] [-d]
                     [--show-matches] [-o OUTPUT]
                     [search_path]

文件搜索工具 - 按各种条件搜索文件

positional arguments:
  search_path           搜索起始路径，默认为当前目录

options:
  -h, --help            显示帮助信息并退出
  -r, --recursive       递归搜索子目录（默认启用）
  --no-recursive        不递归搜索子目录

搜索条件（至少指定一个）:
  -n, --name NAME       按文件名搜索，支持通配符（如 *.txt）
  --regex               将名称或内容参数解释为正则表达式
  -i, --ignore-case     忽略大小写
  -e, --extension EXTENSION [EXTENSION ...]
                        按文件扩展名搜索（如 txt py）
  --min-size MIN_SIZE   最小文件大小（如 1KB、2MB）
  --max-size MAX_SIZE   最大文件大小（如 5MB、1GB）
  --min-date MIN_DATE   最早日期（YYYY-MM-DD 或 YYYY-MM-DD HH:MM:SS）
  --max-date MAX_DATE   最晚日期（YYYY-MM-DD 或 YYYY-MM-DD HH:MM:SS）
  --time-type {modified,created,accessed}
                        时间类型（默认: modified）
  -c, --content CONTENT
                        按文件内容搜索
  --max-content-size MAX_CONTENT_SIZE
                        内容搜索的最大文件大小（默认: 10MB）
  --include-binary      包含二进制文件在内容搜索中
  --context-lines CONTEXT_LINES
                        显示匹配行周围的上下文行数

结果过滤:
  --include-hidden      包含隐藏文件
  --only-files          只包含文件，不包含目录
  --only-dirs           只包含目录，不包含文件
  --limit LIMIT         限制结果数量（0表示不限制）

结果排序:
  --sort-by {name,size,modified,created,extension,path}
                        排序关键字（默认: name）
  --reverse             倒序排列

输出选项:
  --format {list,table,csv}
                        输出格式（默认: list）
  -d, --details         显示详细信息
  --show-matches        显示内容匹配行
  -o, --output OUTPUT   将结果保存到文件
``` 

## file_compare.py - 文件比较工具

这个脚本提供了强大的文件和目录比较功能，可以识别并显示文件之间的差异，以及比较目录结构和内容。

### 功能特点

- **文件比较**:
  - 支持文本文件行级比较
  - 支持二进制文件比较
  - 可选择忽略空白字符、大小写和空行
  - 显示上下文差异
  - 针对大文件优化的比较方法
- **目录比较**:
  - 识别仅存在于一侧的文件和目录
  - 比较两侧都存在的文件内容
  - 递归比较子目录
  - 支持忽略特定文件或目录
- **差异报告**:
  - 文本格式报告（控制台友好）
  - HTML格式报告（带颜色高亮）
  - JSON格式报告（便于程序处理）
  - 可保存报告到文件

### 基本使用方法

比较两个文件：
```bash
python file_compare.py file1.txt file2.txt
```

比较两个目录：
```bash
python file_compare.py dir1 dir2
```

生成HTML格式报告：
```bash
python file_compare.py file1.py file2.py --format html -o report.html
```

忽略空白字符和大小写：
```bash
python file_compare.py file1.txt file2.txt -w -i
```

### 高级用法示例

比较目录时忽略某些文件：
```bash
python file_compare.py project1 project2 --ignore "*.pyc" "*.log" "__pycache__"
```

只显示摘要信息：
```bash
python file_compare.py dir1 dir2 -q
```

显示更多上下文行：
```bash
python file_compare.py file1.py file2.py --context-lines 5
```

不递归比较子目录：
```bash
python file_compare.py dir1 dir2 --no-recursive
```

生成JSON格式报告：
```bash
python file_compare.py dir1 dir2 --format json -o diff.json
```

### 完整命令行参数

```
usage: file_compare.py [-h] [-r] [--no-recursive] [-i] [-w] [-B]
                      [-c CONTEXT_LINES] [--binary]
                      [--ignore IGNORE [IGNORE ...]]
                      [--format {text,html,json}] [-o OUTPUT] [-q] [-v]
                      path1 path2

文件和目录比较工具

positional arguments:
  path1                 第一个文件或目录路径
  path2                 第二个文件或目录路径

比较选项:
  -r, --recursive       递归比较子目录（默认启用）
  --no-recursive        不递归比较子目录
  -i, --ignore-case     忽略大小写差异
  -w, --ignore-whitespace
                        忽略空白字符差异
  -B, --ignore-blank-lines
                        忽略空行
  -c, --context-lines CONTEXT_LINES
                        显示差异上下文的行数（默认: 3）
  --binary              以二进制模式比较文件

过滤选项:
  --ignore IGNORE [IGNORE ...]
                        忽略的文件或目录模式列表（如 *.pyc __pycache__）

输出选项:
  --format {text,html,json}
                        输出格式（默认: text）
  -o, --output OUTPUT   输出报告的文件路径
  -q, --quiet           静默模式，仅显示摘要信息
  -v, --verbose         详细模式，显示更多信息
```