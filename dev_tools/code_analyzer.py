#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
代码分析工具

这个脚本可以分析代码库的结构、统计代码量、评估复杂度等，
支持多种编程语言，可生成可视化报告，帮助开发者了解代码库情况。
"""

import argparse
import datetime
import logging
import os
import re
from collections import defaultdict

# 尝试导入可选依赖
try:
    import matplotlib.pyplot as plt
    import numpy as np

    HAS_MATPLOTLIB = True
except ImportError:
    HAS_MATPLOTLIB = False

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)

# 支持的编程语言及其文件扩展名和注释符号
LANGUAGES = {
    'Python': {
        'extensions': ['.py', '.pyw'],
        'line_comment': '#',
        'block_comment': ['"""', "'''"],
        'color': 'blue'
    },
    'JavaScript': {
        'extensions': ['.js', '.jsx', '.ts', '.tsx'],
        'line_comment': '//',
        'block_comment': ['/*', '*/'],
        'color': 'yellow'
    },
    'Java': {
        'extensions': ['.java'],
        'line_comment': '//',
        'block_comment': ['/*', '*/'],
        'color': 'orange'
    },
    'C/C++': {
        'extensions': ['.c', '.cpp', '.h', '.hpp'],
        'line_comment': '//',
        'block_comment': ['/*', '*/'],
        'color': 'red'
    },
    'HTML': {
        'extensions': ['.html', '.htm'],
        'line_comment': '',
        'block_comment': ['<!--', '-->'],
        'color': 'green'
    },
    'CSS': {
        'extensions': ['.css', '.scss', '.sass', '.less'],
        'line_comment': '',
        'block_comment': ['/*', '*/'],
        'color': 'purple'
    },
    'PHP': {
        'extensions': ['.php'],
        'line_comment': '//',
        'block_comment': ['/*', '*/'],
        'color': 'pink'
    },
    'Go': {
        'extensions': ['.go'],
        'line_comment': '//',
        'block_comment': ['/*', '*/'],
        'color': 'cyan'
    },
    'Ruby': {
        'extensions': ['.rb'],
        'line_comment': '#',
        'block_comment': ['=begin', '=end'],
        'color': 'brown'
    },
    'Rust': {
        'extensions': ['.rs'],
        'line_comment': '//',
        'block_comment': ['/*', '*/'],
        'color': 'gray'
    },
    'Other': {
        'extensions': [],
        'line_comment': '',
        'block_comment': [],
        'color': 'black'
    }
}


