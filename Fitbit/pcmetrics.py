import psutil
import time
from datetime import timedelta
import subprocess

def get_active_screen_time():
    """ Get the system uptime as a proxy for active screen time """
    uptime_seconds = time.time() - psutil.boot_time()
    uptime_str = str(timedelta(seconds=int(uptime_seconds)))  # Convert seconds to HH:MM:SS format
    return uptime_str

def get_cpu_load():
    """ Get the current CPU usage percentage """
    return psutil.cpu_percent(interval=1)  # 1-second interval for real-time usage

def get_open_tabs_mac():
    script = '''
    tell application "Google Chrome"
        set tab_count to 0
        repeat with w in windows
            set tab_count to tab_count + (count of tabs in w)
        end repeat
        return tab_count
    end tell
    '''
    try:
        result = subprocess.run(["osascript", "-e", script], capture_output=True, text=True)
        return int(result.stdout.strip()) if result.stdout.strip().isdigit() else 0
    except Exception as e:
        print(f"Error: {e}")
        return 0

tabs_open = get_open_tabs_mac()
print(f"Google Chrome Tabs Open: {tabs_open}")


def get_safari_tabs():
    script = '''
    tell application "Safari"
        set tab_count to 0
        repeat with w in windows
            set tab_count to tab_count + (count of tabs in w)
        end repeat
        return tab_count
    end tell
    '''
    try:
        result = subprocess.run(["osascript", "-e", script], capture_output=True, text=True)
        return int(result.stdout.strip()) if result.stdout.strip().isdigit() else 0
    except Exception as e:
        print(f"Error: {e}")
        return 0

tabs_safari = get_safari_tabs()
print(f"Safari Tabs Open: {tabs_safari}")

def get_pc_metrics():
    """ Collect and return PC metrics """
    chrome_tabs = get_open_tabs_mac()
    safari_tabs = get_safari_tabs()
    total_tabs = chrome_tabs + safari_tabs

    return {
        "active_screen_time": get_active_screen_time(),
        "cpu_load": get_cpu_load(),
        "total_tabs": total_tabs
    }
