import sqlite3

DATABASE = "health_work_balance.db"

def get_db_connection():
    conn = sqlite3.connect(DATABASE)
    conn.row_factory = sqlite3.Row
    return conn

def insert_user(display_name):
    with get_db_connection() as conn:
        cursor = conn.cursor()
        
        # Insert and ensure we get a valid user ID
        cursor.execute("INSERT INTO users (display_name) VALUES (?) ON CONFLICT(display_name) DO NOTHING", (display_name,))
        conn.commit()
        
        cursor.execute("SELECT id FROM users WHERE display_name=?", (display_name,))
        row = cursor.fetchone()
        if row:
            return row["id"]
        else:
            print(f"⚠️ Display Name '{display_name}' was not inserted or found!")
            return None
        
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
    if not real_time_hr_data:
        print("⚠️ No real-time heart rate data to insert.")
        return

    with get_db_connection() as conn:
        cursor = conn.cursor()

        if isinstance(real_time_hr_data, list):
            # ✅ If `real_time_hr_data` is a list of heart rate readings
            for entry in real_time_hr_data:
                if "value" in entry and "time" in entry:
                    cursor.execute("""
                        INSERT INTO RealTimeHeartRate (user_id, timestamp, heart_rate)
                        VALUES (?, ?, ?)
                    """, (user_id, entry["time"], entry["value"]))

        elif isinstance(real_time_hr_data, dict):
            # ✅ If it's a dictionary with 'activities-heart-intraday' structure
            dataset = real_time_hr_data.get("activities-heart-intraday", {}).get("dataset", [])
            for entry in dataset:
                if "value" in entry and "time" in entry:
                    cursor.execute("""
                        INSERT INTO RealTimeHeartRate (user_id, timestamp, heart_rate)
                        VALUES (?, ?, ?)
                    """, (user_id, entry["time"], entry["value"]))

        else:
            print(f"⚠️ Unexpected data format for real_time_hr_data: {type(real_time_hr_data)}")

        conn.commit()
        print(f"✅ Inserted {cursor.rowcount} real-time heart rate records for user {user_id}.")

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