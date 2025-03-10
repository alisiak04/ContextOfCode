import sqlite3
from datetime import datetime

DATABASE = "health_work_balance.db"

def get_db_connection():
    conn = sqlite3.connect(DATABASE)
    conn.row_factory = sqlite3.Row
    return conn

def insert_user(display_name):
    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("INSERT OR IGNORE INTO users (display_name) VALUES (?)", (display_name,))
        conn.commit()
        cursor.execute("SELECT id FROM users WHERE display_name=?", (display_name,))
        user = cursor.fetchone()
        return user["id"] if user else None

def insert_resting_heart_rate(user_id, resting_heart_rate, date=None):
    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute(
            "INSERT INTO RestHeartRate (user_id, date, resting_heart_rate) VALUES (?, ?, ?)",
            (user_id, date_today() if not date_today() else date_today(), resting_heart_rate)
        )
        conn.commit()

def insert_real_time_heart_rate(user_id, heart_rate):
    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute(
            "INSERT INTO RealTimeHeartRate (user_id, timestamp, heart_rate) VALUES (?, DATETIME('now'), ?)",
            (user_id, heart_rate)
        )
        conn.commit()

def insert_pc_metrics(user_id, cpu_usage, open_tabs):
    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute(
            "INSERT INTO PC_usage (user_id, timestamp, cpu_usage, open_tabs) VALUES (?, DATETIME('now'), ?, ?)",
            (user_id, cpu_usage, open_tabs)
        )
        conn.commit()

def insert_steps_screen(user_id, steps, screen_time_minutes):
    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute(
            "INSERT INTO StepScreen (user_id, timestamp, steps) VALUES (?, DATETIME('now'), ?)",
            (user_id, steps)
        )
        step_screen_id = cursor.lastrowid
        # If you plan to track screen_time separately, add an UPDATE method later.
        conn.commit()

def insert_real_time_heart_rate(user_id, real_time_data):
    """Insert real-time heart rate measurements into the database."""
    with get_db_connection() as conn:
        cursor = conn.cursor()
        for entry in real_time_data.get('activities-heart-intraday', {}).get('dataset', []):
            timestamp = entry["time"]
            value = entry["value"]
            cursor.execute(
                "INSERT INTO RealTimeHeartRate (user_id, timestamp, heart_rate) VALUES (?, ?, ?)",
                (user_id, timestamp, value)
            )
        conn.commit()

def insert_resting_heart_rate(user_id, resting_heart_rate, date=None):
    date = date or date_today()
    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute(
            "INSERT INTO RestHeartRate (user_id, date, resting_heart_rate) VALUES (?, ?, ?)",
            (user_id, date, resting_heart_rate)
        )
        conn.commit()

def insert_burnout_metrics(user_id, total_stress_time, avg_heart_rate, date=None):
    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute(
            "INSERT INTO BurnoutTrends (user_id, date, total_stress_time, avg_heart_rate) VALUES (?, ?, ?, ?)",
            (user_id, date or date_today(), total_stress_time, avg_heart_rate)
        )
        conn.commit()

# Helper function
def date_today():
    return sqlite3.connect(DATABASE).execute("SELECT DATE('now')").fetchone()[0]