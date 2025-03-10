from flask import Flask, request, redirect, render_template
from flask_socketio import SocketIO
from app.api.fitbit import FitbitAPI
from app.errors.handlers import FitbitAPIError, handle_fitbit_error
from task_scheduler import TaskScheduler

app = Flask(__name__)
socketio = SocketIO(app, cors_allowed_origins="*")  # Enable WebSockets

latest_data = {}  # Store latest fetched data
scheduler = None  # Background scheduler reference

@app.route("/")
def home():
    """Redirect user to Fitbit login"""
    return redirect(FitbitAPI.get_auth_link())

@app.route("/callback")
def callback():
    """Handle OAuth callback and start background scheduler"""
    global scheduler

    try:
        auth_code = request.args.get("code")
        if not auth_code:
            raise FitbitAPIError("No authorization code received!")

        # Get Fitbit access token
        token_json = FitbitAPI.get_access_token(auth_code)
        access_token = token_json["access_token"]

        # Start task scheduler
        scheduler = TaskScheduler(access_token, latest_data, socketio)
        scheduler.start()

        return render_template("display_data.html")

    except FitbitAPIError as e:
        return handle_fitbit_error(e)

if __name__ == "__main__":
    socketio.run(app, port=5001, debug=True, use_reloader=False)