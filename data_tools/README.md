# 数据处理工具 (data_processor.py)

这个工具可以处理CSV和Excel文件，提供数据分析、转换、清洗和可视化功能，帮助用户高效处理和分析表格数据。

## 主要功能

- **数据加载与解析** - 支持CSV、Excel和JSON格式
- **数据统计分析** - 计算基础统计量（均值、中位数、标准差等）
- **数据清洗** - 处理缺失值、删除重复项、保留特定列
- **数据筛选** - 按条件过滤数据
- **数据格式转换** - 在CSV、Excel和JSON格式之间转换
- **数据可视化** - 创建多种图表（柱状图、折线图、散点图等）
- **文本分析** - 分析文本列的模式和统计信息

## 依赖库

核心功能依赖：
- Python 3.6+
- 标准库: os, sys, json, csv, argparse, logging

扩展功能依赖：
- pandas - 数据处理和分析
- matplotlib - 数据可视化
- numpy - 数学计算支持
- openpyxl - Excel文件处理

> 注意：工具将根据可用的库自动调整功能。没有pandas时，只支持基本的CSV处理；没有matplotlib时，不支持可视化功能。

## 安装依赖

```bash
pip install pandas matplotlib numpy openpyxl
```

## 使用方法

### 基本用法

```bash
python data_processor.py 数据文件.csv [选项]
```

### 常用选项

| 选项 | 描述 |
|------|------|
| `-o, --output 文件路径` | 输出文件路径 |
| `-f, --format {csv,excel,json}` | 输出格式（默认:csv） |
| `--summary` | 显示数据摘要统计 |
| `--analyze-text 列名` | 分析指定的文本列 |
| `--fill-na 列名=值 [列名=值 ...]` | 填充缺失值 |
| `--drop-duplicates` | 删除重复行 |
| `--keep-columns 列名 [列名 ...]` | 指定要保留的列 |
| `--filter "列名 操作符 值" ["列名 操作符 值" ...]` | 筛选条件 |

### 数据可视化选项

| 选项 | 描述 |
|------|------|
| `--plot {bar,line,scatter,pie,histogram}` | 创建图表类型 |
| `--x-column 列名` | X轴列名 |
| `--y-column 列名` | Y轴列名 |
| `--title 标题` | 图表标题 |
| `--chart-output 文件路径` | 图表输出文件路径 |

## 示例用法

### 基础数据分析

```bash
# 显示CSV文件的摘要统计信息
python data_processor.py 数据.csv --summary
```

### 数据清洗与转换

```bash
# 删除重复行，填充空值，并转换为JSON格式
python data_processor.py 数据.csv --drop-duplicates --fill-na "年龄=0" "城市=未知" -o 清洗后数据.json -f json
```

### 数据筛选

```bash
# 筛选年龄大于30且来自北京的记录
python data_processor.py 客户数据.csv --filter "年龄 > 30" "城市 == 北京" -o 筛选结果.csv
```

### 列选择与保留

```bash
# 只保留姓名、年龄和电话列
python data_processor.py 完整数据.csv --keep-columns 姓名 年龄 电话 -o 简化数据.csv
```

### 数据可视化

```bash
# 创建年龄分布直方图
python data_processor.py 人口数据.csv --plot histogram --x-column 年龄 --title "年龄分布" --chart-output 年龄分布.png

# 创建城市人口柱状图
python data_processor.py 人口数据.csv --plot bar --x-column 城市 --y-column 人口数量 --title "各城市人口" --chart-output 城市人口.png
```

### 文本分析

```bash
# 分析产品描述列
python data_processor.py 产品数据.csv --analyze-text 产品描述
```

## 在代码中使用

```python
from data_processor import DataProcessor

# 初始化处理器
processor = DataProcessor('数据.csv')

# 获取数据摘要
summary = processor.get_summary()
print(f"数据行数: {summary['行数']}")

# 筛选数据
filtered_data = processor.filter_data([
    ('年龄', '>', 30),
    ('城市', '==', '上海')
])

# 数据清洗
cleaned_data = processor.clean_data(
    fill_na={'收入': 0, '学历': '未知'},
    drop_duplicates=True
)

# 保存为Excel
processor.convert_data('输出.xlsx', 'excel')

# 创建可视化
processor.visualize_data(
    chart_type='bar',
    x_column='部门',
    y_column='销售额',
    title='各部门销售情况',
    output_file='销售图表.png'
)
```

## 筛选操作符

支持的筛选操作符:
- `==` : 等于
- `!=` : 不等于
- `>` : 大于
- `<` : 小于
- `>=` : 大于等于
- `<=` : 小于等于
- `contains` : 包含子串
- `startswith` : 以...开头
- `endswith` : 以...结尾

## 注意事项

- 如果在Windows系统上使用带空格的文件名或值，请使用引号包围
- 使用--filter选项时，每个筛选条件需要用引号包围
- 对于大数据集，建议安装pandas以获得更好的性能 