class FitbitAPIError(Exception):
    """Base exception for Fitbit API errors"""
    pass

class AuthenticationError(FitbitAPIError):
    """Raised when authentication fails"""
    pass

class DataFetchError(FitbitAPIError):
    """Raised when unable to fetch data from Fitbit API"""
    pass

def handle_fitbit_error(error):
    """Handle Fitbit API errors and return appropriate response"""
    if isinstance(error, AuthenticationError):
        return "Authentication Error: Failed to authenticate with Fitbit", 401
    elif isinstance(error, DataFetchError):
        return f"Data Fetch Error: {str(error)}", 500
    return f"Unexpected Error: {str(error)}", 500 