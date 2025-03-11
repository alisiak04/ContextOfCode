from flask import Flask, request, redirect, render_template, jsonify
from flask_socketio import SocketIO
from app.api.fitbit import FitbitAPI
from app.errors.handlers import FitbitAPIError, handle_fitbit_error
from task_scheduler import TaskScheduler
import json

app = Flask(__name__)
socketio = SocketIO(app, cors_allowed_origins="*")

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

@socketio.on('connect')
def handle_connect(sid):
    """Send the latest metrics to the client on WebSocket connect."""
    if scheduler is None:
        print("❌ Scheduler not initialized. Cannot send data.")
        return

    with scheduler.shared_data["lock"]:
        current_data = scheduler.shared_data["data"].copy()
    
    print("📊 Sending current metrics on connect:", json.dumps(current_data, indent=2))
    socketio.emit('update_metrics', current_data, room=sid)

if __name__ == "__main__":
    socketio.run(app, port=5001, debug=True, use_reloader=False)
