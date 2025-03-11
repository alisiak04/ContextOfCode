import time
import logging
from threading import Lock

class CachedData:
    _instance = None
    _logger = logging.getLogger(__name__)
    
    def __new__(cls, *args, **kwargs):
        if cls._instance is None:
            cls._instance = super(CachedData, cls).__new__(cls)
            cls._instance._initialized = False
        return cls._instance
    
    def __init__(self, cache_duration_seconds: int = 300):
        if getattr(self, '_initialized', False):
            return
            
        self.data = None  # Stores Fitbit data
        self.access_token = None  # Stores Fitbit access token
        self.cache_duration_seconds = cache_duration_seconds
        self.last_updated = time.monotonic() - self.cache_duration_seconds  # Force initial update
        self.active_update_start_time = 0
        self.lock = Lock()
        self._initialized = True

    def __enter__(self):
        """Thread-safe entry point."""
        self.lock.acquire()
        return self 

    def __exit__(self, exc_type, exc_val, exc_tb):
        """Thread-safe exit point."""
        assert self.lock.locked()
        self.lock.release()

    def is_expired(self) -> bool:
        """Check if cache is expired, ensuring updates happen safely."""
        print("🛠 Checking cache expiration...")
        print(f"🔹 Lock status: {self.lock.locked()}")
        print(f"🔹 Last updated: {self.last_updated}")
        print(f"🔹 Cache duration: {self.cache_duration_seconds}")
        print(f"🔹 Active update start time: {self.active_update_start_time}")

        assert self.lock.locked()
        cache_age_seconds = time.monotonic() - self.last_updated

        if cache_age_seconds < self.cache_duration_seconds:
            print("✅ Cache is NOT expired.")
            return False

        print("⚠️ Cache has expired. Checking for updates...")

        if self.active_update_start_time != 0:
            # If an update is in progress, return old data unless it's too old or missing
            if time.monotonic() - self.active_update_start_time >= 2 * self.cache_duration_seconds:
                CachedData._logger.debug("Update taking too long. Forcing refresh.")
                self.active_update_start_time = 0
                return True
            return self.data is None  # If no data exists, force update

        return True  # Cache has expired and no update is in progress

    def update(self, data: any, access_token: str = None):
        """Update cache with new data and optional access token."""
        assert self.lock.locked()
        if access_token:
            print(f"🔑 Updating access token in cache: {access_token}")
            self.access_token = access_token  # Update token if provided
        
        self.data = data
        self.active_update_start_time = 0
        self.last_updated = time.monotonic()

    def get_data(self):
        """Retrieve cached Fitbit data."""
        assert self.lock.locked()
        return self.data

    def get_token(self):
        """Retrieve cached access token."""
        assert self.lock.locked()
        print(f"🔑 Fetching access token from cache... Current token: {self.access_token}")
        return self.access_token