import wmi
import sqlite3
import time
import smtplib
import re  # For email validation
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from prettytable import PrettyTable
import psutil 

# Create a new database file
conn = sqlite3.connect('monitoring_data.db')  # Use a new database name
cursor = conn.cursor()

# Create a new table without the GPU performance column
cursor.execute('''
    CREATE TABLE IF NOT EXISTS monitoring_data (
        timestamp TEXT,
        ip_address TEXT,
        cpu_load REAL,
        memory_in_use_mb REAL,
        free_disk_space_gb REAL,
        battery_status TEXT,
        battery_life_remaining INTEGER,
        system_performance_score REAL
    )
''')

conn.commit()

# Email validation function
def is_valid_email(gmail):
    regex = r'^[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+$'
    return re.match(regex, gmail) is not None

# Function to send email alert if CPU load exceeds 80%
def send_email_alert(gmail_account, cpu_load, ip_address):
    sender_email = "jayapriyamkumar@gmail.com"
    sender_password = "ewrpykeqqibdvnku"  
    
    receiver_email = gmail_account
    subject = "High CPU Load Alert"
    
    # Create the email content
    message = MIMEMultipart()
    message['From'] = sender_email
    message['To'] = receiver_email
    message['Subject'] = subject

    body = f"Warning! The CPU load on device {ip_address} has reached {cpu_load}%."
    message.attach(MIMEText(body, 'plain'))

    # Send the email
    try:
        server = smtplib.SMTP_SSL('smtp.gmail.com', 465)
        server.login(sender_email, sender_password)
        server.sendmail(sender_email, receiver_email, message.as_string())
        server.quit()
        print(f"Alert email sent to {gmail_account} for IP: {ip_address}")
    except Exception as e:
        print(f"Failed to send alert email: {e}")

# Function to query and display data from a single laptop
def query_laptop(connection, ip):
    try:
        # Operating System Information Table
        os_table = PrettyTable()
        os_table.field_names = ["OS Name", "Version", "System Directory", "Boot-up Device", "Memory In Use (MB)", "Total Virtual Memory (MB)"]
        
        for os in connection.Win32_OperatingSystem():
            total_memory_mb = int(os.TotalVisibleMemorySize) / 1024
            free_memory_mb = int(os.FreePhysicalMemory) / 1024
            memory_in_use_mb = total_memory_mb - free_memory_mb
            
            os_table.add_row([os.Name,
                              os.Version,
                              os.SystemDirectory,
                              os.BootDevice,
                              memory_in_use_mb,
                              int(os.TotalVirtualMemorySize) / 1024])
        print(f"Operating System Information for {ip}")
        print(os_table)

        # CPU Information Table
        cpu_table = PrettyTable()
        cpu_table.field_names = ["CPU Load (%)", "Manufacturer", "Number of Cores", "Max Clock Speed (MHz)"]
        
        for cpu in connection.Win32_Processor():
            cpu_table.add_row([cpu.LoadPercentage,
                               cpu.Manufacturer,
                               cpu.NumberOfCores,
                               cpu.MaxClockSpeed])
        print(f"CPU Information for {ip}")
        print(cpu_table)

        # Disk/Storage Information Table
        disk_table = PrettyTable()
        disk_table.field_names = ["Drive", "Free Space (GB)", "Total Size (GB)", "Disk Type", "File System"]
        
        for disk in connection.Win32_LogicalDisk():
            if disk.FreeSpace:  # To avoid NoneType errors
                disk_table.add_row([disk.DeviceID, 
                                    int(disk.FreeSpace) / (1024**3), 
                                    int(disk.Size) / (1024**3), 
                                    disk.Description, 
                                    disk.FileSystem])
        print(f"Disk/Storage Information for {ip}")
        print(disk_table)

        # Battery Status Table (if available)
        battery_table = PrettyTable()
        battery_table.field_names = ["Battery Status", "Estimated Battery Life Remaining (%)", "Battery Capacity (mWh)"]

        for battery in connection.Win32_Battery():
            status = "Charging" if battery.BatteryStatus == 2 else "Discharging" if battery.BatteryStatus == 1 else "Unknown"
            battery_table.add_row([status, 
                                   battery.EstimatedChargeRemaining, 
                                   battery.DesignCapacity])
        print(f"Battery Status for {ip}")
        print(battery_table)

    except Exception as e:
        print(f"Failed to query {ip}. Error: {e}")

