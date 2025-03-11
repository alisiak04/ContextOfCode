import time
import threading
import traceback
from app.api.fitbit import FitbitAPI
from app.utils.pcmetrics import get_pc_metrics
from app.utils.fitbitmetrics import display_steps_data
from app.utils.activity_monitor import ActivityMonitor
from Database.databaseHandle import (
    insert_user, insert_real_time_heart_rate, 
    insert_resting_heart_rate, insert_pc_metrics,
    insert_steps
)
from task_queue import TaskQueue
from threading import Lock

# Shared data structure with a lock for thread safety
shared_data = {"data": {}, "lock": Lock()}

class TaskScheduler:
    def __init__(self, access_token, socketio):
        self.access_token = access_token
        self.activity_monitor = ActivityMonitor()
        self.shared_data = shared_data
        self.socketio = socketio
        self.task_queue = TaskQueue(socketio)
        self.running = True
        
    def fetch_data(self):
        """Fetch Fitbit and PC metrics, then push updates via WebSockets"""
        try:
            print("🔄 Fetching new data...")
            fitbit_user = FitbitAPI.get_user_data(self.access_token)
            
            steps_list = display_steps_data(fitbit_user.steps)
            current_steps = sum(entry["steps"] for entry in steps_list) if steps_list else 0
            self.activity_monitor.check_inactivity(current_steps, self.access_token)

            pc_metrics = get_pc_metrics()
            display_name = fitbit_user.profile.get("user", {}).get("displayName", "Unknown User")
            user_id = insert_user(display_name)

            if user_id:
                if fitbit_user.real_time_heart_rate_data:
                    insert_real_time_heart_rate(user_id, fitbit_user.real_time_heart_rate_data)
                if fitbit_user.resting_heart_rate:
                    insert_resting_heart_rate(user_id, fitbit_user.resting_heart_rate)
                if pc_metrics:
                    insert_pc_metrics(
                        user_id,
                        float(pc_metrics["cpu_usage"].replace("%", "")),
                        float(pc_metrics["memory_usage"].replace("%", "")),
                        float(pc_metrics["disk_usage"].replace("%", "")),
                        int(pc_metrics["process_count"])
                    )
                insert_steps(user_id, steps_list)

            real_time_hr = fitbit_user.real_time_heart_rate_data
            latest_hr = real_time_hr[-1] if real_time_hr else {"time": "N/A", "value": "No Data"}

            data_to_store = {
                "display_name": display_name,
                "resting_heart_rate": fitbit_user.resting_heart_rate,
                "heart_rate_zones": fitbit_user.heart_rate_zones,
                "real_time_data": real_time_hr,
                "latest_heart_rate": latest_hr,
                "steps_data": steps_list,
                "pc_metrics": pc_metrics,
            }

            with shared_data["lock"]:
                shared_data["data"].update(data_to_store)

            self.socketio.emit("update_metrics", data_to_store)
            self.socketio.emit("update_heart_rate", {"latest_hr": latest_hr})

        except Exception as e:
            print(f"❌ Error in fetching data: {e}")
            traceback.print_exc()

    def start(self):
        """Start scheduler in a separate thread and add to queue."""
        self.thread = threading.Thread(target=self.fetch_data, daemon=True)
        self.thread.start()
        self.task_queue.add_task("fetch_data", self.fetch_data, interval_seconds=300, priority=1)
        self.task_queue.add_task("fetch_resting_heart_rate", self.fetch_resting_heart_rate, interval_seconds=86400, priority=2)

    def fetch_resting_heart_rate(self):
        """Fetch and store resting heart rate."""
        try:
            print("🔄 Fetching resting heart rate...")
            fitbit_user = FitbitAPI.get_user_data(self.access_token)
            if fitbit_user.resting_heart_rate:
                user_id = insert_user(fitbit_user.profile.get("user", {}).get("displayName", "Unknown User"))
                insert_resting_heart_rate(user_id, fitbit_user.resting_heart_rate)
        except Exception as e:
            print(f"❌ Error fetching resting heart rate: {e}")
            traceback.print_exc()
