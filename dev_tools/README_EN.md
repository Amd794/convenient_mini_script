<p align="center">
  <a href="./README_EN.md">English</a> |
  <a href="./README.md">简体中文</a> 
</p>

----

# Development Assistance Tools

This directory contains practical tool scripts for assisting software development.

## code_analyzer.py - Code Analysis Tool

This script can analyze code repository structure, count lines of code, evaluate complexity, etc. It supports multiple programming languages and can generate visualization reports to help developers understand the codebase.

### Features

- Supports multiple programming languages (Python, JavaScript, Java, C/C++, HTML, CSS, etc.)
- Counts lines of code, comment lines, and blank lines
- Calculates comment rate and code complexity
- Detects overly long code lines
- Generates detailed HTML analysis reports (including interactive charts)
- Optional visualization charts
- Customizable exclusion of directories and file types

### Dependencies

Dependencies for basic functionality:
```bash
pip install tabulate
```

Dependencies for visualization chart functionality:
```bash
pip install matplotlib numpy
```

### Usage

Basic usage (analyze current directory):
```bash
python code_analyzer.py
```

Analyze a specified directory:
```bash
python code_analyzer.py /path/to/your/project
```

Generate HTML report and specify output file:
```bash
python code_analyzer.py -o report.html
```

Generate visualization charts:
```bash
python code_analyzer.py -c
```

Exclude specified directories:
```bash
python code_analyzer.py -e node_modules build dist
```

Exclude specified file patterns:
```bash
python code_analyzer.py -f "*.min.js" "*.generated.*"
```

Customize maximum line length (longer lines are considered too long):
```bash
python code_analyzer.py -l 80
```

### Complete Command Line Parameters

```
usage: code_analyzer.py [-h] [-o OUTPUT] [-e EXCLUDE_DIRS [EXCLUDE_DIRS ...]]
                        [-f EXCLUDE_FILES [EXCLUDE_FILES ...]] [-l LINE_LENGTH] [-c]
                        [path]

Code Analysis Tool - Analyze code repository structure and statistics

positional arguments:
  path                  Path to the code repository to analyze, default is the current directory

options:
  -h, --help            Show help information and exit
  -o OUTPUT, --output OUTPUT
                        Output report file path
  -e EXCLUDE_DIRS [EXCLUDE_DIRS ...], --exclude-dirs EXCLUDE_DIRS [EXCLUDE_DIRS ...]
                        List of directory names to exclude
  -f EXCLUDE_FILES [EXCLUDE_FILES ...], --exclude-files EXCLUDE_FILES [EXCLUDE_FILES ...]
                        List of file patterns to exclude
  -l LINE_LENGTH, --line-length LINE_LENGTH
                        Maximum line length, longer is considered too long
  -c, --charts          Generate visualization charts
```

### Analysis Report Example

The generated HTML report includes:
- Overall statistics of the code repository (total number of files, lines of code, comment lines, etc.)
- Detailed statistical data for each programming language
- Code composition analysis charts (proportion of code lines, comment lines, blank lines)
- Distribution charts of lines of code for each language
- Complexity score charts for each language 