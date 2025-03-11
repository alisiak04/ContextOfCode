import time
import threading
from app.api.fitbit import FitbitAPI
from app.utils.pcmetrics import get_pc_metrics
from app.utils.fitbitmetrics import display_steps_data
from app.utils.activity_monitor import ActivityMonitor
import traceback
from Database.databaseHandle import (insert_user, insert_real_time_heart_rate, 
                                    insert_resting_heart_rate, insert_pc_metrics,
                                    insert_steps_screen)

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

                if steps_list and steps_list[0]:
                    current_steps = steps_list[0].get("value", 0)
                    self.activity_monitor.check_inactivity(current_steps, self.access_token)

                # Get PC metrics
                pc_metrics = get_pc_metrics()

                # Extract display name (Ensure it exists)
                display_name = "Unknown User"
                if isinstance(fitbit_user.profile, dict) and "user" in fitbit_user.profile:
                    user_profile = fitbit_user.profile["user"]
                    display_name = user_profile.get("displayName", "Unknown User")
                    full_name = user_profile.get("fullName", "Unknown User")
                else:
                    full_name = "Unknown User"

                print(f"✅ Extracted Display Name: {display_name}, Full Name: {full_name}")

                # Insert or get user ID
                user_id = insert_user(display_name)
                print(f"✅ Inserted User ID: {user_id} for Display Name: {display_name}")

                if user_id is not None:
                    # Insert heart rate data
                    if fitbit_user.real_time_heart_rate_data:
                        insert_real_time_heart_rate(user_id, fitbit_user.real_time_heart_rate_data)

                    # Insert resting heart rate
                    if fitbit_user.resting_heart_rate:
                        insert_resting_heart_rate(user_id, fitbit_user.resting_heart_rate)

                    # Insert PC metrics
                    if pc_metrics:
                        insert_pc_metrics(user_id, 
                                          pc_metrics.get("cpu_usage", 0), 
                                          pc_metrics.get("open_tabs", 0))

                    # Insert steps and screen time data
                    screen_time_minutes = pc_metrics.get("screen_time_minutes", 0)  # Adjust as needed
                    insert_steps_screen(user_id, current_steps, screen_time_minutes)

                # Update shared data
                with self.shared_data.lock:
                    self.shared_data.update({
                        "display_name": display_name,  # ✅ Store only the display name
                        "resting_heart_rate": fitbit_user.resting_heart_rate,
                        "heart_rate_zones": fitbit_user.heart_rate_zones,
                        "real_time_data": fitbit_user.real_time_heart_rate_data,
                        "steps_data": steps_list,
                        "pc_metrics": pc_metrics,
                    })

                # Push update to frontend via WebSockets
                self.socketio.emit("update_metrics", self.shared_data.data)
                print(f"✅ Pushed new data to frontend: {self.shared_data.data}")

            except Exception as e:
                print(f"❌ Error in fetching data: {e}")
                traceback.print_exc()

            time.sleep(300)  # Fetch data every 5 minutes

    def start(self):
        """Start scheduler in a separate thread."""
        self.thread = threading.Thread(target=self.fetch_data, daemon=True)
        self.thread.start()