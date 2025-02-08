# Network Health Monitor 

## Project Overview
The **Network Health Monitor** project is designed to monitor and assess the health of multiple network devices (laptops, routers) in real-time. It utilizes **WMI** (Windows Management Instrumentation) for retrieving device data and **SQLite** for storing the monitoring results. This project is implemented in **Python** and continuously tracks device health metrics like CPU usage, memory, disk space, and battery status.

### Features
- **Real-time Monitoring**: Monitors multiple devices on the same network.
- **Alerting**: Sends email alerts for high CPU usage and displays pop-up alerts.
- **Data Visualization**: Generates graphs for CPU and memory usage.
- **Database Logging**: Stores monitoring data in a local SQLite database.
- **Cross-Platform Support**: Works on Windows OS.

## Technologies Used
- **Python 3.x**: The primary programming language.
- **WMI**: For monitoring system performance on Windows devices.
- **SQLite**: Database for storing monitored data.
- **Psutil**: For advanced system and process monitoring.
- **SMTP**: For sending email alerts.
- **PrettyTable**: For displaying monitoring data in tabular format.
- **Matplotlib**: For plotting system performance graphs.

## Requirements
- Python 3.x
- Required Python libraries:
  - `wmi`
  - `psutil`
  - `sqlite3`
  - `smtplib`
  - `prettytable`
  - `matplotlib`
  
To install the required libraries, run:

```bash
pip install wmi psutil prettytable matplotlib
