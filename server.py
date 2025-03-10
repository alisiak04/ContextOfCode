from flask import Flask, request, redirect, render_template, jsonify
from app.api.fitbit import FitbitAPI
from app.utils.pcmetrics import get_pc_metrics
from app.utils.fitbitmetrics import display_steps_data
from app.utils.activity_monitor import ActivityMonitor
from app.errors.handlers import FitbitAPIError, handle_fitbit_error
from threading import Thread
import time
from datetime import datetime, timedelta

app = Flask(__name__)
activity_monitor = ActivityMonitor()

def background_activity_check(access_token):
    """Background thread to check activity periodically"""
    while True:
        try:
            # Get latest user data
            fitbit_user = FitbitAPI.get_user_data(access_token)
            steps_list = display_steps_data(fitbit_user.steps)
            
            if steps_list and steps_list[0]:
                current_steps = steps_list[0].get('value', 0)
                # Check inactivity and send notification if needed
                activity_monitor.check_inactivity(current_steps, access_token)
            
            # Check every minute instead of every 5 minutes
            time.sleep(60)
        except Exception as e:
            print(f"Error in activity check: {e}")
            time.sleep(60)  # Wait a minute before retrying

@app.route("/debug/activity")
def debug_activity():
    """Debug endpoint to check activity monitor status"""
    status = activity_monitor.get_status()
    return jsonify(status)

@app.route("/")
def home():
    """Step 1: Redirect user to Fitbit login"""
    print("Home route accessed")
    return redirect(FitbitAPI.get_auth_link())

@app.route("/callback")
def callback():
    """Step 2: Handle the OAuth callback"""
    try:
        print("Callback route accessed")
        auth_code = request.args.get("code")
        if not auth_code:
            raise FitbitAPIError("No authorization code received!")

        # Get access token
        token_json = FitbitAPI.get_access_token(auth_code)
        access_token = token_json["access_token"]
        print("Access token received:", access_token)

        # Get initial user data
        fitbit_user = FitbitAPI.get_user_data(access_token)
        steps_list = display_steps_data(fitbit_user.steps)
        
        # Perform immediate activity check if steps data is available
        if steps_list and steps_list[0]:
            current_steps = steps_list[0].get('value', 0)
            activity_monitor.last_step_time = datetime.now() - timedelta(minutes=5)  # Set last step time 5 minutes ago
            activity_monitor.check_inactivity(current_steps, access_token)

        # Start background activity monitoring
        activity_thread = Thread(target=background_activity_check, args=(access_token,))
        activity_thread.daemon = True
        activity_thread.start()
        print("Started activity monitoring thread")
        
        # Get additional metrics
        pc_metrics = get_pc_metrics()

        return render_template(
            'display_data.html',
            profile_data=fitbit_user.profile,
            resting_heart_rate=fitbit_user.resting_heart_rate,
            heart_rate_zones=fitbit_user.heart_rate_zones,
            real_time_data=fitbit_user.real_time_heart_rate_data,
            steps_data=steps_list,
            pc_metrics=pc_metrics
        )

    except FitbitAPIError as e:
        return handle_fitbit_error(e)

if __name__ == "__main__":
    app.run(port=5001, debug=True, use_reloader=True) 