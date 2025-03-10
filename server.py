from flask import Flask, request, redirect, render_template
from flask_socketio import SocketIO, emit
from app.api.fitbit import FitbitAPI
from app.errors.handlers import FitbitAPIError, handle_fitbit_error
from task_scheduler import TaskScheduler
from cache_update_manager import CacheUpdateManager
from cached_data import CachedData

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
                        if not access_token:
                            print("⚠️ No access token found, redirecting to login.")
                            return redirect("/")  # No token, re-authenticate
                       
                        print(f"Fetching data with token: {access_token}")
                        data_snapshot = FitbitAPI.get_user_data(access_token)

                if data_snapshot:
                    cached_data.update(data_snapshot)

            else:
                data_snapshot = cached_data.get_data()
        print(f"Returning data: {data_snapshot}")
        return render_template("display_data.html", data=data_snapshot)

    except Exception as e:
        print(f"Error in fetching data: {e}") 
        return {"status": "error", "message": str(e)}, 500
@socketio.on('connect')
def handle_connect():
    print('🔌 Client connected, pushing cached data...')
    with cached_data:
        if cached_data.data:
            emit('update_metrics', cached_data.data)
        else:
            print("⚠️ No cached data available to send.")

if __name__ == "__main__":
    socketio.run(app, port=5001, debug=True, use_reloader=False)