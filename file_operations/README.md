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

## file_encrypt.py - 文件加密/解密工具

这个脚本提供了文件和目录的加密与解密功能，用于保护敏感数据和个人隐私文件。

### 功能特点

- **多种加密算法**:
  - AES (高级加密标准) - 对称加密算法，广泛用于数据保护
  - Fernet - Python cryptography库的高级加密方案，提供认证加密
- **文件安全措施**:
  - 基于密码的加密，使用PBKDF2派生密钥
  - 盐值随机生成，增强安全性
  - 文件完整性校验（SHA-256哈希）
  - 安全删除选项（多次覆盖原始文件内容）
- **批量处理**:
  - 支持单个文件和整个目录树的加密/解密
  - 递归处理子目录
  - 可选择性排除特定文件
- **友好的用户界面**:
  - 交互式密码输入（不显示密码）
  - 加密/解密进度反馈
  - 详细的错误报告

### 基本使用方法

加密单个文件：
```bash
python file_encrypt.py -e sensitive_document.docx
```

解密文件：
```bash
python file_encrypt.py -d sensitive_document.docx.encrypted
```

加密整个目录：
```bash
python file_encrypt.py -e important_folder
```

解密整个目录：
```bash
python file_encrypt.py -d important_folder_encrypted
```

生成随机强密码：
```bash
python file_encrypt.py -g
```

### 高级用法示例

使用AES算法加密：
```bash
python file_encrypt.py -e data.db -a aes
```

指定输出路径：
```bash
python file_encrypt.py -e photos.zip -o "D:\Backup\photos.zip.encrypted"
```

加密后删除原始文件：
```bash
python file_encrypt.py -e tax_documents.pdf --delete
```

排除某些文件：
```bash
python file_encrypt.py -e project_folder --exclude "*.log" "*.tmp" ".git*"
```

从文件读取密码（用于脚本自动化）：
```bash
python file_encrypt.py -e database.sql --password-file my_password.txt
```

不递归处理子目录：
```bash
python file_encrypt.py -e data_folder --no-recursive
```

### 完整命令行参数

```
usage: file_encrypt.py [-h] (-e | -d | -g) [-o OUTPUT] [-a {aes,fernet}]
                      [-p PASSWORD] [--password-file PASSWORD_FILE] [--delete]
                      [-r] [--no-recursive] [--exclude EXCLUDE [EXCLUDE ...]]
                      [--no-verify] [--length LENGTH] [-q] [-v]
                      [path]

文件加密/解密工具

positional arguments:
  path                  要处理的文件或目录路径

options:
  -h, --help            显示帮助信息并退出
  -e, --encrypt         加密文件或目录
  -d, --decrypt         解密文件或目录
  -g, --generate-password
                        生成随机密码
  -o, --output OUTPUT   输出文件或目录路径
  -a, --algorithm {aes,fernet}
                        加密算法 (默认: fernet)
  -p, --password PASSWORD
                        加密/解密密码 (不推荐在命令行中使用)
  --password-file PASSWORD_FILE
                        从文件读取密码
  --delete              处理后删除原始文件
  -r, --recursive       递归处理子目录（默认启用）
  --no-recursive        不递归处理子目录
  --exclude EXCLUDE [EXCLUDE ...]
                        排除的文件模式列表（如 *.log *.tmp）
  --no-verify           解密时不验证文件完整性
  --length LENGTH       生成的随机密码长度（默认: 16）
  -q, --quiet           静默模式，减少输出
  -v, --verbose         详细模式，显示更多信息
```

### 安全注意事项

- 请妥善保管您的密码，一旦丢失将无法恢复加密文件
- 建议定期备份重要数据
- 推荐使用交互式密码输入，避免在命令行中直接提供密码
- 使用`--delete`选项时请格外小心，原始文件将被安全删除且无法恢复

## file_sync.py - 文件同步工具

这个脚本提供了目录同步功能，可以在两个目录之间保持文件内容的一致性，适用于备份数据、工作文件同步和项目协作等场景。

### 功能特点

