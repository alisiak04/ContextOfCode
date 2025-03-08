import psutil
import time
from datetime import datetime, timedelta

def get_active_screen_time():
    """ Get the system uptime as a proxy for active screen time """
    uptime_seconds = time.time() - psutil.boot_time()
    uptime_str = str(timedelta(seconds=int(uptime_seconds)))  # Convert seconds to HH:MM:SS format
    return uptime_str

def get_cpu_load():
    """ Get the current CPU usage percentage """
    return psutil.cpu_percent(interval=1)  # 1-second interval for real-time usage

def get_pc_metrics():
    """ Collect and return PC metrics """
    return {
        "active_screen_time": get_active_screen_time(),
        "cpu_load": get_cpu_load()
    }