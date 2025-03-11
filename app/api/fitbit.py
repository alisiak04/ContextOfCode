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
            

            if steps_response.status_code != 200:
                print("⚠️ Warning: Steps data unavailable.")
                user_data["steps"] = None
            else:
                response_json = steps_response.json()
                

                user_data["steps"] = response_json 
                    

        except requests.exceptions.RequestException as e:
            print(f"⚠️ Steps request failed: {e}")
            user_data["steps"] = None

        

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
