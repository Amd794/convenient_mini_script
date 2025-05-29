<p align="center">
  <a href="./README_EN.md">English</a> |
  <a href="./README.md">简体中文</a> 
</p>

----

# Network Tools

This directory contains practical tool scripts for network testing and management.

## Network Speed Test Tool (network_speed_test.py)

This script can test various performance indicators of network connections, including download speed, upload speed, latency (ping), etc., and supports result visualization and historical data recording.

### Features

- Tests network download speed, latency (ping), and packet loss rate
- Supports multi-server testing (default uses Cloudflare and Google DNS servers)
- Records historical test results for tracking network performance changes
- Supports displaying test results in table format
- Supports plotting historical data trend charts
- Custom test parameters (such as test size, number of tests, etc.)

### Dependencies

Using this script requires installing the following Python libraries:

```bash
pip install requests tabulate
```

If you need to plot historical data charts, you also need to install:

```bash
pip install matplotlib
```

### Usage

Basic usage (test download speed and latency):
```bash
python network_speed_test.py
```

Test all metrics (including upload speed):
```bash
python network_speed_test.py -a
```

Only test network latency:
```bash
python network_speed_test.py -p
```

View historical test records:
```bash
python network_speed_test.py --history
```

Plot download speed historical trend chart:
```bash
python network_speed_test.py --plot download
```

View the last 5 historical records:
```bash
python network_speed_test.py --history --last 5
```

### Complete Command Line Parameters

```
usage: network_speed_test.py [-h] [-d] [-u] [-p] [-a] [--history]
                            [--plot {download,upload,ping}] [--last LAST]

Network Speed Testing Tool

options:
  -h, --help            Show help information and exit
  -d, --download        Test download speed
  -u, --upload          Test upload speed
  -p, --ping            Test network latency (ping)
  -a, --all             Test all metrics
  --history             Show historical test results
  --plot {download,upload,ping}
                        Plot historical data chart
  --last LAST           Show the last N historical records (for --history and --plot)
```

### Historical Data Storage

Test results will be saved in the `.network_speed_history.json` file in the user's home directory, making it convenient to track network performance changes.

## Batch File Downloader Tool (batch_downloader.py)

This tool is used for batch downloading files from the network, supporting concurrent downloads, resume capability, automatic retries, and more.

### Features

- Batch download multiple URLs
- Support concurrent downloads for improved efficiency
- Resume capability for interrupted downloads
- Automatic retry on download failures
- Detailed progress display
- Support for reading URLs from a file
- Custom HTTP headers
- Detailed download statistics
- Custom filenames and extensions
- Automatic file extension detection from Content-Type
- Force specified file extension, ignoring extensions in URLs
- Random delay support to avoid being detected as a scraper
- Download state saving and restoration for continuing interrupted downloads

### Usage

```bash
python batch_downloader.py [URL...] [options]

Options:
  -f, --file FILE         File containing URLs, one per line
  -o, --output-dir DIR    Directory to save downloaded files (default: ./downloads)
  -w, --workers NUMBER    Number of concurrent downloads (default: 5)
  -t, --timeout SECONDS   Connection timeout in seconds (default: 30)
  -r, --retries NUMBER    Number of download retry attempts (default: 3)
  -s, --suffix EXT        Default file suffix for URLs without a clear file type
  --force-suffix          Force using specified suffix, ignoring extensions in URLs
  --name-map FILE         URL to filename mapping file (JSON or CSV format)
  --no-verify             Do not verify SSL certificates
  --no-resume             Disable download resuming
  --overwrite             Overwrite existing files
  --header HEADER         Add HTTP header, format 'Name: Value'
  --debug                 Enable debug logging
  --no-progress           Disable progress bar
  --random-delay          Enable random delay to avoid being detected as a scraper
  --min-delay SECONDS     Minimum delay in seconds (default: 1.0)
  --max-delay SECONDS     Maximum delay in seconds (default: 5.0)
  --continue              Continue incomplete downloads from previous sessions
  --state-file FILE       Path to save download state file
```

### Examples

```bash
# Download a single file
python batch_downloader.py https://example.com/file.zip

# Batch download URLs from a text file
python batch_downloader.py -f urls.txt -o ./downloads

# Download using 10 concurrent connections
python batch_downloader.py -f urls.txt -w 10

# Add .mp4 extension to files without extensions
python batch_downloader.py -f urls.txt -s mp4

# Force all files to be saved as .torrent format, ignoring extensions in URLs
python batch_downloader.py -f urls.txt -s torrent --force-suffix

# Use a mapping file to specify filenames
python batch_downloader.py -f urls.txt --name-map mappings.json

# Add custom HTTP headers and enable random delay
python batch_downloader.py -f urls.txt --header "Referer: https://example.com" --random-delay

# Continue incomplete downloads from previous session
python batch_downloader.py -f urls.txt --continue
```

### Filename Mapping

You can use a JSON or CSV format mapping file to specify custom filenames for each URL:

- **JSON Format**:
```json
{
  "https://example.com/file1": "custom_filename1.mp4",
  "https://example.com/file2": "custom_filename2.pdf"
}
```

- **CSV Format**:
```csv
https://example.com/file1,custom_filename1.mp4
https://example.com/file2,custom_filename2.pdf
```

### Dependencies

- Python 3.7+
- httpx
- tqdm (optional, for progress display)

Install dependencies:
```bash
pip install httpx tqdm
``` 