- **多种同步模式**:
  - 单向同步（从源目录到目标目录）
  - 双向同步（两个目录之间相互同步，保留最新的文件）
  - 镜像同步（目标目录完全匹配源目录，包括删除源中不存在的文件）
  - 更新模式（仅更新目标中已存在的文件）
- **智能文件对比**:
  - 基于修改时间的快速比较
  - 基于文件大小的预先筛选
  - 基于内容哈希值的精确比较
- **灵活的过滤选项**:
  - 可排除特定文件模式（如 *.tmp, *.log）
  - 可选择性包含隐藏文件
  - 支持符号链接处理
- **冲突解决策略**:
  - 基于修改时间（保留较新的文件）
  - 基于文件大小（保留较大的文件）
  - 固定策略（始终使用源文件或目标文件）
  - 可跳过冲突文件
- **详细的同步报告**:
  - 统计信息（复制、更新、删除、跳过的文件数）
  - 文件操作日志
  - 可导出为JSON格式

### 基本使用方法

单向同步（默认模式）：
```bash
python file_sync.py source_dir target_dir
```

双向同步：
```bash
python file_sync.py source_dir target_dir -m two-way
```

镜像同步：
```bash
python file_sync.py source_dir target_dir -m mirror
```

更新模式：
```bash
python file_sync.py source_dir target_dir -m update
```

### 高级用法示例

排除特定文件：
```bash
python file_sync.py source_dir target_dir -e "*.tmp" "*.log" ".git*"
```

模拟运行（不实际修改文件）：
```bash
python file_sync.py source_dir target_dir --dry-run
```

使用特定冲突解决策略：
```bash
python file_sync.py source_dir target_dir -m two-way -c larger
```

生成同步报告：
```bash
python file_sync.py source_dir target_dir -r sync_report.json
```

包含隐藏文件并跟随符号链接：
```bash
python file_sync.py source_dir target_dir --include-hidden --follow-symlinks
```

删除目标目录中源目录不存在的文件：
```bash
python file_sync.py source_dir target_dir --delete-orphaned
```

### 完整命令行参数

```
usage: file_sync.py [-h] [-m {one-way,two-way,mirror,update}]
                   [-c {newer,larger,source,target,skip,prompt}]
                   [-e EXCLUDE [EXCLUDE ...]] [--include-hidden]
                   [--delete-orphaned] [--no-metadata] [--follow-symlinks]
                   [--dry-run] [-r REPORT] [-q] [-v]
                   source target

文件同步工具 - 同步两个目录的内容

positional arguments:
  source                源目录路径
  target                目标目录路径

options:
  -h, --help            显示帮助信息并退出
  -m, --mode {one-way,two-way,mirror,update}
                        同步模式（默认: one-way）
  -c, --conflict {newer,larger,source,target,skip,prompt}
                        冲突解决策略（默认: newer）
  -e, --exclude EXCLUDE [EXCLUDE ...]
                        排除的文件模式列表（如 *.tmp *.log）
  --include-hidden      包括隐藏文件（以.开头）
  --delete-orphaned     删除目标中源不存在的文件
  --no-metadata         不保留文件元数据（修改时间等）
  --follow-symlinks     跟随符号链接
  --dry-run             仅模拟运行，不实际修改文件
  -r, --report REPORT   生成同步报告的文件路径
  -q, --quiet           静默模式，减少输出
  -v, --verbose         详细模式，显示更多信息
```

### 同步模式说明

- **单向同步 (one-way)**: 将源目录的文件复制到目标目录。只会添加或更新文件，不会删除目标目录中的任何文件。
- **双向同步 (two-way)**: 两个目录之间相互同步，保留最新的文件版本。适合两个工作环境之间的文件同步。
- **镜像同步 (mirror)**: 使目标目录成为源目录的精确副本，包括删除源目录中不存在的文件。适合备份场景。
- **更新模式 (update)**: 仅更新目标目录中已存在的文件，不会添加新文件或删除文件。适合更新已部署的应用程序。

### 冲突解决策略