class CodeAnalyzer:
    """代码分析类，提供代码库分析功能"""

    def __init__(self, path, exclude_dirs=None, exclude_files=None, max_line_length=100):
        """
        初始化代码分析器
        
        Args:
            path (str): 要分析的代码库路径
            exclude_dirs (list): 要排除的目录列表
            exclude_files (list): 要排除的文件模式列表
            max_line_length (int): 最大行长度，超过则视为过长行
        """
        self.path = os.path.abspath(path)
        self.exclude_dirs = exclude_dirs or ['.git', '.svn', '.hg', '__pycache__', 'node_modules', 'venv', '.venv',
                                             'env', '.env']
        self.exclude_files = exclude_files or ['*.min.js', '*.min.css', '*.svg', '*.png', '*.jpg', '*.jpeg', '*.gif',
                                               '*.ico']
        self.max_line_length = max_line_length
        self.results = {}
        self.extension_map = self._build_extension_map()

    def _build_extension_map(self):
        """构建文件扩展名到语言的映射"""
        extension_map = {}
        for lang, info in LANGUAGES.items():
            for ext in info['extensions']:
                extension_map[ext] = lang
        return extension_map

    def _is_excluded(self, path):
        """检查路径是否应该被排除"""
        # 检查是否在排除目录中
        for excluded_dir in self.exclude_dirs:
            if f"/{excluded_dir}/" in path.replace("\\", "/") or path.replace("\\", "/").endswith(f"/{excluded_dir}"):
                return True

        # 检查是否匹配排除文件模式
        filename = os.path.basename(path)
        for pattern in self.exclude_files:
            if self._match_pattern(filename, pattern):
                return True

        return False

    def _match_pattern(self, filename, pattern):
        """简单的文件名模式匹配"""
        # 将*转换为正则表达式
        regex = "^" + pattern.replace(".", "\\.").replace("*", ".*") + "$"
        return bool(re.match(regex, filename))

    def _get_language(self, file_path):
        """根据文件扩展名确定编程语言"""
        _, ext = os.path.splitext(file_path.lower())
        return self.extension_map.get(ext, 'Other')

    def _count_lines(self, file_path):
        """统计文件的代码行、注释行和空行"""
        language = self._get_language(file_path)
        lang_info = LANGUAGES[language]

        line_comment = lang_info['line_comment']
        block_comment_start = lang_info['block_comment'][0] if lang_info['block_comment'] else None
        block_comment_end = lang_info['block_comment'][1] if len(lang_info['block_comment']) > 1 else None

        total_lines = 0
        code_lines = 0
        comment_lines = 0
        blank_lines = 0
        long_lines = 0
        in_block_comment = False

        try:
            with open(file_path, 'r', encoding='utf-8', errors='replace') as f:
                for line in f:
                    total_lines += 1
                    stripped = line.strip()

                    # 检查行长度
                    if len(line.rstrip('\r\n')) > self.max_line_length:
                        long_lines += 1

                    # 空行
                    if not stripped:
                        blank_lines += 1
                        continue

                    # 注释行（块注释内或行注释）
                    if in_block_comment:
                        comment_lines += 1
                        if block_comment_end and block_comment_end in stripped:
                            in_block_comment = False
                        continue

                    if block_comment_start and block_comment_start in stripped:
                        comment_lines += 1
                        if block_comment_end and block_comment_end in stripped[stripped.find(block_comment_start) + len(
                                block_comment_start):]:
                            pass  # 单行块注释
                        else:
                            in_block_comment = True
                        continue

                    if line_comment and stripped.startswith(line_comment):
                        comment_lines += 1
                        continue

                    # 代码行
                    code_lines += 1

        except Exception as e:
            logging.error(f"处理文件 {file_path} 时出错: {str(e)}")
            return 0, 0, 0, 0, 0

        return total_lines, code_lines, comment_lines, blank_lines, long_lines

    def _estimate_complexity(self, file_path):
        """估计文件的复杂度（简化版）"""
        language = self._get_language(file_path)

        # 分支、循环和条件语句的关键字
        complexity_keywords = {
            'Python': ['if', 'elif', 'else', 'for', 'while', 'except', 'with'],
            'JavaScript': ['if', 'else', 'for', 'while', 'switch', 'case', 'try', 'catch'],
            'Java': ['if', 'else', 'for', 'while', 'switch', 'case', 'try', 'catch'],
            'C/C++': ['if', 'else', 'for', 'while', 'switch', 'case', 'try', 'catch'],
            'PHP': ['if', 'else', 'elseif', 'for', 'foreach', 'while', 'switch', 'case', 'try', 'catch'],
            'Go': ['if', 'else', 'for', 'switch', 'case', 'select'],
            'Ruby': ['if', 'elsif', 'else', 'unless', 'case', 'when', 'for', 'while', 'until', 'begin', 'rescue'],
            'Rust': ['if', 'else', 'match', 'for', 'while', 'loop']
        }

        keywords = complexity_keywords.get(language, [])
        if not keywords:
            return 0

        complexity = 0
        try:
            with open(file_path, 'r', encoding='utf-8', errors='replace') as f:
                content = f.read()

                # 简单的基于关键字的复杂度估计
                for keyword in keywords:
                    # 使用正则表达式匹配独立的关键字
                    pattern = r'\b' + keyword + r'\b'
                    complexity += len(re.findall(pattern, content))

        except Exception as e:
            logging.error(f"分析文件复杂度 {file_path} 时出错: {str(e)}")

        return complexity

    def analyze(self):
        """分析代码库并生成结果"""
        logging.info(f"开始分析代码库: {self.path}")

        stats = defaultdict(lambda: {
            'files': 0,
            'total_lines': 0,
            'code_lines': 0,
            'comment_lines': 0,
            'blank_lines': 0,
            'long_lines': 0,
            'complexity': 0,
            'file_paths': []
        })

        total_stats = {
            'files': 0,
            'total_lines': 0,
            'code_lines': 0,
            'comment_lines': 0,
            'blank_lines': 0,
            'long_lines': 0,
            'complexity': 0
        }

        file_count = 0
        for root, dirs, files in os.walk(self.path):
            # 排除目录
            dirs[:] = [d for d in dirs if d not in self.exclude_dirs]

            for file in files:
                file_path = os.path.join(root, file)

                # 检查是否应该排除
                if self._is_excluded(file_path):
                    continue

                # 确定文件的编程语言
                language = self._get_language(file_path)
                if language == 'Other':
                    continue

                # 统计行数
                total_lines, code_lines, comment_lines, blank_lines, long_lines = self._count_lines(file_path)

                # 估计复杂度
                complexity = self._estimate_complexity(file_path)

                # 更新语言统计信息
                stats[language]['files'] += 1
                stats[language]['total_lines'] += total_lines
                stats[language]['code_lines'] += code_lines
                stats[language]['comment_lines'] += comment_lines
                stats[language]['blank_lines'] += blank_lines
                stats[language]['long_lines'] += long_lines
                stats[language]['complexity'] += complexity
                stats[language]['file_paths'].append(file_path)

                # 更新总体统计信息
                total_stats['files'] += 1
                total_stats['total_lines'] += total_lines
                total_stats['code_lines'] += code_lines
                total_stats['comment_lines'] += comment_lines
                total_stats['blank_lines'] += blank_lines
                total_stats['long_lines'] += long_lines
                total_stats['complexity'] += complexity

                file_count += 1
                if file_count % 100 == 0:
                    logging.info(f"已分析 {file_count} 个文件...")

        self.results = {
            'by_language': dict(stats),
            'total': total_stats,
            'timestamp': datetime.datetime.now().isoformat()
        }

        logging.info(f"分析完成，共 {total_stats['files']} 个文件，{total_stats['total_lines']} 行代码")
        return self.results

    def generate_report(self, output_file=None):
        """生成分析报告"""
        if not self.results:
            logging.warning("没有分析结果可供报告")
            return

        # 如果未指定输出文件，使用默认名称
        if not output_file:
            timestamp = datetime.datetime.now().strftime('%Y%m%d_%H%M%S')
            output_file = f"code_analysis_{timestamp}.html"

        # 计算评论比例
        for lang, data in self.results['by_language'].items():
            if data['code_lines'] > 0:
                comment_ratio = data['comment_lines'] / data['code_lines'] * 100
            else:
                comment_ratio = 0
            data['comment_ratio'] = comment_ratio

        # 生成HTML报告
        html_content = self._generate_html_report()

        try:
            with open(output_file, 'w', encoding='utf-8') as f:
                f.write(html_content)
            logging.info(f"分析报告已保存至: {output_file}")
            return output_file
        except Exception as e:
            logging.error(f"保存报告失败: {str(e)}")
            return None

    def _generate_html_report(self):
        """生成HTML格式的报告"""
        # 计算总计数据
        total = self.results['total']
        timestamp = datetime.datetime.fromisoformat(self.results['timestamp']).strftime('%Y-%m-%d %H:%M:%S')

        # 开始构建HTML
        html = f"""<!DOCTYPE html>
<html lang="zh-CN">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>代码库分析报告</title>
    <style>
        body {{
            font-family: Arial, sans-serif;
            line-height: 1.6;
            color: #333;
            max-width: 1200px;
            margin: 0 auto;
            padding: 20px;
        }}
        h1, h2, h3 {{
            color: #2c3e50;
        }}
        table {{
            width: 100%;
            border-collapse: collapse;
            margin: 20px 0;
        }}
        th, td {{
            padding: 12px 15px;
            text-align: left;
            border-bottom: 1px solid #ddd;
        }}
        th {{
            background-color: #f2f2f2;
        }}
        tr:hover {{
            background-color: #f5f5f5;
        }}
        .summary {{
            background-color: #e8f4f8;
            padding: 15px;
            border-radius: 5px;
            margin-bottom: 20px;
        }}
        .chart-container {{
            display: flex;
            justify-content: space-between;
            flex-wrap: wrap;
            margin: 30px 0;
        }}
        .chart {{
            width: 48%;
            min-width: 400px;
            height: 400px;
            margin-bottom: 30px;
            box-shadow: 0 0 10px rgba(0,0,0,0.1);
            padding: 10px;
            box-sizing: border-box;
        }}
        .footer {{
            margin-top: 30px;
            padding-top: 10px;
            border-top: 1px solid #eee;
            color: #777;
            font-size: 0.9em;
        }}
    </style>
</head>
<body>
    <h1>代码库分析报告</h1>
    <p>分析时间: {timestamp}</p>
    <p>代码库路径: {self.path}</p>
    
    <div class="summary">
        <h2>总体统计</h2>
        <p>总文件数: {total['files']}</p>
        <p>总代码行: {total['total_lines']}</p>
        <p>有效代码行: {total['code_lines']}</p>
        <p>注释行: {total['comment_lines']}</p>
        <p>空行: {total['blank_lines']}</p>
        <p>过长行(>{self.max_line_length}字符): {total['long_lines']}</p>
        <p>注释率: {total['comment_lines'] / total['code_lines'] * 100:.2f}% (注释行/代码行)</p>
        <p>总体复杂度评分: {total['complexity']}</p>
    </div>
    
    <h2>按编程语言统计</h2>
    <table>
        <tr>
            <th>语言</th>
            <th>文件数</th>
            <th>代码行</th>
            <th>注释行</th>
            <th>空行</th>
            <th>注释率</th>
            <th>过长行</th>
            <th>复杂度评分</th>
        </tr>
"""

        # 按代码行数排序语言
        sorted_languages = sorted(
            self.results['by_language'].items(),
            key=lambda x: x[1]['code_lines'],
            reverse=True
        )

        # 添加每种语言的行
        for language, data in sorted_languages:
            comment_ratio = data['comment_ratio']
            html += f"""
        <tr>
            <td>{language}</td>
            <td>{data['files']}</td>
            <td>{data['code_lines']}</td>
            <td>{data['comment_lines']}</td>
            <td>{data['blank_lines']}</td>
            <td>{comment_ratio:.2f}%</td>
            <td>{data['long_lines']}</td>
            <td>{data['complexity']}</td>
        </tr>"""

        html += """
    </table>
    
    <div class="chart-container">
        <div class="chart" id="languageDistribution">
            <canvas id="languageChart"></canvas>
        </div>
        <div class="chart" id="codeComposition">
            <canvas id="compositionChart"></canvas>
        </div>
    </div>
    
    <h2>复杂度评估</h2>
    <div class="chart-container">
        <div class="chart" id="complexityChart">
            <canvas id="complexityCanvas"></canvas>
        </div>
    </div>
    
    <div class="footer">
        <p>由代码分析工具生成 - code_analyzer.py</p>
    </div>
    
    <script src="https://cdn.jsdelivr.net/npm/chart.js"></script>
    <script>
        // 准备语言分布图表数据
        const languageData = {
            labels: [
"""

        # 添加图表数据 - 语言标签
        for language, _ in sorted_languages:
            html += f"                '{language}',\n"

        html += """
            ],
            datasets: [{
                label: '代码行数',
                data: [
"""

        # 添加图表数据 - 语言代码行数
        for _, data in sorted_languages:
            html += f"                    {data['code_lines']},\n"

        html += """
                ],
                backgroundColor: [
"""

        # 添加图表数据 - 语言颜色
        for language, _ in sorted_languages:
            color = LANGUAGES.get(language, LANGUAGES['Other'])['color']
            html += f"                    '{color}',\n"

        html += """
                ],
                hoverOffset: 4
            }]
        };

        // 准备代码组成图表数据
        const compositionData = {
            labels: ['代码行', '注释行', '空行'],
            datasets: [{
                label: '行数',
                data: [
"""

        html += f"""
                    {total['code_lines']},
                    {total['comment_lines']},
                    {total['blank_lines']},
"""

        html += """
                ],
                backgroundColor: [
                    'rgba(54, 162, 235, 0.6)',
                    'rgba(255, 206, 86, 0.6)',
                    'rgba(75, 192, 192, 0.6)'
                ],
                borderColor: [
                    'rgba(54, 162, 235, 1)',
                    'rgba(255, 206, 86, 1)',
                    'rgba(75, 192, 192, 1)'
                ],
                borderWidth: 1
            }]
        };
        
        // 准备复杂度图表数据
        const complexityData = {
            labels: [
"""

        # 添加复杂度图表数据 - 语言标签
        for language, _ in sorted_languages:
            html += f"                '{language}',\n"

        html += """
            ],
            datasets: [{
                label: '复杂度评分',
                data: [
"""

        # 添加复杂度图表数据 - 复杂度分数
        for _, data in sorted_languages:
            html += f"                    {data['complexity']},\n"

        html += """
                ],
                backgroundColor: 'rgba(153, 102, 255, 0.6)',
                borderColor: 'rgba(153, 102, 255, 1)',
                borderWidth: 1
            }]
        };

        // 创建图表
        window.onload = function() {
            // 语言分布饼图
            const languageCtx = document.getElementById('languageChart').getContext('2d');
            new Chart(languageCtx, {
                type: 'pie',
                data: languageData,
                options: {
                    plugins: {
                        title: {
                            display: true,
                            text: '代码行数按编程语言分布',
                            font: {
                                size: 16
                            }
                        },
                        legend: {
                            position: 'bottom'
                        }
                    }
                }
            });
            
            // 代码组成饼图
            const compositionCtx = document.getElementById('compositionChart').getContext('2d');
            new Chart(compositionCtx, {
                type: 'pie',
                data: compositionData,
                options: {
                    plugins: {
                        title: {
                            display: true,
                            text: '代码组成分析',
                            font: {
                                size: 16
                            }
                        },
                        legend: {
                            position: 'bottom'
                        }
                    }
                }
            });
            
            // 复杂度条形图
            const complexityCtx = document.getElementById('complexityCanvas').getContext('2d');
            new Chart(complexityCtx, {
                type: 'bar',
                data: complexityData,
                options: {
                    plugins: {
                        title: {
                            display: true,
                            text: '各语言复杂度评分',
                            font: {
                                size: 16
                            }
                        },
                        legend: {
                            display: false
                        }
                    },
                    scales: {
                        y: {
                            beginAtZero: true,
                            title: {
                                display: true,
                                text: '复杂度评分'
                            }
                        }
                    }
                }
            });
        };
    </script>
</body>
</html>
"""

        return html

    def plot_charts(self):
        """绘制分析结果图表"""
        if not HAS_MATPLOTLIB:
            logging.warning("绘制图表需要安装matplotlib: pip install matplotlib")
            return

        if not self.results:
            logging.warning("没有分析结果可供绘图")
            return

        # 准备数据
        languages = []
        code_lines = []
        comment_ratios = []
        complexities = []

        sorted_languages = sorted(
            self.results['by_language'].items(),
            key=lambda x: x[1]['code_lines'],
            reverse=True
        )

        for language, data in sorted_languages:
            languages.append(language)
            code_lines.append(data['code_lines'])

            if data['code_lines'] > 0:
                comment_ratios.append(data['comment_lines'] / data['code_lines'] * 100)
            else:
                comment_ratios.append(0)

            complexities.append(data['complexity'])

        # 取前10种语言以保持图表可读性
        if len(languages) > 10:
            languages = languages[:10]
            code_lines = code_lines[:10]
            comment_ratios = comment_ratios[:10]
            complexities = complexities[:10]

        # 创建一组子图
        fig, axes = plt.subplots(2, 2, figsize=(15, 12))

        # 1. 代码行数分布饼图
        axes[0, 0].pie(code_lines, labels=languages, autopct='%1.1f%%', startangle=90)
        axes[0, 0].set_title('代码行数分布')

        # 2. 每种语言的代码行数条形图
        y_pos = np.arange(len(languages))
        axes[0, 1].barh(y_pos, code_lines, align='center')
        axes[0, 1].set_yticks(y_pos)
        axes[0, 1].set_yticklabels(languages)
        axes[0, 1].set_xlabel('代码行数')
        axes[0, 1].set_title('各语言代码行数')

        # 3. 注释比例条形图
        axes[1, 0].bar(languages, comment_ratios)
        axes[1, 0].set_ylabel('注释率 (%)')
        axes[1, 0].set_title('各语言注释率')
        plt.setp(axes[1, 0].xaxis.get_majorticklabels(), rotation=45, ha="right")

        # 4. 复杂度得分条形图
        axes[1, 1].bar(languages, complexities, color='orange')
        axes[1, 1].set_ylabel('复杂度评分')
        axes[1, 1].set_title('各语言复杂度评分')
        plt.setp(axes[1, 1].xaxis.get_majorticklabels(), rotation=45, ha="right")

        # 调整布局
        plt.tight_layout()

        # 保存和显示图表
        timestamp = datetime.datetime.now().strftime('%Y%m%d_%H%M%S')
        chart_file = f"code_analysis_charts_{timestamp}.png"
        plt.savefig(chart_file)
        plt.show()

        logging.info(f"分析图表已保存至: {chart_file}")
        return chart_file


