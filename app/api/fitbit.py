import requests
import base64
from config.settings import Config
from app.errors.handlers import AuthenticationError, DataFetchError
from app.models.user import FitbitUser
from datetime import datetime, timedelta
import psutil
import math

class FitbitAPI:
    @staticmethod
    def get_auth_link():
        """Generate the authorization link for Fitbit login"""
        return (
            f"{Config.AUTH_URL}?response_type=code&client_id={Config.CLIENT_ID}"
            f"&redirect_uri={Config.REDIRECT_URI}&scope=activity%20heartrate%20sleep%20profile&expires_in=31536000"
        )

    @staticmethod
    def get_access_token(auth_code):
        """Exchange authorization code for access token"""
        if '#_=_ ' in auth_code:
            auth_code = auth_code.split('#')[0]
        
        data = {
            "client_id": Config.CLIENT_ID,
            "client_secret": Config.CLIENT_SECRET,
            "code": auth_code,
            "grant_type": "authorization_code",
            "redirect_uri": Config.REDIRECT_URI,
        }
        headers = {"Content-Type": "application/x-www-form-urlencoded"}
        
        # Create the Authorization header
        auth_string = f"{Config.CLIENT_ID}:{Config.CLIENT_SECRET}"
        auth_base64 = base64.b64encode(auth_string.encode()).decode("utf-8")
        headers["Authorization"] = f"Basic {auth_base64}"

        try:
            token_response = requests.post(Config.TOKEN_URL, data=data, headers=headers)
            token_data = token_response.json()
            if "access_token" not in token_data:
                raise AuthenticationError("Failed to get access token")
            return token_data
        except requests.exceptions.RequestException as e:
            raise AuthenticationError(f"Token request failed: {str(e)}")

    @staticmethod
    def get_user_data(access_token):
        """Fetch all user data from Fitbit API, with proper error handling"""
        headers = {"Authorization": f"Bearer {access_token}"}

        # Initialize empty data dictionary
        user_data = {}

        try:
            print(f"🌍 Fetching Fitbit user profile...")
            profile_response = requests.get(Config.DISPLAY_NAME_URL, headers=headers)
            print(f"🔍 Profile Response Code: {profile_response.status_code}")
            print(f"🔍 Profile Response Body: {profile_response.text}")

            if profile_response.status_code != 200:
                print("🚨 Failed to fetch user profile!")
                return None  # Return None if profile request fails

            user_data["profile"] = profile_response.json()

        except requests.exceptions.RequestException as e:
            print(f"🚨 Profile request failed: {e}")
            return None

        # Heart Rate Data
        try:
            print(f"🌍 Fetching Fitbit heart rate data...")
            heart_rate_response = requests.get(Config.HEART_RATE_URL, headers=headers)
            print(f"🔍 Heart Rate Response Code: {heart_rate_response.status_code}")
            print(f"🔍 Heart Rate Response Body: {heart_rate_response.text}")

            if heart_rate_response.status_code != 200:
                print("⚠️ Warning: Heart rate data unavailable.")
                user_data["heart_rate"] = None  # Store None instead of failing
            else:
                user_data["heart_rate"] = heart_rate_response.json()

        except requests.exceptions.RequestException as e:
            print(f"⚠️ Heart rate request failed: {e}")
            user_data["heart_rate"] = None  # Store None and continue

        # Real-Time Heart Rate Data
        try:
            print(f"🌍 Fetching Fitbit real-time heart rate data...")
            real_time_response = requests.get(Config.REAL_TIME_HEART_RATE_URL, headers=headers)
            print(f"🔍 Real-Time HR Response Code: {real_time_response.status_code}")
            print(f"🔍 Real-Time HR Response Body: {real_time_response.text}")

            if real_time_response.status_code != 200:
                print("⚠️ Warning: Real-time heart rate data unavailable.")
                user_data["real_time_heart_rate"] = None
            else:
                user_data["real_time_heart_rate"] = real_time_response.json()

        except requests.exceptions.RequestException as e:
            print(f"⚠️ Real-time heart rate request failed: {e}")
            user_data["real_time_heart_rate"] = None

        # Steps Data
        try:
            print(f"🌍 Fetching Fitbit steps data...")
            steps_response = requests.get(Config.STEPS_URL, headers=headers)
            print(f"🔍 Steps Response Code: {steps_response.status_code}")
            print(f"🔍 Steps Response Body: {steps_response.text}")

            if steps_response.status_code != 200:
                print("⚠️ Warning: Steps data unavailable.")
                user_data["steps"] = None
            else:
                user_data["steps"] = steps_response.json()

        except requests.exceptions.RequestException as e:
            print(f"⚠️ Steps request failed: {e}")
            user_data["steps"] = None

        print(f"✅ Final Fitbit Data: {user_data}")  # Debugging output

        return FitbitUser(user_data) if user_data else None
    
    @staticmethod
    def get_devices(access_token):
        """Get the list of devices for the user"""
        headers = {"Authorization": f"Bearer {access_token}"}
        devices_url = "https://api.fitbit.com/1/user/-/devices.json"
        
        try:
            response = requests.get(devices_url, headers=headers)
            response.raise_for_status()
            return response.json()  # Returns a list of devices
        except requests.exceptions.RequestException as e:
            raise DataFetchError(f"Failed to fetch devices: {str(e)}")

    @staticmethod
    def set_alarm(access_token, tracker_id, label="Get up and move"):
        """Set an alarm on the specified Fitbit device"""
        headers = {
            "Authorization": f"Bearer {access_token}",
            "Content-Type": "application/json"
        }
        
        # Set the alarm time to 1 minute from now for testing
        alarm_time = (datetime.now() + timedelta(minutes=1)).strftime("%H:%M") + "-00:00"
        
        # Alarm data
        alarm_data = {
            "time": alarm_time,  # Set to 1 minute from now
            "enabled": True,
            "recurring": True,  # Set to repeat daily
            "weekDays": "MONDAY,TUESDAY,WEDNESDAY,THURSDAY,FRIDAY"  # Adjust as needed
        }
        
        alarms_url = f"https://api.fitbit.com/1/user/-/devices/tracker/{tracker_id}/alarms.json"
        
        try:
            response = requests.post(alarms_url, headers=headers, json=alarm_data)
            response.raise_for_status()
            print(f"Successfully set alarm: {response.json()}")
            return True  # Indicate that the alarm was set successfully
        except requests.exceptions.RequestException as e:
            print(f"Failed to set alarm: {str(e)}")
            return False  # Indicate failure


    def check_inactivity(self, current_steps, access_token):
        """Check if user has been inactive while using the computer"""
        current_time = datetime.now()
        
        self.log_debug(f"Checking inactivity - Current steps: {current_steps}, Last steps: {self.last_step_count}")
        
        if current_steps is not None and self.last_step_count is not None and current_steps > self.last_step_count:
            self.log_debug(f"Steps increased from {self.last_step_count} to {current_steps}")
            self.last_step_count = current_steps
            self.last_step_time = current_time
            return False
                
        # Check if computer is being actively used
        if not self.is_computer_active():
            self.log_debug("Computer is not actively being used")
            return False  # No alarm set, no reminder needed
        
        # Calculate time since last step
        minutes_inactive = (current_time - self.last_step_time).total_seconds() / 60
        self.log_debug(f"Minutes since last step: {minutes_inactive:.1f}")
        
        # Check if we should set an alarm
        if minutes_inactive >= self.inactivity_threshold:
            self.log_debug(f"Setting alarm - Inactive for {minutes_inactive:.1f} minutes while using computer")
            
            # Get the tracker ID
            devices = FitbitAPI.get_devices(access_token)
            if devices:
                tracker_id = devices[0]['id']  # Assuming the first device is the one we want
                self.log_debug(f"Using tracker ID: {tracker_id}")
                alarm_set = FitbitAPI.set_alarm(access_token, tracker_id)  # Set the alarm
                if alarm_set:
                    self.log_debug("Alarm set successfully, show reminder card.")
                    return True  # Indicate that the reminder card should be shown
                else:
                    self.log_debug("Failed to set alarm.")
            else:
                self.log_debug("No devices found for the user.")
        
        return False  # No alarm set, no reminder needed


    def is_computer_active(self):
        """Check if computer is being actively used based on CPU and process activity"""
        try:
            # Get CPU usage
            cpu_percent = psutil.cpu_percent(interval=2)
            
            # If cpu_percent is None or less than 0, log and return False
            if cpu_percent is None or cpu_percent < 0:
                self.log_debug(f"Invalid CPU percent: {cpu_percent}, assuming inactive.")
                return False

            # Get active window processes
            active_processes = []
            for proc in psutil.process_iter(['name', 'cpu_percent']):
                try:
                    # Filter for common active usage processes
                    proc_name = proc.info['name'].lower()
                    cpu_usage = proc.info['cpu_percent']
                    
                    # Check if cpu_usage is a valid number (float) and greater than 1.0
                    if isinstance(cpu_usage, (float, int)) and cpu_usage > 1.0 and any(x in proc_name for x in ['chrome', 'firefox', 'safari', 'edge', 'code', 'word', 'excel']):
                        active_processes.append(proc_name)
                except (psutil.NoSuchProcess, psutil.AccessDenied):
                    continue  # Skip processes that are no longer available

            # Check if CPU usage is high or if there are active processes
            is_active = cpu_percent > 10 or len(active_processes) > 0
            self.log_debug(f"Computer activity check - CPU: {cpu_percent}%, Active processes: {', '.join(active_processes)}")
            return is_active

        except Exception as e:
            self.log_debug(f"Error checking computer activity: {e}")
            return False