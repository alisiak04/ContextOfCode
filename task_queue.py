import time
import threading
import heapq
from datetime import datetime
from collections import namedtuple

# Define a Task object with a priority field for the queue
# The priority ensures tasks with same next_run time are ordered consistently
Task = namedtuple('Task', ['next_run', 'interval', 'name', 'function', 'priority'])

# Make Task comparable based on next_run time and then priority
def __lt__(self, other):
    if self.next_run == other.next_run:
        return self.priority < other.priority
    return self.next_run < other.next_run

# Add the __lt__ method to the Task namedtuple
Task.__lt__ = __lt__

class TaskQueue:
    def __init__(self, socketio=None):
        self.queue = []  # Priority queue
        self.lock = threading.Lock()
        self.running = True
        self.socketio = socketio
        self.last_execution = {}  # Track last execution time for each task
        
    def add_task(self, name, function, interval_seconds, initial_delay=0, priority=0):
        """Add a task to the queue with a specific interval and optional initial delay"""
        next_run = time.time() + initial_delay
        with self.lock:
            task = Task(next_run, interval_seconds, name, function, priority)
            heapq.heappush(self.queue, task)
            self.last_execution[name] = 0  # Initialize last execution time
        print(f"✅ Added task: {name} (runs every {interval_seconds}s, next run in {initial_delay}s)")
            
    def run(self):
        """Process tasks from the queue when they're due to run"""
        while self.running:
            now = time.time()
            task_to_run = None
            
            with self.lock:
                if self.queue and self.queue[0].next_run <= now:
                    task = heapq.heappop(self.queue)
                    task_to_run = task
                    
                    # Re-schedule the task with its interval
                    # If interval is infinity, don't reschedule
                    if task.interval != float('inf'):
                        next_task = Task(
                            now + task.interval,
                            task.interval,
                            task.name,
                            task.function,
                            task.priority
                        )
                        heapq.heappush(self.queue, next_task)
            
            if task_to_run:
                try:
                    # Update last execution time before running
                    self.last_execution[task_to_run.name] = now
                    print(f"🔄 Running task: {task_to_run.name} at {datetime.fromtimestamp(now).strftime('%H:%M:%S')}")
                    
                    # Execute the task function
                    result = task_to_run.function()
                    
                    # Emit result via websocket if available and result is not None
                    if result and self.socketio:
                        # Determine the event name based on task name
                        event_name = f"update_{task_to_run.name}"
                        self.socketio.emit(event_name, result)
                        print(f"📡 Emitted {task_to_run.name} data to frontend")
                except Exception as e:
                    print(f"❌ Error in task {task_to_run.name}: {e}")
                    import traceback
                    traceback.print_exc()
            
            # Sleep briefly to prevent CPU spinning
            time.sleep(0.1)
    
    def start(self):
        """Start the task queue in a separate thread"""
        self.thread = threading.Thread(target=self.run, daemon=True)
        self.thread.start()
        print("🚀 Task queue started")
        
    def stop(self):
        """Stop the task queue"""
        self.running = False
        if hasattr(self, 'thread'):
            self.thread.join(timeout=5.0)
        print("⏹️ Task queue stopped")
        
    def get_task_status(self):
        """Return status information about all scheduled tasks"""
        now = time.time()
        status = []
        
        with self.lock:
            for task in self.queue:
                last_run = self.last_execution.get(task.name, 0)
                next_run = task.next_run
                
                status.append({
                    "name": task.name,
                    "interval": task.interval,
                    "last_run": datetime.fromtimestamp(last_run).strftime('%Y-%m-%d %H:%M:%S') if last_run > 0 else "Never",
                    "next_run": datetime.fromtimestamp(next_run).strftime('%Y-%m-%d %H:%M:%S'),
                    "seconds_until_next_run": int(next_run - now) if next_run > now else 0
                })
                
        return status