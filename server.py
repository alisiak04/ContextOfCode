from flask import Flask, request, redirect, render_template, jsonify
from flask_socketio import SocketIO
from app.api.fitbit import FitbitAPI
from app.errors.handlers import FitbitAPIError, handle_fitbit_error
from task_scheduler import TaskScheduler
from Database.retrieve_database import fetch_hourly_steps, fetch_pc_usage_trends
from log_activity import log_activity  
from cached_data import CachedData
app = Flask(__name__)
socketio = SocketIO(app, cors_allowed_origins="*")
cached_data = CachedData(cache_duration_seconds=300)
scheduler = None  # Background scheduler reference

@app.route("/")
def home():
    """Redirect user to Fitbit login if no cached token, else show data."""
    return redirect(FitbitAPI.get_auth_link())

@app.route("/callback")
def callback():
    """Handle OAuth callback and start scheduler."""
    global scheduler
    try:
        auth_code = request.args.get("code")
        if not auth_code:
            raise FitbitAPIError("No authorization code received!")

        token_json = FitbitAPI.get_access_token(auth_code)
        access_token = token_json["access_token"]

        initial_data = FitbitAPI.get_user_data(access_token)
        with cached_data:
            cached_data.update(initial_data, access_token)
            print(f"✅ Token stored in cached_data: {access_token[:10]}...")

        # Start scheduler immediately
        scheduler = TaskScheduler(access_token, socketio)
        scheduler.start()
        
        return redirect("/data")

    except FitbitAPIError as e:
        return handle_fitbit_error(e)

@app.route("/data")
def display_data():
    """Return the latest fetched data."""
    if scheduler is None:
        return jsonify({"error": "Scheduler not initialized"}), 500

    with scheduler.shared_data["lock"]:
        latest_data = scheduler.shared_data["data"].copy()
    
    return render_template("display_data.html", data=latest_data)

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
    
    ## Try to get token from scheduler first, then fall back to cached token
    access_token = None
    if scheduler is not None:
        access_token = scheduler.access_token
    
    # If no token from scheduler, try the cached token
    if not access_token:
        with cached_data:
            access_token = cached_data.get_token()
    
    # Still no token? Return error
    if not access_token:
        return jsonify({"message": "❌ Not authenticated. Please log in with Fitbit first!"}), 401
    
    data = request.json
    
    
    # Your log_activity function doesn't accept a token parameter, 
    # but it uses the cached_data singleton internally
    result, status = log_activity(data)
    
    print(f"📤 Response: {result}, Status: {status}")
    return jsonify(result), status


@socketio.on('connect')
def handle_connect():  # Remove 'sid' parameter - SocketIO handles room assignment automatically
    """Send the latest metrics to the client on WebSocket connect."""
    if scheduler is None:
        print("⚠️ Scheduler not initialized. Client might need to authenticate first.")
        socketio.emit('auth_required', {"message": "Please log in with Fitbit first"})
        return

    with scheduler.shared_data["lock"]:
        current_data = scheduler.shared_data["data"].copy()
    
    
    socketio.emit('update_metrics', current_data)

if __name__ == "__main__":
    socketio.run(app, port=5001, debug=True, use_reloader=False)