当双向同步时，如果两个目录中的同一文件都有修改，会产生冲突。可以通过以下策略解决：

- **newer**: 保留修改时间较新的文件（默认）
- **larger**: 保留文件大小较大的文件
- **source**: 始终使用源目录中的文件
- **target**: 始终使用目标目录中的文件
- **skip**: 跳过冲突文件，不进行同步
- **prompt**: 提示用户选择（目前尚未实现，等同于skip）

## file_compress.py - 文件压缩/解压工具

这个脚本提供了文件和目录的压缩与解压功能，支持多种压缩格式，适用于文件备份、文件共享和存储空间优化。

### 功能特点

- **多种压缩格式支持**:
  - ZIP格式 - 最常用的跨平台压缩格式
  - TAR格式 - 无压缩的归档格式
  - TAR.GZ格式 - 使用GZIP算法压缩的TAR文件
  - TAR.BZ2格式 - 使用BZIP2算法压缩的TAR文件
- **丰富的压缩选项**:
  - 可调节的压缩级别（ZIP格式）
  - 排除特定文件模式
  - 选择性包含隐藏文件
  - 文件统计和压缩率报告
- **灵活的解压功能**:
  - 支持展平目录结构
  - 选择性解压特定文件
  - 自定义输出目录
- **压缩文件管理**:
  - 列出压缩文件内容
  - 显示详细的文件信息

### 基本使用方法

压缩文件或目录（默认ZIP格式）：
```bash
python file_compress.py -c my_documents
```

指定压缩格式：
```bash
python file_compress.py -c photos -f tar.gz
```

解压文件：
```bash
python file_compress.py -d archive.zip
```

解压到指定目录：
```bash
python file_compress.py -d archive.zip -o extracted_files
```

查看压缩文件内容：
```bash
python file_compress.py -l archive.zip
```

### 高级用法示例

使用较低压缩级别（更快但文件更大）：
```bash
python file_compress.py -c large_folder -f zip --level 1
```

排除特定文件：
```bash
python file_compress.py -c project_dir -e "*.log" "*.tmp" ".git*"
```

包含隐藏文件：
```bash
python file_compress.py -c config_files --include-hidden
```

解压时展平目录结构：
```bash
python file_compress.py -d nested_archive.zip --flatten
```

只解压特定文件：
```bash
python file_compress.py -d backup.tar.gz --files "docs/important.pdf" "images/"
```

详细查看压缩文件内容：
```bash
python file_compress.py -l archive.zip -v
```

### 完整命令行参数

```
usage: file_compress.py [-h] (-c | -d | -l) [-o OUTPUT] [-f {zip,tar,tar.gz,tar.bz2}]
                        [--level {0,1,2,3,4,5,6,7,8,9}] [-e EXCLUDE [EXCLUDE ...]]
                        [--include-hidden] [--flatten] [--files FILES [FILES ...]]
                        [-v] path

文件压缩/解压工具

positional arguments:
  path                  要处理的文件或目录路径

options:
  -h, --help            显示帮助信息并退出
  -c, --compress        压缩文件或目录
  -d, --decompress      解压文件
  -l, --list            列出压缩文件内容
  -o, --output OUTPUT   输出文件或目录路径
  -v, --verbose         详细模式，显示更多信息

压缩选项:
  -f, --format {zip,tar,tar.gz,tar.bz2}
                        压缩格式（默认: zip）
  --level {0,1,2,3,4,5,6,7,8,9}
                        压缩级别 0-9，9为最高压缩率（仅用于ZIP格式，默认: 9）
  -e, --exclude EXCLUDE [EXCLUDE ...]
                        要排除的文件模式列表（如 *.tmp *.log）
  --include-hidden      包括隐藏文件

解压选项:
  --flatten             展平目录结构（所有文件直接解压到输出目录）
  --files FILES [FILES ...]
                        只解压指定的文件或目录
```

### 压缩格式说明

