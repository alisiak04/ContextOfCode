import psutil
from datetime import datetime

def get_pc_metrics():
    """
    Returns actual PC metrics using psutil
    """
    try:
        print("\n=== PC Metrics Debug ===")
        
        # CPU Usage (average over 1 second)
        cpu_usage = psutil.cpu_percent(interval=1)
        print(f"CPU Usage: {cpu_usage}%")
        
        # Memory Usage
        memory = psutil.virtual_memory()
        memory_usage = memory.percent
        print(f"Memory Usage: {memory_usage}%")
        
        # Disk Usage
        disk = psutil.disk_usage('/')
        disk_usage = disk.percent
        print(f"Disk Usage: {disk_usage}%")
        
        # Process count
        process_count = len(list(psutil.process_iter()))
        print(f"Process Count: {process_count}")
        
        # System uptime
        boot_time = datetime.fromtimestamp(psutil.boot_time())
        uptime_hours = round((datetime.now() - boot_time).total_seconds() / 3600, 1)

        return {
            'cpu_usage': f"{cpu_usage:.1f}%",
            'memory_usage': f"{memory_usage:.1f}%",
            'disk_usage': f"{disk_usage:.1f}%",
            'process_count': process_count,
            'uptime_hours': f"{uptime_hours:.1f}"
        }
    except Exception as e:
        print(f"\nError getting PC metrics: {str(e)}")
        # Return default values if there's an error
        return {
            'cpu_usage': 'N/A',
            'memory_usage': 'N/A',
            'disk_usage': 'N/A',
            'process_count': 'N/A',
            'uptime_hours': 'N/A'
        } 