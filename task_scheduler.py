import time
import threading
import traceback
from app.api.fitbit import FitbitAPI
from app.utils.pcmetrics import get_pc_metrics
from flask_socketio import SocketIO
from threading import Lock
import json

class TaskScheduler:
    def __init__(self, access_token, socketio: SocketIO):
        self.access_token = access_token
        self.socketio = socketio
        self.running = True
        self.shared_data = {"data": {}, "lock": Lock()}  # Store latest data with a lock

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


            # ✅ Extract steps in last 15 minutes
            last_15_min_steps = 0
            intraday_steps = fitbit_user.steps.get("activities-steps-intraday", {}).get("dataset", [])
            if intraday_steps:
                last_15_min_steps = intraday_steps[-1]["value"]  # Last recorded interval
                
            
           

            # Store data
            new_data = {
                "display_name": fitbit_user.profile.get("user", {}).get("displayName", "Unknown User"),
                "resting_heart_rate": fitbit_user.resting_heart_rate,
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
           

        except Exception as e:
            print(f"❌ Error fetching data: {e}")
            traceback.print_exc()

    def start(self):
        """Fetch data once, then refresh every 5 minutes."""
        self.fetch_data()  # Fetch immediately
        
        def loop():
            while self.running:
                time.sleep(300)  # Wait 5 minutes
                self.fetch_data()  # Refresh data
        
        threading.Thread(target=loop, daemon=True).start()