- **ZIP (.zip)**: 最通用的压缩格式，支持大多数操作系统和程序。提供良好的压缩率和合理的速度。支持单个文件压缩和加密。
- **TAR (.tar)**: 仅归档不压缩，通常用于保留文件权限和特性。文件大小基本不变。
- **TAR.GZ (.tar.gz)**: 使用GZIP算法压缩的TAR文件，提供良好的压缩率和速度，在Linux系统中常用。
- **TAR.BZ2 (.tar.bz2)**: 使用BZIP2算法压缩的TAR文件，通常比GZIP提供更高的压缩率，但速度较慢。

### 注意事项

- 对大文件进行压缩或解压可能需要较长时间和较多内存
- ZIP格式在跨平台使用时最兼容
- 在解压前请确保有足够的磁盘空间
- 文件路径中包含中文或特殊字符可能在某些环境下导致问题

## file_dupes.py - 文件重复查找工具

这个脚本用于查找目录中的重复文件，支持多种比较方式和重复文件处理选项，可用于清理磁盘空间、整理备份和优化文件存储。

### 功能特点

- **多种文件比较方法**:
  - 基于文件大小的快速比较
  - 基于哈希值的精确比较（MD5、SHA1、SHA256算法）
  - 逐字节内容比较（最精确但速度最慢）
- **灵活的文件筛选**:
  - 指定最小文件大小
  - 排除特定文件模式
  - 选择性包含隐藏文件
- **丰富的重复处理选项**:
  - 生成详细报告（文本、CSV、JSON格式）
  - 删除重复文件（保留第一个）
  - 创建硬链接（节省磁盘空间但保持文件路径）
  - 创建符号链接
  - 移动重复文件到指定目录
  - 交互式处理（手动选择每组文件的处理方式）
- **高效实现**:
  - 多阶段比较算法（先按大小分组再比较内容）
  - 哈希值缓存（避免重复计算）
  - 详细的统计信息和进度报告

### 基本使用方法

查找当前目录中的重复文件：
```bash
python file_dupes.py .
```

扫描多个目录：
```bash
python file_dupes.py 文档 图片 下载
```

查找并删除重复文件：
```bash
python file_dupes.py . -p delete
```

查找并创建硬链接（节省空间）：
```bash
python file_dupes.py . -p hardlink
```

### 高级用法示例

使用SHA256算法进行精确比较：
```bash
python file_dupes.py . -m hash -a sha256
```

忽略小于1MB的文件：
```bash
python file_dupes.py . --min-size 1MB
```

排除特定类型文件：
```bash
python file_dupes.py . -e "*.tmp" "*.log" "*.bak"
```

将重复文件移动到备份目录：
```bash
python file_dupes.py . -p move -t ./duplicates
```

交互式处理重复文件：
```bash
python file_dupes.py . -p interactive
```

生成JSON格式报告：
```bash
python file_dupes.py . -f json -o duplicates_report.json
```

### 完整命令行参数

```
usage: file_dupes.py [-h] [-r] [--no-recursive] [-m {size,hash,content}]
                     [-a {md5,sha1,sha256}] [--min-size MIN_SIZE]
                     [-e EXCLUDE [EXCLUDE ...]] [--include-hidden]
                     [--follow-symlinks]
                     [-p {report,delete,hardlink,symlink,move,interactive}]
                     [-t TARGET_DIR] [-o OUTPUT] [-f {text,csv,json}] [-q] [-v]
                     directories [directories ...]

文件重复查找工具

positional arguments:
  directories           要扫描的目录路径列表

options:
  -h, --help            显示帮助信息并退出
  -r, --recursive       递归扫描子目录（默认启用）
  --no-recursive        不递归扫描子目录

比较选项:
  -m, --method {size,hash,content}
                        文件比较方法（默认: hash）
  -a, --algorithm {md5,sha1,sha256}
                        哈希算法（默认: md5）
  --min-size MIN_SIZE   最小文件大小，如 1KB、2MB（默认: 1B）

过滤选项:
  -e, --exclude EXCLUDE [EXCLUDE ...]
                        要排除的文件模式列表（如 *.tmp *.log）
  --include-hidden      包括隐藏文件
  --follow-symlinks     跟随符号链接

处理选项:
  -p, --process {report,delete,hardlink,symlink,move,interactive}
                        重复文件处理操作（默认: report）
  -t, --target-dir      移动重复文件的目标目录（用于move操作）

输出选项:
  -o, --output OUTPUT   报告输出文件路径
  -f, --format {text,csv,json}
                        报告格式（默认: text）
  -q, --quiet           静默模式，减少输出
  -v, --verbose         详细模式，显示更多信息
```

