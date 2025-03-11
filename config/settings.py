class Config:
    # Fitbit App credentials
    CLIENT_ID = "23Q3T7"
    CLIENT_SECRET = "eee401b70553617de75989d262207feb"
    REDIRECT_URI = "http://localhost:5001/callback"

    # Fitbit API URLs
    AUTH_URL = "https://www.fitbit.com/oauth2/authorize"
    TOKEN_URL = "https://api.fitbit.com/oauth2/token"
    HEART_RATE_URL = "https://api.fitbit.com/1/user/-/activities/heart/date/today/1d.json"
    STEPS_URL = "https://api.fitbit.com/1/user/-/activities/steps/date/today/1d/15min.json"
    REAL_TIME_HEART_RATE_URL = "https://api.fitbit.com/1/user/-/activities/heart/date/today/1d/1min.json"
    DISPLAY_NAME_URL = "https://api.fitbit.com/1/user/-/profile.json" 
    LOG_ACTIVITY_URL = "https://api.fitbit.com/1/user/-/activities.json"