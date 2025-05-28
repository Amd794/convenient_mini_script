# Data Processing Tool (data_processor.py)

This tool can process CSV and Excel files, providing data analysis, conversion, cleaning, and visualization functions to help users efficiently process and analyze tabular data.

## Main Features

- **Data Loading and Parsing** - Supports CSV, Excel, and JSON formats
- **Data Statistical Analysis** - Calculates basic statistics (mean, median, standard deviation, etc.)
- **Data Cleaning** - Handles missing values, removes duplicates, retains specific columns
- **Data Filtering** - Filters data by conditions
- **Data Format Conversion** - Converts between CSV, Excel, and JSON formats
- **Data Visualization** - Creates various charts (bar charts, line graphs, scatter plots, etc.)
- **Text Analysis** - Analyzes patterns and statistics of text columns

## Dependencies

Core functionality dependencies:
- Python 3.6+
- Standard libraries: os, sys, json, csv, argparse, logging

Extended functionality dependencies:
- pandas - Data processing and analysis
- matplotlib - Data visualization
- numpy - Mathematical computation support
- openpyxl - Excel file handling

> Note: The tool will automatically adjust functionality based on available libraries. Without pandas, only basic CSV processing is supported; without matplotlib, visualization features are not supported.

## Installing Dependencies

```bash
pip install pandas matplotlib numpy openpyxl
```

## Usage

### Basic Usage

```bash
python data_processor.py data_file.csv [options]
```

### Common Options

| Option | Description |
|--------|-------------|
| `-o, --output file_path` | Output file path |
| `-f, --format {csv,excel,json}` | Output format (default: csv) |
| `--summary` | Display data summary statistics |
| `--analyze-text column_name` | Analyze the specified text column |
| `--fill-na column=value [column=value ...]` | Fill missing values |
| `--drop-duplicates` | Remove duplicate rows |
| `--keep-columns column [column ...]` | Specify columns to retain |
| `--filter "column operator value" ["column operator value" ...]` | Filter conditions |

### Data Visualization Options

| Option | Description |
|--------|-------------|
| `--plot {bar,line,scatter,pie,histogram}` | Chart type to create |
| `--x-column column_name` | X-axis column name |
| `--y-column column_name` | Y-axis column name |
| `--title title` | Chart title |
| `--chart-output file_path` | Chart output file path |

## Example Usage

### Basic Data Analysis

```bash
# Display summary statistics for a CSV file
python data_processor.py data.csv --summary
```

### Data Cleaning and Conversion

```bash
# Remove duplicates, fill empty values, and convert to JSON format
python data_processor.py data.csv --drop-duplicates --fill-na "age=0" "city=unknown" -o cleaned_data.json -f json
```

### Data Filtering

```bash
# Filter records where age is greater than 30 and city is Beijing
python data_processor.py customer_data.csv --filter "age > 30" "city == Beijing" -o filtered_results.csv
```

### Column Selection and Retention

```bash
# Only keep name, age, and phone columns
python data_processor.py complete_data.csv --keep-columns name age phone -o simplified_data.csv
```

### Data Visualization

```bash
# Create age distribution histogram
python data_processor.py population_data.csv --plot histogram --x-column age --title "Age Distribution" --chart-output age_distribution.png

# Create city population bar chart
python data_processor.py population_data.csv --plot bar --x-column city --y-column population --title "City Populations" --chart-output city_population.png
```

### Text Analysis

```bash
# Analyze product description column
python data_processor.py product_data.csv --analyze-text product_description
```

## Using in Code

```python
from data_processor import DataProcessor

# Initialize processor
processor = DataProcessor('data.csv')

# Get data summary
summary = processor.get_summary()
print(f"Number of rows: {summary['rows']}")

# Filter data
filtered_data = processor.filter_data([
    ('age', '>', 30),
    ('city', '==', 'Shanghai')
])

# Clean data
cleaned_data = processor.clean_data(
    fill_na={'income': 0, 'education': 'unknown'},
    drop_duplicates=True
)

# Save as Excel
processor.convert_data('output.xlsx', 'excel')

# Create visualization
processor.visualize_data(
    chart_type='bar',
    x_column='department',
    y_column='sales',
    title='Sales by Department',
    output_file='sales_chart.png'
)
```

## Filter Operators

Supported filter operators:
- `==` : Equals
- `!=` : Not equals
- `>` : Greater than
- `<` : Less than
- `>=` : Greater than or equal to
- `<=` : Less than or equal to
- `contains` : Contains substring
- `startswith` : Starts with
- `endswith` : Ends with

## Notes

- If using filenames or values with spaces on Windows systems, please surround them with quotes
- When using the --filter option, each filter condition must be surrounded by quotes
- For large datasets, it is recommended to install pandas for better performance 