### 比较方法说明

- **size**: 仅比较文件大小。最快但可能产生误报（不同内容的文件可能大小相同）。
- **hash**: 使用哈希算法比较文件内容。平衡了速度和准确性，适合大多数场景。
- **content**: 逐字节比较文件内容。最准确但处理大文件时速度较慢。

### 处理操作说明

- **report**: 仅生成重复文件报告，不修改任何文件（默认）。
- **delete**: 删除所有重复文件，保留每组的第一个文件。
- **hardlink**: 将重复文件替换为到原始文件的硬链接，节省磁盘空间。
- **symlink**: 将重复文件替换为到原始文件的符号链接。
- **move**: 将重复文件移动到指定目录。
- **interactive**: 交互式处理，对每组重复文件手动选择操作。

### 注意事项

- 删除、硬链接和符号链接操作会修改文件系统，操作前请确保备份重要数据。
- 硬链接仅在同一文件系统上有效，不能跨驱动器使用。
- 大型目录的扫描可能需要较长时间和较多内存，特别是使用content比较方法时。
- 建议先使用默认的report模式查看重复文件，确认无误后再执行其他操作。

## file_monitor.py - 文件监控工具

这个脚本用于实时监控指定目录中的文件变化（创建、修改、删除、重命名等），并可以在文件发生变化时记录或执行指定操作。适用于自动备份、开发监控、日志跟踪等场景。

### 功能特点

- **实时监控文件变化**:
  - 监控文件创建、修改、删除和移动事件
  - 支持递归监控子目录
  - 可单独监控文件或目录变化
- **精细的过滤系统**:
  - 按文件名模式过滤（通配符支持）
  - 按文件大小范围过滤
  - 可选择性包含隐藏文件
  - 按事件类型过滤
- **多种响应操作**:
  - 日志记录（控制台、文件或JSON格式）
  - 自动备份变化的文件
  - 执行自定义命令
  - 发送桌面通知
- **高级功能**:
  - 批处理模式（收集一段时间内的事件后一次处理）
  - 冷却时间设置（防止频繁触发）
  - 详细的事件统计

### 使用场景

1. **开发辅助**:
   - 监控源代码变化并自动运行测试或构建
   - 监控配置文件变化并自动重启服务
   - 实时预览开发效果

2. **数据安全**:
   - 监控重要文件变化并自动备份
   - 记录敏感目录的访问和修改行为
   - 检测异常文件操作

3. **自动化工作流**:
   - 监控下载文件夹并自动分类处理新文件
   - 监控共享目录变化并执行后续处理
   - 图片或视频文件变化时自动转换格式

### 基本使用方法

监控单个目录：
```bash
python file_monitor.py 要监控的目录
```

监控多个目录：
```bash
python file_monitor.py 目录1 目录2 目录3
```

监控特定类型的文件：
```bash
python file_monitor.py --include "*.txt" "*.log" 要监控的目录
```

排除特定类型的文件：
```bash
python file_monitor.py --exclude "*.tmp" "*.bak" 要监控的目录
```

### 高级用法示例

仅监控文件创建和删除事件：
```bash
python file_monitor.py --event-types created deleted 要监控的目录
```

监控文件变化并自动备份：
```bash
python file_monitor.py -b --backup-dir "备份目录" 要监控的目录
```

监控并执行自定义命令：
```bash
python file_monitor.py -c "echo 文件 {filename} 已变化" 要监控的目录
```

将监控日志保存到文件：
```bash
python file_monitor.py -l file --log-file "监控日志.txt" 要监控的目录
```

