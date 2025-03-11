import time
import threading
import traceback
from app.api.fitbit import FitbitAPI
from app.utils.pcmetrics import get_pc_metrics
from flask_socketio import SocketIO
from threading import Lock
import json
from Database.databaseHandle import (
    insert_user,
    insert_pc_metrics,
    insert_steps,
    insert_real_time_heart_rate,
    insert_resting_heart_rate,
)

class TaskScheduler:
    def __init__(self, access_token, socketio: SocketIO):
        self.access_token = access_token
        self.socketio = socketio
        self.running = True
        self.shared_data = {"data": {}, "lock": Lock()}  # Store latest data with a lock
        self.latest_data = {}  

    def fetch_data(self):
        """Fetch Fitbit and PC metrics, update cache, and send WebSocket updates."""
        try:
            print("🔄 Fetching new data...")
            
            # Get Fitbit & PC metrics
            fitbit_user = FitbitAPI.get_user_data(self.access_token)
            steps_data = fitbit_user.steps.get("activities-steps-intraday", {}).get("dataset", []) if fitbit_user.steps else []
            latest_steps = steps_data[-1]["value"] if steps_data else "N/A"


            pc_metrics = get_pc_metrics()

            # Extract latest heart rate
            latest_hr = fitbit_user.real_time_heart_rate_data[-1] if fitbit_user.real_time_heart_rate_data else "No Data"
            heart_rate_history = fitbit_user.real_time_heart_rate_data or []
            display_name = fitbit_user.profile.get("user", {}).get("displayName", "Unknown User")
            resting_heart_rate =fitbit_user.resting_heart_rate

            # ✅ Extract steps in last 15 minutes
            last_15_min_steps = 0
            intraday_steps = fitbit_user.steps.get("activities-steps-intraday", {}).get("dataset", [])
            if intraday_steps:
                last_15_min_steps = intraday_steps[-1]["value"]  # Last recorded interval
                
            # ✅ Store fetched data in a variable for later use
            self.latest_data = {
                "display_name": display_name,
                "steps_data": steps_data,
                "heart_rate_history": heart_rate_history,
                "resting_heart_rate": resting_heart_rate,
                "pc_metrics": pc_metrics,
            }

           

            # Store data
            new_data = {
                "display_name": display_name,
                "resting_heart_rate": resting_heart_rate,
                "latest_heart_rate": latest_hr,
                "heart_rate_history": heart_rate_history, 
                "latest_steps": latest_steps,
                "last_15_min_steps": last_15_min_steps,
                "pc_metrics": pc_metrics,
            }

            # Update shared data
            with self.shared_data["lock"]:
                self.shared_data["data"] = new_data
           

            # Send data update via WebSockets
            self.socketio.emit("update_metrics", new_data)
            self.process_and_save_data()

        except Exception as e:
            print(f"❌ Error fetching data: {e}")
            traceback.print_exc()


    def process_and_save_data(self):
        """Process fetched data and save it to the database."""
        try:
            if not self.latest_data:
                print("⚠️ No data to save.")
                return

            display_name = self.latest_data["display_name"]
            steps_data = self.latest_data["steps_data"]
            heart_rate_history = self.latest_data["heart_rate_history"]
            resting_heart_rate = self.latest_data["resting_heart_rate"]
            pc_metrics = self.latest_data["pc_metrics"]

            # ✅ Get user ID (insert if new user)
            user_id = insert_user(display_name)

            # ✅ Process PC metrics
            cpu = float(pc_metrics["cpu_usage"].replace("%", ""))
            mem = float(pc_metrics["memory_usage"].replace("%", ""))
            disk = float(pc_metrics["disk_usage"].replace("%", ""))
            proc = int(pc_metrics["process_count"])
            formatted_steps = []
            for entry in formatted_steps:
                if isinstance(entry, dict) and "time" in entry and "value" in entry:
                    formatted_steps.append({"timestamp": entry["time"], "steps": entry["value"]})
                else:
                    print(f"⚠️ Skipping malformed entry: {entry}")
                        # ✅ Save data to database
            insert_pc_metrics(user_id, cpu, mem, disk, proc)
            insert_steps(user_id, formatted_steps)
            insert_real_time_heart_rate(user_id, heart_rate_history)
            insert_resting_heart_rate(user_id, resting_heart_rate)

            print(f"✅ Data successfully saved to the database for user {display_name}.")

        except Exception as e:
            print(f"❌ Error saving data to database: {e}")
            traceback.print_exc()


    def start(self):
        """Fetch data once, then refresh every 5 minutes."""
        self.fetch_data()  # Fetch immediately
        
        def loop():
            while self.running:
                time.sleep(300)  # Wait 5 minutes
                self.fetch_data()  # Refresh data
        
        threading.Thread(target=loop, daemon=True).start()
