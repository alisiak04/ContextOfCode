import requests
from flask import Flask, request, redirect, render_template
import base64
from pcmetrics import get_pc_metrics
from fitbitmetrics import display_steps_data

# 🔹 Fitbit App credentials
CLIENT_ID = "23Q3T7"
CLIENT_SECRET = "eee401b70553617de75989d262207feb"
REDIRECT_URI = "http://localhost:5001/callback"  # Flask will handle this


# 🔹 Fitbit API URLs
AUTH_URL = "https://www.fitbit.com/oauth2/authorize"
TOKEN_URL = "https://api.fitbit.com/oauth2/token"
HEART_RATE_URL = "https://api.fitbit.com/1/user/-/activities/heart/date/today/1d.json"  
STEPS_URL = "https://api.fitbit.com/1/user/-/activities/steps/date/today/1d/15min.json"  
REAL_TIME_HEART_RATE_URL = "https://api.fitbit.com/1/user/-/activities/heart/date/today/1d/1min.json"  
DISPLAY_NAME_URL = "https://api.fitbit.com/1/user/-/profile.json"


app = Flask(__name__)

@app.route("/")
def home():
    """ Step 1: Redirect user to Fitbit login """
    print("Home route accessed") 
    auth_link = (
        f"{AUTH_URL}?response_type=code&client_id={CLIENT_ID}"
        f"&redirect_uri={REDIRECT_URI}&scope=activity%20heartrate%20sleep%20profile&expires_in=31536000" 
        # 31536000 is 1 year in seconds
    )
    return redirect(auth_link)

@app.route("/callback")
def callback():
    print("Callback route accessed") 
    """ Step 2: Exchange authorization code for an access token """
    auth_code = request.args.get("code")
    print("Authorization code received:", auth_code, flush=True) 
    if not auth_code:
        return "Error: No authorization code received!"
    
     # Handle #_=_ at the end of the URL
    if '#_=_ ' in auth_code:
        auth_code = auth_code.split('#')[0]
    
    print("Authorization code received:", auth_code , flush=True) 

    # Request an access token
    data = {
        "client_id": CLIENT_ID,
        "client_secret": CLIENT_SECRET,
        "code": auth_code,
        "grant_type": "authorization_code",
        "redirect_uri": REDIRECT_URI,
    }
    headers = {"Content-Type": "application/x-www-form-urlencoded"}
    
    # Create the Authorisation header
    auth_string = f"{CLIENT_ID}:{CLIENT_SECRET}"
    auth_base64 = base64.b64encode(auth_string.encode()).decode("utf-8")
    headers["Authorization"] = f"Basic {auth_base64}"

    token_response = requests.post(TOKEN_URL, data=data, headers=headers)
    token_json = token_response.json()

    print("Token Response JSON:", token_json)

    if "access_token" not in token_json:
        return f"Error getting access token: {token_json}"

    access_token = token_json["access_token"]

    print("Access token received:", access_token) 

    # Fetch Fitbit metrics (Heart Rate Data)
    headers = {"Authorization": f"Bearer {access_token}"}

    profile_response = requests.get(DISPLAY_NAME_URL, headers=headers)
    profile_data = profile_response.json()
    
    if "user" not in profile_data or "displayName" not in profile_data["user"]:
        return "Error: Unable to fetch user profile data"
    
    display_name = profile_data["user"]["displayName"] 
    #i still have to use the name somewhere 

    fitbit_response = requests.get(HEART_RATE_URL, headers=headers)
    fitbit_data = fitbit_response.json()

    if 'activities-heart' not in fitbit_data:
        return f"Error fetching heart rate data: {fitbit_data}"
    
    # Fetch Real-Time Heart Rate Data
    real_time_response = requests.get(REAL_TIME_HEART_RATE_URL, headers=headers)
    real_time_data = real_time_response.json()


    # Fetch steps data
    steps_response = requests.get(STEPS_URL, headers=headers)
    steps_data = steps_response.json()
    
    if 'activities-steps' not in steps_data:
        return f"Error fetching steps data: {steps_data}"
    steps_list = display_steps_data(steps_data)

    # Get PC metrics
    pc_metrics = get_pc_metrics()

    #Call the displaying function from fitbitmetrics.py to render the data
    return render_template(
        'display_data.html',
        resting_heart_rate=fitbit_data['activities-heart'][0]['value'].get('restingHeartRate', None),
        heart_rate_zones=fitbit_data['activities-heart'][0]['value'].get('heartRateZones', []),
        real_time_data=real_time_data.get('activities-heart-intraday', {}).get('dataset', []),
        steps_data=steps_list,
        pc_metrics=pc_metrics
    )
if __name__ == "__main__":
    app.run(port=5001, debug=True,  use_reloader=True)