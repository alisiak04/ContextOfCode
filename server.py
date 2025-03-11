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

app = Flask(__name__)
socketio = SocketIO(app, cors_allowed_origins="*")

# Thread-safe cache
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
        scheduler = TaskScheduler(access_token, cached_data, socketio)
        scheduler.start()

        initial_data = FitbitAPI.get_user_data(access_token)


        with cached_data:
            cached_data.update(initial_data)  # Update cache with initial data



        return redirect("/data")

    except FitbitAPIError as e:
        return handle_fitbit_error(e)

@app.route("/data")
def display_data():
    """Fetch Fitbit data using thread-safe caching."""
    try:
        print("🔄 Entering /data route...") 
        with cached_data:
            print("🔎 Checking if cached data is expired...")
            if cached_data.is_expired():
                with CacheUpdateManager(cached_data) as cache_update_manager:
                    if cache_update_manager.update_started_elsewhere():
                        print("🔄 Another thread is updating the cache. Waiting...")
                        cache_update_manager.spin_wait_for_update_to_complete()
                        data_snapshot = None
                    else:
                        print("✅ No other updates in progress. Fetching new data...")
                        access_token = cached_data.get_token()
                        print(f"🔑 Storing new access token: {access_token}")
                        if not access_token:
                            print("⚠️ No access token found, redirecting to login.")
                            return redirect("/")  # No token, re-authenticate
                       
                        print(f"Fetching data with token: {access_token}")
                        data_snapshot = FitbitAPI.get_user_data(access_token)

                if data_snapshot:
                    cached_data.update(data_snapshot)

            else:
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
    print("🚀 Received request at /api/log_activity")  # ✅ Debugging
    
    data = request.json
    print(f"📨 Request Data: {data}")  # ✅ Debugging

    result, status = log_activity(data)  # ✅ Call imported function
    print(f"📤 Response: {result}, Status: {status}")  # ✅  # ✅ Call imported function
    return jsonify(result), status

@socketio.on('connect')
def handle_connect(auth):
    print("🔌 Client connected, pushing cached data...")

    if cached_data and cached_data.data:
        try:
            # Ensure JSON-serializable format
            json_serializable_data = json.dumps(cached_data.data, default=lambda o: o.__dict__)
            emit('update_metrics', json.loads(json_serializable_data))  # Convert back to dictionary
        except Exception as e:
            print(f"⚠️ JSON Serialization Error: {e}")
    else:
        print("⚠️ No cached data available to send.")

if __name__ == "__main__":
    socketio.run(app, port=5001, debug=True, use_reloader=False)