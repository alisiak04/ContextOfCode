import time
from cached_data import CachedData

class CacheUpdateManager:
    def __init__(self, cached_data: CachedData):
        self.cached_data = cached_data
        self.update_already_started = False

    def __enter__(self):
        assert self.cached_data.lock.locked()

        # Check if an update is already in progress
        self.update_already_started = self.cached_data.active_update_start_time != 0
        if not self.update_already_started:
            self.cached_data.active_update_start_time = time.monotonic()

        self.cached_data.lock.release()  # Allow other threads to read old data
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.cached_data.lock.acquire()
        # Only reset active_update_start_time if we started the update
        if not self.update_already_started:
            self.cached_data.active_update_start_time = 0

    def update_started_elsewhere(self) -> bool:
        """Check if another thread is already updating."""
        return self.update_already_started
    
    def spin_wait_for_update_to_complete(self):
        """Wait for another thread to finish updating the cache."""
        assert self.update_started_elsewhere()
        
        while True:
            self.cached_data.lock.acquire()
            update_in_progress = self.cached_data.active_update_start_time != 0
            self.cached_data.lock.release()

            if not update_in_progress:
                break
            time.sleep(0.1)  # Reduce CPU usage