启用批处理模式（减少频繁处理）：
```bash
python file_monitor.py --batch --batch-timeout 10 要监控的目录
```

监控大型文件的变化：
```bash
python file_monitor.py --min-size 10MB 要监控的目录
```

启用桌面通知：
```bash
python file_monitor.py -n 要监控的目录
```

设置监控超时时间：
```bash
python file_monitor.py -t 3600 要监控的目录  # 监控1小时后自动停止
```

### 完整命令行参数

```
usage: file_monitor.py [-h] [-r] [--no-recursive] [-t TIMEOUT] [-i INCLUDE [INCLUDE ...]]
                        [-e EXCLUDE [EXCLUDE ...]] [--include-hidden]
                        [--event-types {created,modified,deleted,moved,all} [{created,modified,deleted,moved,all} ...]]
                        [--file-types {file,directory,all} [{file,directory,all} ...]]
                        [--min-size MIN_SIZE] [--max-size MAX_SIZE] [--cooldown COOLDOWN]
                        [--batch] [--batch-timeout BATCH_TIMEOUT]
                        [-l {console,file}] [--log-file LOG_FILE] [--json-log JSON_LOG]
                        [-b] [--backup-dir BACKUP_DIR] [-c COMMAND] [-n]
                        [-q] [-v]
                        paths [paths ...]

文件监控工具

positional arguments:
  paths                 要监控的路径列表

options:
  -h, --help            显示帮助信息并退出
  -r, --recursive       递归监控子目录（默认启用）
  --no-recursive        不递归监控子目录
  -t, --timeout TIMEOUT 监控超时时间（秒），0表示一直运行（默认）

过滤选项:
  -i, --include INCLUDE [INCLUDE ...]
                        要包含的文件模式列表（如 *.txt *.log）
  -e, --exclude EXCLUDE [EXCLUDE ...]
                        要排除的文件模式列表（如 *.tmp *.bak）
  --include-hidden      包括隐藏文件
  --event-types {created,modified,deleted,moved,all} [{created,modified,deleted,moved,all} ...]
                        要监控的事件类型列表
  --file-types {file,directory,all} [{file,directory,all} ...]
                        要监控的文件类型列表
  --min-size MIN_SIZE   最小文件大小，如 1KB、2MB（默认: 0）
  --max-size MAX_SIZE   最大文件大小，如 10MB、1GB
  --cooldown COOLDOWN   相同文件两次事件间的最小冷却时间（秒）（默认: 1）

批处理选项:
  --batch               批处理模式，收集一段时间内的事件后一次处理
  --batch-timeout BATCH_TIMEOUT
                        批处理超时时间（秒）（默认: 5）

操作选项:
  -l, --log {console,file}
                        日志输出目标（默认: console）
  --log-file LOG_FILE   日志文件路径（当--log=file时使用）
  --json-log JSON_LOG   JSON格式日志文件路径
  -b, --backup          备份修改的文件
  --backup-dir BACKUP_DIR
                        备份目录路径（默认: file_monitor_backups）
  -c, --command COMMAND 文件变化时执行的命令，可使用{path}、{filename}等占位符
  -n, --notify          启用桌面通知

其他选项:
  -q, --quiet           静默模式，减少输出
  -v, --verbose         详细模式，显示更多信息
```

### 命令占位符

在使用 `-c/--command` 选项指定自定义命令时，可以使用以下占位符：

- `{path}`: 完整的文件路径
- `{filename}`: 仅文件名（不含路径）
- `{event_type}`: 事件类型（created、modified、deleted、moved）
- `{file_type}`: 文件类型（file或directory）
- `{dest_path}`: 目标路径（仅对moved事件有效）
- `{dest_filename}`: 目标文件名（仅对moved事件有效）

例如：
```bash
python file_monitor.py -c "echo 文件 {filename} 被 {event_type} 了" 要监控的目录
```

### 依赖项

此脚本依赖 `watchdog` 库来监控文件系统事件。如果尚未安装，请运行：
```bash
pip install watchdog
```

