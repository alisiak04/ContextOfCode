from flask import Flask, request, redirect, render_template, jsonify
from flask_socketio import SocketIO, emit
from app.api.fitbit import FitbitAPI
from app.errors.handlers import FitbitAPIError, handle_fitbit_error
from task_scheduler import TaskScheduler
from cache_update_manager import CacheUpdateManager
from cached_data import CachedData
from Database.retrieve_database import fetch_hourly_steps, fetch_pc_usage_trends
import json
from log_activity import log_activity  
from task_scheduler import shared_data
app = Flask(__name__)
socketio = SocketIO(app, cors_allowed_origins="*")

# Get singleton instance of CachedData
cached_data = CachedData(cache_duration_seconds=300)
scheduler = None  # Background scheduler reference

@app.route("/")
def home():
    """Redirect user to Fitbit login if no cached token, else show data."""
    with cached_data:
        if cached_data.get_token():
            return redirect("/data")
    
    return redirect(FitbitAPI.get_auth_link())

@app.route("/callback")
def callback():
    """Handle OAuth callback and start background scheduler."""
    global scheduler
    
    try:
        auth_code = request.args.get("code")
        if not auth_code:
            raise FitbitAPIError("No authorization code received!")

        # Exchange auth code for access token
        token_json = FitbitAPI.get_access_token(auth_code)
        access_token = token_json["access_token"]

        # Update cache with access token
        with cached_data:
            cached_data.update(data=None, access_token=access_token)

        # Start scheduler
        scheduler = TaskScheduler(access_token, socketio)
        scheduler.start()

        # Immediately fetch and cache data
        initial_data = FitbitAPI.get_user_data(access_token)
        with cached_data:
            cached_data.update(initial_data)  # Update cache with initial data

        return redirect("/data")

    except FitbitAPIError as e:
        return handle_fitbit_error(e)

@app.route("/data")
def display_data():
    """Fetch and cache data immediately if expired, otherwise return cached data."""
    try:
        print("🔄 Entering /data route...") 
        with cached_data:
            if cached_data.is_expired():
                access_token = cached_data.get_token()
                if not access_token:
                    return redirect("/")  # No token, re-authenticate
                
                # Fetch new data and cache it
                new_data = FitbitAPI.get_user_data(access_token)
                with cached_data:
                    cached_data.update(new_data)
            
            data_snapshot = cached_data.get_data()
        
        return render_template("display_data.html", data=data_snapshot)
    
    except Exception as e:
        print(f"Error in fetching data: {e}") 
        return {"status": "error", "message": str(e)}, 500


@app.route("/trends")
def trends():
    """Render the trends page."""
    return render_template("trends.html")

@app.route("/api/hourly_steps")
def hourly_steps():
    """Fetch hourly steps data."""
    return jsonify(fetch_hourly_steps())

@app.route('/api/pc_usage')
def get_pc_usage():
    return jsonify(fetch_pc_usage_trends())

@app.route("/api/log_activity", methods=["POST"])
def log_activity_endpoint():
    """Endpoint to log user activity to Fitbit."""
    print("🚀 Received request at /api/log_activity")
    
    data = request.json
    print(f"📨 Request Data: {data}")

    result, status = log_activity(data)  # Using the imported function with singleton
    print(f"📤 Response: {result}, Status: {status}")
    return jsonify(result), status


@socketio.on('connect')
def handle_connect(auth=None):
    """Handle WebSocket connection with optional authentication."""
    try:
        print("✅ Client connected")
        with shared_data["lock"]:
            current_data = shared_data["data"].copy()  # Safe access to shared data
        socketio.emit('update_metrics', current_data)
    except Exception as e:
        print(f"❌ Error in handle_connect: {e}")

if __name__ == "__main__":
    socketio.run(app, port=5001, debug=True, use_reloader=False)
