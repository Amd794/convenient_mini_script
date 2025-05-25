#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
数据处理工具

这个脚本可以处理CSV和Excel文件，提供数据分析、转换、清洗和可视化功能，
支持多种数据操作和转换格式，帮助用户高效处理表格数据。
"""

import argparse
import csv
import json
import logging
import os
import sys
from collections import Counter

# 尝试导入可选依赖
try:
    import pandas as pd

    HAS_PANDAS = True
except ImportError:
    HAS_PANDAS = False

try:
    import matplotlib.pyplot as plt
    import numpy as np

    HAS_MATPLOTLIB = True
except ImportError:
    HAS_MATPLOTLIB = False

try:
    import openpyxl

    HAS_OPENPYXL = True
except ImportError:
    HAS_OPENPYXL = False

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)


class DataProcessor:
    """数据处理类，提供对CSV和Excel文件的处理功能"""

    def __init__(self, input_file=None):
        """
        初始化数据处理器
        
        Args:
            input_file (str): 输入文件路径（CSV或Excel）
        """
        self.input_file = input_file
        self.data = None
        self.headers = []
        self.stats = {}

        # 检查必要的依赖
        if not HAS_PANDAS:
            logging.warning("缺少pandas库，部分功能可能受限。请安装pandas: pip install pandas")

        # 如果提供了输入文件，则加载数据
        if input_file:
            self.load_data(input_file)

    def load_data(self, file_path):
        """
        加载数据文件（CSV或Excel）
        
        Args:
            file_path (str): 文件路径
            
        Returns:
            bool: 是否成功加载
        """
        if not os.path.exists(file_path):
            logging.error(f"文件不存在: {file_path}")
            return False

        self.input_file = file_path
        file_ext = os.path.splitext(file_path)[1].lower()

        try:
            if HAS_PANDAS:
                if file_ext in ['.csv', '.txt']:
                    self.data = pd.read_csv(file_path)
                elif file_ext in ['.xlsx', '.xls']:
                    if not HAS_OPENPYXL and file_ext == '.xlsx':
                        logging.warning("处理.xlsx文件需要安装openpyxl: pip install openpyxl")
                        return False
                    self.data = pd.read_excel(file_path)
                elif file_ext == '.json':
                    self.data = pd.read_json(file_path)
                else:
                    logging.error(f"不支持的文件类型: {file_ext}")
                    return False

                self.headers = list(self.data.columns)
                logging.info(f"成功加载数据: {len(self.data)} 行, {len(self.headers)} 列")
                return True
            else:
                # 如果没有pandas，使用内置模块处理（仅支持CSV）
                if file_ext != '.csv':
                    logging.error(f"没有pandas库，只能处理CSV文件")
                    return False

                self.data = []
                with open(file_path, 'r', newline='', encoding='utf-8') as f:
                    reader = csv.DictReader(f)
                    self.headers = reader.fieldnames
                    for row in reader:
                        self.data.append(row)

                logging.info(f"成功加载CSV数据: {len(self.data)} 行, {len(self.headers)} 列")
                return True

        except Exception as e:
            logging.error(f"加载文件失败: {str(e)}")
            return False

    def get_summary(self):
        """
        获取数据摘要统计信息
        
        Returns:
            dict: 包含数据摘要的字典
        """
        if self.data is None:
            logging.error("没有加载数据")
            return {}

        summary = {
            "行数": 0,
            "列数": 0,
            "列名": [],
            "数据类型": {},
            "缺失值": {},
            "唯一值数量": {},
            "数值统计": {}
        }

        if HAS_PANDAS and isinstance(self.data, pd.DataFrame):
            df = self.data
            summary["行数"] = len(df)
            summary["列数"] = len(df.columns)
            summary["列名"] = list(df.columns)

            # 数据类型
            summary["数据类型"] = {col: str(dtype) for col, dtype in df.dtypes.items()}

            # 缺失值统计
            summary["缺失值"] = {col: int(df[col].isna().sum()) for col in df.columns}

            # 唯一值数量
            summary["唯一值数量"] = {col: int(df[col].nunique()) for col in df.columns}

            # 数值型列的统计
            for col in df.select_dtypes(include=['number']).columns:
                summary["数值统计"][col] = {
                    "最小值": float(df[col].min()),
                    "最大值": float(df[col].max()),
                    "平均值": float(df[col].mean()),
                    "中位数": float(df[col].median()),
                    "标准差": float(df[col].std())
                }
        else:
            # 使用基本Python处理CSV数据
            summary["行数"] = len(self.data)
            summary["列数"] = len(self.headers)
            summary["列名"] = self.headers

            # 尝试检测数据类型并计算统计信息
            for col in self.headers:
                # 数据类型检测
                col_types = set()
                non_null_values = []
                null_count = 0

                for row in self.data:
                    val = row.get(col, "")
                    if val == "":
                        null_count += 1
                    else:
                        col_types.add(type(val).__name__)
                        try:
                            num_val = float(val)
                            non_null_values.append(num_val)
                        except (ValueError, TypeError):
                            pass

                if len(col_types) == 1:
                    summary["数据类型"][col] = list(col_types)[0]
                else:
                    summary["数据类型"][col] = "mixed"

                summary["缺失值"][col] = null_count

                # 唯一值
                unique_values = set(row.get(col, "") for row in self.data)
                summary["唯一值数量"][col] = len(unique_values)

                # 数值统计
                if non_null_values:
                    summary["数值统计"][col] = {
                        "最小值": min(non_null_values),
                        "最大值": max(non_null_values),
                        "平均值": sum(non_null_values) / len(non_null_values)
                    }

                    # 计算中位数
                    sorted_values = sorted(non_null_values)
                    n = len(sorted_values)
                    if n % 2 == 1:
                        median = sorted_values[n // 2]
                    else:
                        median = (sorted_values[n // 2 - 1] + sorted_values[n // 2]) / 2
                    summary["数值统计"][col]["中位数"] = median

        self.stats = summary
        return summary

    def filter_data(self, conditions):
        """
        根据条件筛选数据
        
        Args:
            conditions (list): 条件列表，每个条件是一个元组 (列名, 操作符, 值)
                              操作符可以是: ==, !=, >, <, >=, <=, contains, startswith, endswith
        
        Returns:
            DataFrame/list: 筛选后的数据
        """
        if self.data is None:
            logging.error("没有加载数据")
            return None

        if HAS_PANDAS and isinstance(self.data, pd.DataFrame):
            df = self.data.copy()

            for col, op, val in conditions:
                if col not in df.columns:
                    logging.error(f"列不存在: {col}")
                    continue

                if op == "==":
                    df = df[df[col] == val]
                elif op == "!=":
                    df = df[df[col] != val]
                elif op == ">":
                    df = df[df[col] > val]
                elif op == "<":
                    df = df[df[col] < val]
                elif op == ">=":
                    df = df[df[col] >= val]
                elif op == "<=":
                    df = df[df[col] <= val]
                elif op == "contains":
                    df = df[df[col].astype(str).str.contains(str(val), na=False)]
                elif op == "startswith":
                    df = df[df[col].astype(str).str.startswith(str(val), na=False)]
                elif op == "endswith":
                    df = df[df[col].astype(str).str.endswith(str(val), na=False)]
                else:
                    logging.error(f"不支持的操作符: {op}")

            return df
        else:
            # 基本Python过滤
            filtered_data = []

            for row in self.data:
                include_row = True

                for col, op, val in conditions:
                    if col not in self.headers:
                        logging.error(f"列不存在: {col}")
                        continue

                    row_val = row.get(col, "")

                    # 尝试转换为数值类型进行比较
                    try:
                        if isinstance(val, (int, float)) and row_val:
                            row_val = float(row_val)
                    except (ValueError, TypeError):
                        pass

                    if op == "==":
                        if row_val != val:
                            include_row = False
                            break
                    elif op == "!=":
                        if row_val == val:
                            include_row = False
                            break
                    elif op == ">":
                        if not (isinstance(row_val, (int, float)) and row_val > val):
                            include_row = False
                            break
                    elif op == "<":
                        if not (isinstance(row_val, (int, float)) and row_val < val):
                            include_row = False
                            break
                    elif op == ">=":
                        if not (isinstance(row_val, (int, float)) and row_val >= val):
                            include_row = False
                            break
                    elif op == "<=":
                        if not (isinstance(row_val, (int, float)) and row_val <= val):
                            include_row = False
                            break
                    elif op == "contains":
                        if not (isinstance(row_val, str) and str(val) in row_val):
                            include_row = False
                            break
                    elif op == "startswith":
                        if not (isinstance(row_val, str) and row_val.startswith(str(val))):
                            include_row = False
                            break
                    elif op == "endswith":
                        if not (isinstance(row_val, str) and row_val.endswith(str(val))):
                            include_row = False
                            break
                    else:
                        logging.error(f"不支持的操作符: {op}")

                if include_row:
                    filtered_data.append(row)

            return filtered_data

    def clean_data(self, fill_na=None, drop_duplicates=False, columns_to_keep=None):
        """
        清洗数据（处理缺失值、重复值等）
        
        Args:
            fill_na (dict): 用于填充缺失值的字典 {列名: 填充值}
            drop_duplicates (bool): 是否删除重复行
            columns_to_keep (list): 要保留的列名列表
        
        Returns:
            DataFrame/list: 清洗后的数据
        """
        if self.data is None:
            logging.error("没有加载数据")
            return None

        if HAS_PANDAS and isinstance(self.data, pd.DataFrame):
            df = self.data.copy()

            # 选择列
            if columns_to_keep:
                valid_columns = [col for col in columns_to_keep if col in df.columns]
                if valid_columns:
                    df = df[valid_columns]
                else:
                    logging.warning("指定的列不存在")

            # 填充缺失值
            if fill_na:
                for col, val in fill_na.items():
                    if col in df.columns:
                        df[col] = df[col].fillna(val)

            # 删除重复行
            if drop_duplicates:
                orig_len = len(df)
                df = df.drop_duplicates()
                logging.info(f"删除了 {orig_len - len(df)} 行重复数据")

            return df
        else:
            # 基本Python数据清洗
            cleaned_data = []
            seen_rows = set()  # 用于检测重复行

            for row in self.data:
                # 创建新的行，仅保留指定的列
                if columns_to_keep:
                    new_row = {col: row.get(col, "") for col in columns_to_keep if col in self.headers}
                else:
                    new_row = row.copy()

                # 填充缺失值
                if fill_na:
                    for col, val in fill_na.items():
                        if col in new_row and (new_row[col] == "" or new_row[col] is None):
                            new_row[col] = val

                # 处理重复行
                if drop_duplicates:
                    # 创建行的哈希表示用于检查重复
                    row_key = tuple((k, v) for k, v in sorted(new_row.items()))
                    if row_key in seen_rows:
                        continue
                    seen_rows.add(row_key)

                cleaned_data.append(new_row)

            if drop_duplicates:
                logging.info(f"删除了 {len(self.data) - len(cleaned_data)} 行重复数据")

            return cleaned_data

    def convert_data(self, output_file, output_format):
        """
        转换数据为指定格式并保存
        
        Args:
            output_file (str): 输出文件路径
            output_format (str): 输出格式，可选值: csv, excel, json
            
        Returns:
            bool: 是否成功转换并保存
        """
        if self.data is None:
            logging.error("没有加载数据")
            return False

        # 确保输出目录存在
        output_dir = os.path.dirname(output_file)
        if output_dir and not os.path.exists(output_dir):
            try:
                os.makedirs(output_dir)
            except Exception as e:
                logging.error(f"创建输出目录失败: {str(e)}")
                return False

        try:
            if HAS_PANDAS and isinstance(self.data, pd.DataFrame):
                df = self.data

                if output_format == 'csv':
                    df.to_csv(output_file, index=False, encoding='utf-8')
                elif output_format == 'excel':
                    if not HAS_OPENPYXL:
                        logging.error("导出Excel格式需要安装openpyxl: pip install openpyxl")
                        return False
                    df.to_excel(output_file, index=False)
                elif output_format == 'json':
                    df.to_json(output_file, orient='records', force_ascii=False, indent=4)
                else:
                    logging.error(f"不支持的输出格式: {output_format}")
                    return False

                logging.info(f"数据已保存至: {output_file}")
                return True
            else:
                # 基本Python导出
                if output_format == 'csv':
                    with open(output_file, 'w', newline='', encoding='utf-8') as f:
                        writer = csv.DictWriter(f, fieldnames=self.headers)
                        writer.writeheader()
                        writer.writerows(self.data)
                elif output_format == 'json':
                    with open(output_file, 'w', encoding='utf-8') as f:
                        json.dump(self.data, f, ensure_ascii=False, indent=4)
                elif output_format == 'excel':
                    logging.error("没有pandas和openpyxl库，无法导出Excel格式")
                    return False
                else:
                    logging.error(f"不支持的输出格式: {output_format}")
                    return False

                logging.info(f"数据已保存至: {output_file}")
                return True

        except Exception as e:
            logging.error(f"保存文件失败: {str(e)}")
            return False

    def visualize_data(self, chart_type, x_column=None, y_column=None, output_file=None, title=None):
        """
        可视化数据
        
        Args:
            chart_type (str): 图表类型，可选值: bar, line, scatter, pie, histogram
            x_column (str): X轴列名
            y_column (str): Y轴列名
            output_file (str): 输出文件路径，None表示显示图表而不保存
            title (str): 图表标题
            
        Returns:
            bool: 是否成功创建可视化
        """
        if not HAS_MATPLOTLIB:
            logging.error("可视化图表需要安装matplotlib: pip install matplotlib")
            return False

        if self.data is None:
            logging.error("没有加载数据")
            return False

        try:
            plt.figure(figsize=(10, 6))

            if HAS_PANDAS and isinstance(self.data, pd.DataFrame):
                df = self.data

                if chart_type == 'bar':
                    if not x_column or not y_column:
                        logging.error("条形图需要指定x_column和y_column")
                        return False
                    df.plot(kind='bar', x=x_column, y=y_column, ax=plt.gca())

                elif chart_type == 'line':
                    if not x_column or not y_column:
                        logging.error("线图需要指定x_column和y_column")
                        return False
                    df.plot(kind='line', x=x_column, y=y_column, ax=plt.gca())

                elif chart_type == 'scatter':
                    if not x_column or not y_column:
                        logging.error("散点图需要指定x_column和y_column")
                        return False
                    df.plot(kind='scatter', x=x_column, y=y_column, ax=plt.gca())

                elif chart_type == 'pie':
                    if not y_column:
                        logging.error("饼图需要指定y_column")
                        return False

                    # 如果提供了x_column，使用它作为标签
                    if x_column:
                        pie_data = df.groupby(x_column)[y_column].sum()
                        pie_data.plot(kind='pie', ax=plt.gca())
                    else:
                        # 直接使用y_column的值
                        df[y_column].plot(kind='pie', ax=plt.gca())

                elif chart_type == 'histogram':
                    if not x_column:
                        logging.error("直方图需要指定x_column")
                        return False
                    df[x_column].plot(kind='hist', bins=20, ax=plt.gca())

                else:
                    logging.error(f"不支持的图表类型: {chart_type}")
                    return False
            else:
                # 基本Python数据可视化（有限功能）
                if not x_column or not y_column:
                    logging.error("需要指定x_column和y_column")
                    return False

                # 提取数据
                x_values = []
                y_values = []

                for row in self.data:
                    x_val = row.get(x_column)
                    y_val = row.get(y_column)

                    try:
                        x_val = float(x_val) if x_val else 0
                        y_val = float(y_val) if y_val else 0
                        x_values.append(x_val)
                        y_values.append(y_val)
                    except (ValueError, TypeError):
                        continue

                if chart_type == 'bar':
                    plt.bar(x_values, y_values)
                elif chart_type == 'line':
                    plt.plot(x_values, y_values)
                elif chart_type == 'scatter':
                    plt.scatter(x_values, y_values)
                elif chart_type == 'histogram':
                    plt.hist(x_values, bins=20)
                else:
                    logging.error(f"不支持的图表类型或需要pandas库: {chart_type}")
                    return False

            # 设置标题和标签
            if title:
                plt.title(title)
            if x_column:
                plt.xlabel(x_column)
            if y_column and chart_type != 'pie' and chart_type != 'histogram':
                plt.ylabel(y_column)

            # 调整布局
            plt.tight_layout()

            # 保存或显示图表
            if output_file:
                plt.savefig(output_file)
                logging.info(f"图表已保存至: {output_file}")
            else:
                plt.show()

            return True

        except Exception as e:
            logging.error(f"创建可视化图表失败: {str(e)}")
            return False

    def analyze_text_column(self, column):
        """
        分析文本列的内容
        
        Args:
            column (str): 列名
            
        Returns:
            dict: 分析结果
        """
        if self.data is None:
            logging.error("没有加载数据")
            return {}

        if column not in self.headers:
            logging.error(f"列不存在: {column}")
            return {}

        result = {
            "唯一值数量": 0,
            "最常见值": [],
            "平均长度": 0,
            "最短值长度": 0,
            "最长值长度": 0
        }

        if HAS_PANDAS and isinstance(self.data, pd.DataFrame):
            df = self.data

            # 确保处理的是字符串列
            series = df[column].astype(str).replace('nan', '')

            # 唯一值计数
            result["唯一值数量"] = series.nunique()

            # 最常见值
            value_counts = series.value_counts().head(5).to_dict()
            result["最常见值"] = [{"值": val, "次数": count} for val, count in value_counts.items()]

            # 字符串长度统计
            lengths = series.str.len()
            result["平均长度"] = lengths.mean()
            result["最短值长度"] = lengths.min()
            result["最长值长度"] = lengths.max()
        else:
            # 基本Python分析
            values = [str(row.get(column, "")) for row in self.data]
            values = [v for v in values if v]  # 排除空值

            if not values:
                return result

            # 唯一值计数
            unique_values = set(values)
            result["唯一值数量"] = len(unique_values)

            # 字符串长度统计
            lengths = [len(v) for v in values]
            result["平均长度"] = sum(lengths) / len(lengths)
            result["最短值长度"] = min(lengths)
            result["最长值长度"] = max(lengths)

            # 最常见值
            counter = Counter(values)
            most_common = counter.most_common(5)
            result["最常见值"] = [{"值": val, "次数": count} for val, count in most_common]

        return result


def parse_command(cmd_str):
    """
    解析命令行中的筛选条件
    
    Args:
        cmd_str (str): 命令字符串，格式为: "列名 操作符 值"
        
    Returns:
        tuple: (列名, 操作符, 值)
    """
    parts = cmd_str.strip().split(' ', 2)
    if len(parts) != 3:
        raise ValueError(f"无效的条件格式: {cmd_str}, 应为 '列名 操作符 值'")

    col, op, val = parts

    # 处理值的类型
    if val.lower() == 'true':
        val = True
    elif val.lower() == 'false':
        val = False
    else:
        try:
            if '.' in val:
                val = float(val)
            else:
                val = int(val)
        except ValueError:
            # 保持为字符串
            pass

    return col, op, val


def main():
    """主函数"""
    parser = argparse.ArgumentParser(description="数据处理工具 - 处理CSV和Excel文件")

    # 输入输出参数
    parser.add_argument("input_file", help="输入文件路径 (CSV 或 Excel)")
    parser.add_argument("-o", "--output", help="输出文件路径")
    parser.add_argument("-f", "--format", choices=["csv", "excel", "json"],
                        default="csv", help="输出文件格式(默认: csv)")

    # 数据分析参数
    parser.add_argument("--summary", action="store_true", help="显示数据摘要统计")
    parser.add_argument("--analyze-text", help="分析指定的文本列")

    # 数据清洗参数
    parser.add_argument("--fill-na", nargs="+", help="填充缺失值，格式: 列名=值 [列名=值 ...]")
    parser.add_argument("--drop-duplicates", action="store_true", help="删除重复行")
    parser.add_argument("--keep-columns", nargs="+", help="保留的列名列表")

    # 数据筛选参数
    parser.add_argument("--filter", nargs="+", help="筛选条件，格式: '列名 操作符 值' [条件2 ...]")

    # 数据可视化参数
    parser.add_argument("--plot", choices=["bar", "line", "scatter", "pie", "histogram"],
                        help="创建图表类型")
    parser.add_argument("--x-column", help="X轴列名(用于图表)")
    parser.add_argument("--y-column", help="Y轴列名(用于图表)")
    parser.add_argument("--title", help="图表标题")
    parser.add_argument("--chart-output", help="图表输出文件路径")

    args = parser.parse_args()

    # 初始化数据处理器
    processor = DataProcessor()

    # 加载数据
    print(f"\n正在加载数据: {args.input_file}")
    if not processor.load_data(args.input_file):
        print("加载数据失败，程序退出")
        return 1

    # 显示摘要统计
    if args.summary:
        print("\n=== 数据摘要统计 ===")
        summary = processor.get_summary()
        print(f"行数: {summary['行数']}")
        print(f"列数: {summary['列数']}")
        print(f"列名: {', '.join(summary['列名'])}")

        print("\n列数据类型:")
        for col, dtype in summary['数据类型'].items():
            print(f"  {col}: {dtype}")

        print("\n缺失值统计:")
        for col, count in summary['缺失值'].items():
            if count > 0:
                print(f"  {col}: {count} ({count / summary['行数'] * 100:.1f}%)")

        print("\n数值型列统计:")
        for col, stats in summary['数值统计'].items():
            print(f"  {col}:")
            print(f"    范围: {stats['最小值']} - {stats['最大值']}")
            print(f"    平均值: {stats['平均值']:.2f}")
            print(f"    中位数: {stats['中位数']:.2f}")
            if '标准差' in stats:
                print(f"    标准差: {stats['标准差']:.2f}")

    # 分析文本列
    if args.analyze_text:
        print(f"\n=== 文本列分析: {args.analyze_text} ===")
        text_analysis = processor.analyze_text_column(args.analyze_text)

        if text_analysis:
            print(f"唯一值数量: {text_analysis['唯一值数量']}")
            print(
                f"字符串长度: {text_analysis['最短值长度']} - {text_analysis['最长值长度']} (平均: {text_analysis['平均长度']:.1f})")

            print("最常见值:")
            for item in text_analysis['最常见值']:
                print(f"  {item['值']}: {item['次数']} 次")

    # 处理数据
    data = processor.data
    modified = False

    # 应用过滤条件
    if args.filter:
        try:
            conditions = [parse_command(cmd) for cmd in args.filter]
            print(f"\n应用筛选条件: {', '.join(args.filter)}")
            data = processor.filter_data(conditions)
            modified = True
        except Exception as e:
            print(f"应用筛选条件失败: {str(e)}")

    # 清洗数据
    clean_options = {}
    if args.fill_na:
        fill_values = {}
        for item in args.fill_na:
            parts = item.split('=', 1)
            if len(parts) == 2:
                col, val = parts
                try:
                    # 尝试转换为适当的类型
                    if val.lower() == 'true':
                        val = True
                    elif val.lower() == 'false':
                        val = False
                    elif val.isdigit():
                        val = int(val)
                    else:
                        try:
                            val = float(val)
                        except ValueError:
                            # 保持为字符串
                            pass

                    fill_values[col] = val
                except Exception as e:
                    print(f"解析填充值失败: {item} - {str(e)}")

        if fill_values:
            clean_options['fill_na'] = fill_values
            print(f"\n填充缺失值: {fill_values}")

    if args.drop_duplicates:
        clean_options['drop_duplicates'] = True
        print("\n删除重复行")

    if args.keep_columns:
        clean_options['columns_to_keep'] = args.keep_columns
        print(f"\n保留列: {', '.join(args.keep_columns)}")

    if clean_options:
        data = processor.clean_data(**clean_options)
        modified = True

        # 更新处理器中的数据以便后续操作
        processor.data = data

    # 可视化数据
    if args.plot:
        print(f"\n创建{args.plot}图表...")
        success = processor.visualize_data(
            chart_type=args.plot,
            x_column=args.x_column,
            y_column=args.y_column,
            output_file=args.chart_output,
            title=args.title
        )

        if success:
            if args.chart_output:
                print(f"图表已保存至: {args.chart_output}")
            else:
                print("图表已显示")
        else:
            print("创建图表失败")

    # 保存处理后的数据
    if args.output and (modified or args.output != args.input_file):
        print(f"\n保存处理后的数据至: {args.output} (格式: {args.format})")
        if processor.convert_data(args.output, args.format):
            print("数据保存成功")
        else:
            print("保存数据失败")

    print("\n处理完成!")
    return 0


if __name__ == "__main__":
    try:
        sys.exit(main())
    except Exception as e:
        logging.error(f"程序异常: {str(e)}")
        sys.exit(1)