### 注意事项

- 对于高频变化的目录（如日志目录或临时文件目录），建议使用批处理模式减少处理次数
- 在Windows系统上，某些操作（如编辑并保存文件）可能会触发多个事件
- 桌面通知功能在不同操作系统上可能需要额外的依赖库
- 当使用备份功能时，请确保有足够的磁盘空间存储备份文件

## text_merger.py - 文本文件合并工具

这个脚本用于将多个文本文件合并成一个文件，支持各种合并方式、文件排序方法、分隔符选项和文本处理功能。适用于日志整合、文档汇编、数据收集等场景。

### 功能特点

- **灵活的文件排序**:
  - 按文件名排序
  - 按文件大小排序
  - 按修改时间排序
  - 自定义排序顺序
- **多种文件分隔方式**:
  - 空行分隔
  - 自定义分隔符
  - 文件名作为分隔标题
  - 带框的文件名标题
  - 标记行分隔（如横线）
- **强大的文本处理功能**:
  - 删除空行和重复行
  - 修剪行（删除首尾空白）
  - 添加行前缀和后缀
  - 根据正则表达式过滤内容
  - 限制行长度
  - 删除HTML标签
  - 转换制表符为空格
  - 添加行号
  - 行包装
- **完善的输入/输出控制**:
  - 支持不同的文件编码
  - 可添加自定义页眉和页脚
  - 输出到文件或标准输出
  - 自动生成文件来源信息

### 基本使用方法

合并多个文本文件：
```bash
python text_merger.py file1.txt file2.txt file3.txt -o merged.txt
```

合并并按大小排序：
```bash
python text_merger.py *.txt -o merged.txt -s size
```

合并并按修改时间逆序排序（最新的文件在前）：
```bash
python text_merger.py *.log -o merged.log -s modified -r
```

使用文件名作为分隔标题：
```bash
python text_merger.py *.md -o merged.md --separator filename
```

### 高级用法示例

删除重复行和空行：
```bash
python text_merger.py *.txt -o clean.txt --remove-duplicate-lines --remove-empty-lines
```

只包含匹配特定模式的行：
```bash
python text_merger.py error*.log -o errors_only.log --include "ERROR|CRITICAL" --ignore-case
```

添加行号并限制行长度：
```bash
python text_merger.py source.txt -o numbered.txt --number-lines --max-line-length 80
```

添加自定义页眉和页脚：
```bash
python text_merger.py *.txt -o report.txt --header "===== 合并报告 =====" --footer "===== 报告结束 ====="
```

使用自定义分隔符：
```bash
python text_merger.py *.txt -o merged.txt --separator custom --custom-separator "\n\n===== 下一个文件 =====\n\n"
```

将表格数据合并为CSV（删除空行，修剪空白）：
```bash
python text_merger.py table*.txt -o combined.csv --remove-empty-lines --trim-lines
```

### 完整命令行参数

