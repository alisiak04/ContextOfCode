import sqlite3
from app.utils.pcmetrics import get_pc_metrics
from datetime import datetime



DATABASE = "healthwork_balance.db"

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
        
def insert_pc_metrics(user_id, cpu_usage, memory_usage, disk_usage, process_count):
    """
    Inserts PC metrics into the database.
    """
    metrics = get_pc_metrics()  # Fetch actual PC metrics

    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("""
            INSERT INTO PC_usage (user_id, cpu_usage, memory_usage, disk_usage, process_count) 
            VALUES (?, ?, ?, ?, ?)
        """, (user_id, 
              float(metrics["cpu_usage"].replace("%", "")),  # Remove % and store as float
              float(metrics["memory_usage"].replace("%", "")),  
              float(metrics["disk_usage"].replace("%", "")),  
              int(metrics["process_count"])))  

        conn.commit()
        

def insert_steps(user_id, steps_data):
    """
    Inserts steps data into the StepScreen table.
    :param user_id: User ID
    :param steps_data: List of dictionaries with {'time': 'HH:MM:SS', 'steps': int}
    """
    if not steps_data:
        print("⚠️ No step data available to insert.")
        return

    with get_db_connection() as conn:
        cursor = conn.cursor()

        for entry in steps_data:
            # Convert time into full timestamp (YYYY-MM-DD HH:MM:SS)
            now = datetime.now().date()
            full_timestamp = f"{now} {entry['time']}"

            cursor.execute("""
                INSERT INTO StepScreen (user_id, timestamp, steps)
                VALUES (?, ?, ?)
            """, (user_id, full_timestamp, entry["steps"]))

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
