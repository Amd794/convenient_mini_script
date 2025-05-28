<p align="center">
  <a href="./README_EN.md">English</a> |
  <a href="./README.md">简体中文</a> 
</p>

----

# Network Tools

This directory contains practical tool scripts for network testing and management.

## network_speed_test.py - Network Speed Testing Tool

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