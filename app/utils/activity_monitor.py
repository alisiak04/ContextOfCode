import time
from datetime import datetime, timedelta
import psutil
from app.api.fitbit import FitbitAPI

class ActivityMonitor:
    def __init__(self):
        self.last_step_count = 0
        self.last_step_time = datetime.now() - timedelta(minutes=4)  # Start with 4 minutes of inactivity
        self.last_notification_time = None
        self.inactivity_threshold = 5  # minutes (5 minutes)
        self.notification_cooldown = 10  # minutes (10 minutes)
        self.debug_log = []  # Store debug messages
        self.max_log_entries = 100
        print("ActivityMonitor initialized with 4 minutes of initial inactivity")
        
    def log_debug(self, message):
        """Add timestamped debug message to log"""
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        log_entry = f"{timestamp}: {message}"
        print(log_entry)  # Print to console
        self.debug_log.append(log_entry)
        # Keep only the last N entries
        if len(self.debug_log) > self.max_log_entries:
            self.debug_log = self.debug_log[-self.max_log_entries:]
        
    def is_computer_active(self):
        """Check if computer is being actively used based on CPU and process activity"""
        try:
            # Get CPU usage
            cpu_percent = psutil.cpu_percent(interval=1)
            
            # Get active window processes
            active_processes = []
            for proc in psutil.process_iter(['name', 'cpu_percent']):
                try:
                    # Filter for common active usage processes
                    proc_name = proc.info['name'].lower()
                    if (proc.info['cpu_percent'] > 1.0 and 
                        any(x in proc_name for x in ['chrome', 'firefox', 'safari', 'edge', 'code', 'word', 'excel'])):
                        active_processes.append(proc_name)
                except (psutil.NoSuchProcess, psutil.AccessDenied):
                    pass
            
            is_active = cpu_percent > 10 or len(active_processes) > 0
            self.log_debug(f"Computer activity check - CPU: {cpu_percent}%, Active processes: {', '.join(active_processes)}")
            return is_active
            
        except Exception as e:
            self.log_debug(f"Error checking computer activity: {e}")
            return False

    def check_inactivity(self, current_steps, access_token):
        """Check if user has been inactive while using the computer"""
        current_time = datetime.now()
        
        self.log_debug(f"Checking inactivity - Current steps: {current_steps}, Last steps: {self.last_step_count}")
        
        # If steps have increased, update last step time
        if current_steps > self.last_step_count:
            self.log_debug(f"Steps increased from {self.last_step_count} to {current_steps}")
            self.last_step_count = current_steps
            self.last_step_time = current_time
            return
        
        # Check if computer is being actively used
        if not self.is_computer_active():
            self.log_debug("Computer is not actively being used")
            return
        
        # Calculate time since last step
        minutes_inactive = (current_time - self.last_step_time).total_seconds() / 60
        self.log_debug(f"Minutes since last step: {minutes_inactive:.1f}")
        
        # Check if we should send a notification
        if minutes_inactive >= self.inactivity_threshold:
            # Check if enough time has passed since last notification
            if (self.last_notification_time is None or 
                (current_time - self.last_notification_time).total_seconds() / 60 >= self.notification_cooldown):
                self.log_debug(f"Sending movement reminder - Inactive for {minutes_inactive:.1f} minutes while using computer")
                FitbitAPI.send_notification(access_token, minutes_inactive)  # Pass the inactive time
                self.last_notification_time = current_time
            else:
                time_since_last = (current_time - self.last_notification_time).total_seconds() / 60
                self.log_debug(f"Skipping notification - Only {time_since_last:.1f} minutes since last notification")
                
    def get_status(self):
        """Get current monitoring status"""
        current_time = datetime.now()
        status = {
            'last_step_count': self.last_step_count,
            'minutes_since_last_step': (current_time - self.last_step_time).total_seconds() / 60,
            'computer_active': self.is_computer_active(),
            'last_notification': None if self.last_notification_time is None else self.last_notification_time.strftime("%Y-%m-%d %H:%M:%S"),
            'minutes_since_last_notification': None if self.last_notification_time is None else 
                (current_time - self.last_notification_time).total_seconds() / 60,
            'recent_logs': self.debug_log[-10:]  # Get last 10 log entries
        }
        return status 