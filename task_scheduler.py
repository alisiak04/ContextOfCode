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

class TaskScheduler:
    def __init__(self, access_token, shared_data, socketio):
        self.access_token = access_token
        self.activity_monitor = ActivityMonitor()
        self.shared_data = shared_data  # Store fetched data
        self.socketio = socketio  # WebSocket reference
        self.running = True

    def fetch_data(self):
        """Fetch Fitbit and PC metrics, then push updates via WebSockets"""
        while self.running:
            try:
                print("🔄 Fetching new data...")

                # Get Fitbit user data
                fitbit_user = FitbitAPI.get_user_data(self.access_token)
                steps_list = display_steps_data(fitbit_user.steps)

                if steps_list:
                    current_steps = sum(entry["steps"] for entry in steps_list)  # Sum steps for today
                    self.activity_monitor.check_inactivity(current_steps, self.access_token)

                # Get PC metrics
                pc_metrics = get_pc_metrics()

                # Extract display name (Ensure it exists)
                display_name = "Unknown User"
                if isinstance(fitbit_user.profile, dict) and "user" in fitbit_user.profile:
                    user_profile = fitbit_user.profile["user"]
                    display_name = user_profile.get("displayName", "Unknown User")

                # Insert or get user ID
                user_id = insert_user(display_name)
                
                if user_id is not None:
                    # Insert heart rate data
                    if fitbit_user.real_time_heart_rate_data:
                        insert_real_time_heart_rate(user_id, fitbit_user.real_time_heart_rate_data)

                    # Insert resting heart rate
                    if fitbit_user.resting_heart_rate:
                        insert_resting_heart_rate(user_id, fitbit_user.resting_heart_rate)

                    # Insert PC metrics
                    if pc_metrics:
                        insert_pc_metrics(
                            user_id, 
                            float(pc_metrics["cpu_usage"].replace("%", "")),  
                            float(pc_metrics["memory_usage"].replace("%", "")),  
                            float(pc_metrics["disk_usage"].replace("%", "")),  
                            int(pc_metrics["process_count"])
                        )

                    # Insert step data
                    insert_steps(user_id, steps_list)

                # Update shared data
                data_to_store = {
                    "display_name": display_name,
                    "resting_heart_rate": fitbit_user.resting_heart_rate,
                    "heart_rate_zones": fitbit_user.heart_rate_zones,
                    "real_time_data": fitbit_user.real_time_heart_rate_data,
                    "steps_data": steps_list,
                    "pc_metrics": pc_metrics,
                }
                
                with self.shared_data:
                    # Use the shared instance's update method
                    self.shared_data.update(data_to_store)

                # Push update to frontend via WebSockets
                self.socketio.emit("update_metrics", data_to_store)
                print(f"✅ Pushed new data to frontend")

            except Exception as e:
                print(f"❌ Error in fetching data: {e}")
                traceback.print_exc()

            time.sleep(300)  # Fetch data every 5 minutes

    def start(self):
        """Start scheduler in a separate thread."""
        self.thread = threading.Thread(target=self.fetch_data, daemon=True)
        self.thread.start()