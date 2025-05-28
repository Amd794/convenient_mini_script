<p align="center">
  <a href="./README_EN.md">English</a> |
  <a href="./README.md">简体中文</a> 
</p>

----

# System Tools

This directory contains practical tool scripts for system monitoring and management.

## system_monitor.py - System Resource Monitoring Tool

This script can monitor system resource usage in real-time, including CPU, memory, disk, and network, and supports exporting monitoring data to CSV files.

### Features

- Real-time display of system resource usage (CPU, memory, disk, network)
- Support for displaying CPU usage by core
- Support for exporting monitoring data to CSV files
- Support for custom monitoring intervals and duration
- Provides silent mode for collecting data in the background

### Dependencies

Using this script requires installing the following Python libraries:

```bash
pip install psutil tabulate
```

### Usage

Basic usage (real-time system resource monitoring):
```bash
python system_monitor.py
```

Specify data refresh interval (in seconds):
```bash
python system_monitor.py -i 5
```

Set monitoring duration (in seconds):
```bash
python system_monitor.py -d 3600  # Stop automatically after monitoring for 1 hour
```

Export monitoring data to a CSV file:
```bash
python system_monitor.py -e system_stats.csv
```

Silent mode, no output but records data:
```bash
python system_monitor.py -q -e system_stats.csv
```

### Complete Command Line Parameters

```
usage: system_monitor.py [-h] [-i INTERVAL] [-d DURATION] [-e EXPORT] [-q]

System Resource Monitoring Tool

options:
  -h, --help            Show help information and exit
  -i INTERVAL, --interval INTERVAL
                        Monitoring data refresh interval (seconds), default is 2 seconds
  -d DURATION, --duration DURATION
                        Monitoring duration (seconds), default is unlimited
  -e EXPORT, --export EXPORT
                        Export monitoring data to CSV file
  -q, --quiet           Silent mode, do not display data in the console
```

### CSV Output Format

The exported CSV file contains the following columns:
- Time - Data recording timestamp
- CPU Usage(%) - Overall CPU usage percentage
- Memory Usage(%) - Memory usage percentage
- Used Memory(GB) - Size of used memory
- Total Memory(GB) - Size of total memory
- Disk Usage(%) - Disk usage percentage
- Used Space(GB) - Used disk space
- Total Space(GB) - Total disk space
- Network Sent(KB/s) - Network sending rate
- Network Received(KB/s) - Network receiving rate 