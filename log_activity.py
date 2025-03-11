import requests
from cached_data import CachedData

cached_data = CachedData(cache_duration_seconds=300)  # Ensures stored access token

def log_activity(data):
    """Logs an activity to Fitbit using user input."""
    try:
        print(f"🔍 getting to log activity")
        with cached_data:
            access_token = cached_data.get_token()  # Retrieve stored token
            print(f"🔍 Retrieved Access Token: {access_token}")

        if not access_token:
            return {"message": "❌ No valid access token!"}, 401

        print(f"🔑 Using Access Token for Log Activity: {access_token}")
        url = "https://api.fitbit.com/1/user/-/activities.json"
        headers = {
            "Authorization": f"Bearer {access_token}",
            "Content-Type": "application/json"
        }

        payload = {
            "activityId": int(data["activityId"]),
            "startTime": data["startTime"],
            "durationMillis": int(data["duration"]) * 60 * 1000,
            "date": data["date"],
            "manualCalories": int(data["calories"]),
            "distance": float(data["distance"]),
            "distanceUnit": "km"
        }

        response = requests.post(url, json=payload, headers=headers)

        if response.status_code == 201:
            return {"message": "✅ Activity logged successfully!"}, 201
        else:
            return {"message": f"❌ Error: {response.text}"}, response.status_code

    except Exception as e:
        return {"message": f"⚠️ Exception: {str(e)}"}, 500