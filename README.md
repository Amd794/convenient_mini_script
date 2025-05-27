# 便捷迷你脚本集合

这个仓库包含了一系列为个人日常使用而设计的便捷脚本，旨在提高工作效率和简化重复性任务。

## 简介

在日常工作和生活中，我们经常需要执行一些简单但重复的操作。这个脚本集合的目的是将这些常见操作自动化，节省时间并提高效率。

## 脚本分类

脚本按照功能分为以下几个类别：

- **文件操作**: 批量重命名、格式转换、文件整理等
- **系统工具**: 系统监控、自动备份、清理缓存等
- **开发辅助**: 代码格式化、依赖管理、环境配置等
- **网络工具**: 下载辅助、API测试、网络监测等
- **数据处理**: 数据转换、提取、分析等

## 可用脚本

### 文件操作

- **[organize_files.py](file_operations/organize_files.py)**: 自动整理文件夹，按文件类型分类文件到不同子文件夹中，并生成整理报告。[详情](file_operations/README.md)
- **[batch_rename.py](file_operations/batch_rename.py)**: 批量重命名文件，支持多种重命名模式、文件筛选和预览功能，还能保存历史操作并提供撤销功能。[详情](file_operations/README.md)
- **[file_finder.py](file_operations/file_finder.py)**: 强大的文件搜索工具，支持按文件名、内容、大小、日期等条件搜索文件，并提供多种结果排序和输出格式选项。[详情](file_operations/README.md)
- **[file_compare.py](file_operations/file_compare.py)**: 文件和目录比较工具，能够识别和显示文件之间的差异，以及比较目录结构和内容，支持多种输出格式。[详情](file_operations/README.md)
- **[file_encrypt.py](file_operations/file_encrypt.py)**: 文件加密/解密工具，支持多种加密算法，提供对单个文件和整个目录的加密保护，带有文件完整性校验和安全删除功能。[详情](file_operations/README.md)
- **[file_sync.py](file_operations/file_sync.py)**: 文件同步工具，支持多种同步模式（单向、双向、镜像等），可在两个目录之间保持文件内容的一致性，具有智能冲突解决和详细报告功能。[详情](file_operations/README.md)
- **[file_compress.py](file_operations/file_compress.py)**: 文件压缩/解压工具，支持多种压缩格式（ZIP、TAR、TAR.GZ、TAR.BZ2），提供灵活的压缩选项和解压功能，适用于文件备份、共享和存储空间优化。[详情](file_operations/README.md)

### 系统工具

- **[system_monitor.py](system_tools/system_monitor.py)**: 实时监控系统资源使用情况，显示CPU、内存、磁盘和网络使用情况，支持数据导出。[详情](system_tools/README.md)

### 网络工具

- **[network_speed_test.py](network_tools/network_speed_test.py)**: 测试网络连接性能，包括下载速度、上传速度、延迟和丢包率，支持历史数据记录和可视化。[详情](network_tools/README.md)

### 开发辅助

- **[code_analyzer.py](dev_tools/code_analyzer.py)**: 分析代码库结构、统计代码量、评估复杂度等，支持多种编程语言，可生成可视化报告。[详情](dev_tools/README.md)

### 数据处理

- **[data_processor.py](data_tools/data_processor.py)**: 提供CSV和Excel文件的数据分析、清洗、转换和可视化功能，支持数据过滤、统计分析和图表生成。[详情](data_tools/README.md)

## 贡献

这是一个个人使用的脚本集合，但欢迎分享您的想法和改进建议。

## 许可

本项目中的脚本仅供个人学习和使用。

## 注意事项

- 使用脚本前请确保理解其功能和可能的影响
- 对重要数据进行操作前，建议先备份
- 某些脚本可能需要特定的环境依赖，请查看各脚本的说明