# Function to collect network performance
def collect_network_performance():
    # First snapshot of network stats
    net_io_1 = psutil.net_io_counters()
    bytes_sent_1 = net_io_1.bytes_sent
    bytes_recv_1 = net_io_1.bytes_recv

    # Wait for 1 second
    time.sleep(1)

    # Second snapshot of network stats
    net_io_2 = psutil.net_io_counters()
    bytes_sent_2 = net_io_2.bytes_sent
    bytes_recv_2 = net_io_2.bytes_recv

    # Calculate the difference (bytes transferred in that second)
    bytes_sent_per_second = (bytes_sent_2 - bytes_sent_1) / (1024 ** 2)  # Convert to MB
    bytes_recv_per_second = (bytes_recv_2 - bytes_recv_1) / (1024 ** 2)  # Convert to MB

    # Total data transferred in that second (sent + received)
    total_data_per_second_mb = bytes_sent_per_second + bytes_recv_per_second

    return round(total_data_per_second_mb, 2)  # Return the result in MB


# Function to collect GPU performance for system performance calculation
def collect_gpu_performance(connection):
    gpu_utilization = 0
    try:
        for gpu in connection.Win32_VideoController():
            gpu_utilization = gpu.LoadPercentage if hasattr(gpu, 'LoadPercentage') else 0
    except Exception as e:
        print(f"Failed to retrieve GPU data: {e}")
    return gpu_utilization

# Function to compute system performance
def compute_system_performance(cpu_load, memory_in_use_mb, total_memory_mb, disk_usage, network_performance, gpu_utilization, battery_life_remaining):
    memory_usage = (memory_in_use_mb / total_memory_mb) * 100 if total_memory_mb > 0 else 0  # Convert memory usage to percentage
    max_possible_data_mb = 1000  # Normalize to 1000MB/sec, adjust as needed
    network_performance_percentage = (network_performance / max_possible_data_mb) * 100 if max_possible_data_mb > 0 else 0
    
    # Weights for each component
    w1, w2, w3, w4, w5, w6 = 0.20, 0.15, 0.10, 0.15, 0.10, 0.30
    
    performance_score = (
        (cpu_load / 100) * w1 +
        (memory_usage / 100) * w2 +
        (disk_usage / 100) * w3 +
        (network_performance_percentage / 100) * w4 +
        (gpu_utilization / 100) * w5 +
        (battery_life_remaining / 100) * w6
    ) * 100

    return round(performance_score, 2)

