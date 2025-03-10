import sqlite3

DATABASE = "health_work_balance.db"

def get_db_connection():
    """Establish a connection to the SQLite database."""
    conn = sqlite3.connect(DATABASE)
    conn.row_factory = sqlite3.Row  # Enables dictionary-like row access
    return conn

def insert_user(display_name):
    """Insert a user into the database (if not exists) and return the user_id."""
    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("INSERT OR IGNORE INTO users (display_name) VALUES (?)", (display_name,))
        conn.commit()
        return cursor.execute("SELECT id FROM users WHERE display_name=?", (display_name,)).fetchone()["id"]

def insert_resting_heart_rate(user_id, resting_heart_rate):
    """Insert the user's resting heart rate into the database."""
    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute(
            "INSERT INTO RestHeartRate (user_id, date, resting_heart_rate) VALUES (?, DATE('now'), ?)",
            (user_id, resting_heart_rate)
        )
        conn.commit()

def insert_real_time_heart_rate(user_id, real_time_data):
    """Insert real-time heart rate measurements into the database."""
    with get_db_connection() as conn:
        cursor = conn.cursor()
        for entry in real_time_data.get('activities-heart-intraday', {}).get('dataset', []):
            cursor.execute(
                "INSERT INTO RealTimeHeartRate (user_id, timestamp, heart_rate) VALUES (?, ?, ?)",
                (user_id, entry["time"], entry["value"])
            )
        conn.commit()

def insert_steps(user_id, steps_data):
    """Insert step count into the database (screen time will be updated later)."""
    with get_db_connection() as conn:
        cursor = conn.cursor()
        for entry in steps_data.get('activities-steps-intraday', {}).get('dataset', []):
            cursor.execute(
                "INSERT INTO StepScreen (user_id, timestamp, steps, screen_time) VALUES (?, ?, ?, ?)",
                (user_id, entry["time"], entry["value"], 0)  # Screen time will be updated later
            )
        conn.commit()

def insert_pc_metrics(user_id, pc_metrics):
    """Insert CPU usage and open tabs count into the database."""
    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute(
            "INSERT INTO PC_usage (user_id, timestamp, cpu_usage, open_tabs) VALUES (?, CURRENT_TIMESTAMP, ?, ?)",
            (user_id, pc_metrics["cpu_load"], pc_metrics["total_tabs"])
        )
        conn.commit()