def main():
    """主函数"""
    parser = argparse.ArgumentParser(description="代码分析工具 - 分析代码库结构和统计")
    parser.add_argument("path", nargs="?", default=".", help="要分析的代码库路径，默认为当前目录")
    parser.add_argument("-o", "--output", help="输出报告的文件路径")
    parser.add_argument("-e", "--exclude-dirs", nargs="+", help="要排除的目录名列表")
    parser.add_argument("-f", "--exclude-files", nargs="+", help="要排除的文件模式列表")
    parser.add_argument("-l", "--line-length", type=int, default=100, help="最大行长度，超过视为过长")
    parser.add_argument("-c", "--charts", action="store_true", help="生成可视化图表")

    args = parser.parse_args()

    print(f"\n正在分析代码库: {args.path}")
    print("=" * 50)

    # 创建和运行分析器
    analyzer = CodeAnalyzer(
        path=args.path,
        exclude_dirs=args.exclude_dirs,
        exclude_files=args.exclude_files,
        max_line_length=args.line_length
    )

    # 分析代码
    results = analyzer.analyze()

    # 显示简要结果
    total = results['total']
    print("\n代码库分析结果摘要:")
    print(f"总文件数: {total['files']}")
    print(f"总行数: {total['total_lines']}")
    print(f"代码行: {total['code_lines']}")
    print(f"注释行: {total['comment_lines']}")
    print(f"空行: {total['blank_lines']}")
    print(f"注释率: {total['comment_lines'] / total['code_lines'] * 100:.2f}% (注释行/代码行)")

    print("\n按编程语言统计:")
    for language, data in sorted(results['by_language'].items(), key=lambda x: x[1]['code_lines'], reverse=True):
        print(f"{language}: {data['files']} 个文件, {data['code_lines']} 行代码")

    # 生成报告
    report_file = analyzer.generate_report(args.output)
    if report_file:
        print(f"\n详细报告已保存至: {report_file}")

    # 生成图表
    if args.charts:
        if HAS_MATPLOTLIB:
            chart_file = analyzer.plot_charts()
            if chart_file:
                print(f"分析图表已保存至: {chart_file}")
        else:
            print("\n警告: 缺少matplotlib库，无法生成图表。")
            print("请安装matplotlib: pip install matplotlib")

    print("=" * 50)


if __name__ == "__main__":
    # 检查依赖
    try:
        import tabulate
    except ImportError:
        print("\n警告: 缺少tabulate库，可能影响输出格式。")
        print("请安装tabulate: pip install tabulate\n")

    try:
        import requests
    except ImportError:
        pass  # requests不是必需的

    main()