```
usage: text_merger.py [-h] [-o OUTPUT] [-s {name,size,modified,custom}] [-r]
                      [--custom-order CUSTOM_ORDER [CUSTOM_ORDER ...]]
                      [--separator {none,newline,custom,filename,filename_box,marker_line}]
                      [--custom-separator CUSTOM_SEPARATOR]
                      [--file-encoding FILE_ENCODING]
                      [--output-encoding OUTPUT_ENCODING]
                      [--remove-empty-lines] [--remove-duplicate-lines]
                      [--trim-lines] [--line-prefix LINE_PREFIX]
                      [--line-suffix LINE_SUFFIX] [--include INCLUDE]
                      [--exclude EXCLUDE] [--ignore-case]
                      [--max-line-length MAX_LINE_LENGTH] [--remove-html]
                      [--convert-tabs] [--tab-size TAB_SIZE] [--number-lines]
                      [--wrap-lines WRAP_LINES] [--skip-errors]
                      [--header HEADER] [--header-file HEADER_FILE]
                      [--footer FOOTER] [--footer-file FOOTER_FILE]
                      [--no-warning] [-q] [-v]
                      files [files ...]

文本文件合并工具

positional arguments:
  files                 要合并的文件列表

options:
  -h, --help            显示帮助信息并退出
  -o, --output OUTPUT   输出文件路径（如果省略则输出到标准输出）

排序选项:
  -s, --sort {name,size,modified,custom}
                        文件排序方法（默认: name）
  -r, --reverse         逆序排序
  --custom-order CUSTOM_ORDER [CUSTOM_ORDER ...]
                        自定义文件排序顺序（仅当sort=custom时有效）

分隔符选项:
  --separator {none,newline,custom,filename,filename_box,marker_line}
                        文件分隔符类型（默认: newline）
  --custom-separator CUSTOM_SEPARATOR
                        自定义分隔符（当separator=custom时使用）

编码选项:
  --file-encoding FILE_ENCODING
                        输入文件编码（默认: utf-8）
  --output-encoding OUTPUT_ENCODING
                        输出文件编码（默认: utf-8）

处理选项:
  --remove-empty-lines  删除空行
  --remove-duplicate-lines
                        删除重复行
  --trim-lines          修剪行（删除首尾空白）
  --line-prefix LINE_PREFIX
                        添加到每行开头的前缀
  --line-suffix LINE_SUFFIX
                        添加到每行结尾的后缀
  --include INCLUDE     包含正则表达式模式（仅包含匹配的行）
  --exclude EXCLUDE     排除正则表达式模式（排除匹配的行）
  --ignore-case         正则表达式忽略大小写
  --max-line-length MAX_LINE_LENGTH
                        最大行长度（截断更长的行）
  --remove-html         删除HTML标签
  --convert-tabs        将制表符转换为空格
  --tab-size TAB_SIZE   制表符大小（默认: 4）
  --number-lines        添加行号
  --wrap-lines WRAP_LINES
                        行包装宽度（每行最大字符数）

其他选项:
  --skip-errors         跳过处理错误
  --header HEADER       添加到输出文件开头的文本
  --header-file HEADER_FILE
                        从文件读取要添加到输出文件开头的文本
  --footer FOOTER       添加到输出文件结尾的文本
  --footer-file FOOTER_FILE
                        从文件读取要添加到输出文件结尾的文本
  --no-warning          不添加生成文件的警告注释
  -q, --quiet           静默模式，减少输出
  -v, --verbose         详细模式，显示更多信息
```

### 分隔符类型说明

- **none**: 不添加分隔符，文件内容直接连接
- **newline**: 在文件之间添加一个空行（默认）
- **custom**: 使用自定义分隔符
- **filename**: 使用文件名作为分隔标题（例如：`# file.txt`）
- **filename_box**: 使用带框的文件名（例如：`+--------+`、`| file.txt |`、`+--------+`）
- **marker_line**: 使用横线作为分隔符（例如：`----------------`）

### 使用场景

1. **日志分析**：合并多个日志文件，按时间顺序排列，并筛选出包含特定关键词的行
   ```bash
   python text_merger.py log*.txt -o combined_logs.txt -s modified --include "error|warning" --ignore-case
   ```

2. **源代码合并**：合并多个源代码文件，添加文件名作为标题，去除注释行
   ```bash
   python text_merger.py *.py -o full_source.txt --separator filename --exclude "^\s*#"
   ```

3. **数据整理**：合并CSV数据文件，删除重复的标题行，修剪空白字符
   ```bash
   python text_merger.py data*.csv -o merged_data.csv --exclude "^id,name,value" --trim-lines
   ```

4. **文档汇编**：将多个Markdown文件合并为一个文档，添加适当的标题分隔
   ```bash
   python text_merger.py chapter*.md -o book.md --separator filename_box
   ```

### 注意事项

- 处理大型文件时可能会消耗较多内存
- 删除重复行功能在处理大量数据时可能会降低性能
- 某些编码转换可能导致字符丢失，请确保正确指定输入和输出编码
- 默认情况下，合并后的文件会包含生成信息头部，可以使用 `--no-warning` 禁用