# Function to collect and store data from a single laptop
def collect_data(connection, ip_address, gmail_account):
    timestamp = time.strftime("%Y-%m-%d %H:%M:%S")

    # CPU Information
    cpu_load = None
    for cpu in connection.Win32_Processor():
        cpu_load = cpu.LoadPercentage

    # Memory In Use
    memory_in_use_mb = None
    total_memory_mb = None  # Define total_memory_mb here
    for os in connection.Win32_OperatingSystem():
        total_memory_mb = int(os.TotalVisibleMemorySize) / 1024  # Now you're defining total_memory_mb
        free_memory_mb = int(os.FreePhysicalMemory) / 1024
        memory_in_use_mb = total_memory_mb - free_memory_mb
    memory_in_use_mb = round(memory_in_use_mb, 2)

    # Disk/Storage Information (Free space for each disk)
    free_disk_space_gb = 0
    total_disk_space_gb = 0
    for disk in connection.Win32_LogicalDisk():
        if disk.FreeSpace:
            free_disk_space_gb += int(disk.FreeSpace) / (1024**3)
            total_disk_space_gb += int(disk.Size) / (1024**3)
    disk_usage = (total_disk_space_gb - free_disk_space_gb) / total_disk_space_gb * 100 if total_disk_space_gb else 0
    free_disk_space_gb = round(free_disk_space_gb, 2)

    # Battery Status (if available)
    battery_status = "Unknown"
    battery_life_remaining = None
    for battery in connection.Win32_Battery():
        battery_status = "Charging" if battery.BatteryStatus == 2 else "Discharging" if battery.BatteryStatus == 1 else "Unknown"
        battery_life_remaining = battery.EstimatedChargeRemaining

    # Network Performance
    network_performance = collect_network_performance()

    # GPU Performance (only used for system performance calculation, not stored/displayed)
    gpu_performance = collect_gpu_performance(connection)

    # Compute System Performance Score
    system_performance = compute_system_performance(cpu_load, memory_in_use_mb, total_memory_mb, disk_usage, network_performance, gpu_performance, battery_life_remaining)

    # Store data in the database (removed network_performance)
    cursor.execute('''
    INSERT INTO monitoring_data (timestamp, ip_address, cpu_load, memory_in_use_mb, free_disk_space_gb, battery_status, battery_life_remaining, system_performance_score)
    VALUES (?, ?, ?, ?, ?, ?, ?, ?)
    ''', (timestamp, ip_address, cpu_load, memory_in_use_mb, free_disk_space_gb, battery_status, battery_life_remaining, system_performance))
    conn.commit()

    # Display the collected data (removed network_performance)
    table = PrettyTable()
    table.field_names = ["Timestamp", "IP Address", "CPU Load (%)", "Memory In Use (MB)", "Free Disk Space (GB)", "Battery Status", "Battery Life Remaining (%)", "System Performance Score"]
    table.add_row([timestamp, ip_address, cpu_load, memory_in_use_mb, free_disk_space_gb, battery_status, battery_life_remaining, system_performance])
    print(table)

    # Send alert if CPU load is above 80%
    if cpu_load and cpu_load >= 80:
        send_email_alert(gmail_account, cpu_load, ip_address)


# Main program (same as your existing code)
if __name__ == "__main__":
    num_laptops = int(input("Enter the number of laptops to monitor: "))

    laptops = []
    for i in range(num_laptops):
        ip = input(f"Enter the IP address of laptop {i+1}: ")
        user = input(f"Enter the username for laptop {i+1}: ")
        password = input(f"Enter the password for laptop {i+1}: ")

        while True:
            gmail = input(f"Enter Gmail for laptop {i+1} (for alerts): ")
            if is_valid_email(gmail):
                break
            else:
                print("Invalid email format! Please enter a valid Gmail address.")
        
        laptops.append({"ip": ip, "user": user, "password": password, "gmail": gmail})

    for laptop in laptops:
        try:
            connection = wmi.WMI(computer=laptop["ip"], user=laptop["user"], password=laptop["password"])
            query_laptop(connection, laptop["ip"])
        except Exception as e:
            print(f"Failed to query {laptop['ip']}: {e}")
        
        print("\n" + "*"*50 + f" End of Query for {laptop['ip']} " + "*"*50 + "\n")

    try:
        while True:
            for laptop in laptops:
                try:
                    connection = wmi.WMI(computer=laptop["ip"], user=laptop["user"], password=laptop["password"])
                    collect_data(connection, laptop["ip"], laptop["gmail"])
                except Exception as e:
                    print(f"Failed to collect data from {laptop['ip']}: {e}")
            time.sleep(1)  # Monitor every 1 second
    except KeyboardInterrupt:
        print("Monitoring stopped.")
        conn.close()  
