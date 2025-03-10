import sqlite3

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
        return cursor.execute("SELECT id FROM users WHERE display_name=?", (display_name,)).fetchone()["id"]

def insert_pc_metrics(user_id, cpu_usage, open_tabs):
    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("""
            INSERT INTO PC_usage (user_id, cpu_usage, open_tabs) 
            VALUES (?, ?, ?)
        """, (user_id, cpu_usage, open_tabs))
        conn.commit()

def insert_steps_screen(user_id, steps, screen_time_minutes):
    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("""
            INSERT INTO StepScreen (user_id, steps, screen_time) 
            VALUES (?, ?, ?)
        """, (user_id, steps, screen_time_minutes))
        conn.commit()

def insert_real_time_heart_rate(user_id, real_time_hr_data):
    """Insert real-time heart rate data into the database."""
    if isinstance(real_time_hr_data, list):
        # If it's a list, iterate over each entry
        for entry in real_time_hr_data:
            # Assuming each entry is a dictionary with the necessary keys
            # Insert each entry into the database
            # Example: insert into your database here
            # db.insert(user_id=user_id, heart_rate=entry['value'], timestamp=entry['time'])
            pass  # Replace with actual insertion logic
    elif isinstance(real_time_hr_data, dict):
        # If it's a dictionary, handle it as before
        for entry in real_time_hr_data.get('activities-heart-intraday', {}).get('dataset', []):
            # Insert each entry into the database
            # Example: insert into your database here
            # db.insert(user_id=user_id, heart_rate=entry['value'], timestamp=entry['time'])
            pass  # Replace with actual insertion logic
    else:
        print("Unexpected data format for real_time_hr_data")

def insert_resting_heart_rate(user_id, resting_heart_rate):
    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("""
            INSERT INTO RestHeartRate (user_id, date, resting_heart_rate)
            VALUES (?, DATE('now'), ?)
        """, (user_id, resting_heart_rate))
        conn.commit()

# def insert_burnout_metrics(user_id, total_stress_time, avg_heart_rate, date=None):
#     with get_db_connection() as conn:
#         cursor = conn.cursor()
#         cursor.execute(
#             "INSERT INTO BurnoutTrends (user_id, date, total_stress_time, avg_heart_rate) VALUES (?, ?, ?, ?)",
#             (user_id, date or date_today(), total_stress_time, avg_heart_rate)
#         )
#         conn.commit()

# # Helper function
# def date_today():
#     return sqlite3.connect(DATABASE).execute("SELECT DATE('now')").fetchone()[0]