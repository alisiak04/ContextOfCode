import sqlite3

DATABASE = "healthwork_balance.db"

def get_db_connection():
    """Establish a connection to the SQLite database."""
    conn = sqlite3.connect(DATABASE)
    conn.row_factory = sqlite3.Row
    return conn

def fetch_hourly_steps():
    """Fetch hourly step data from the last 24 hours."""
    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("""
            SELECT strftime('%Y-%m-%d %H:00', timestamp) AS hour, SUM(steps) AS total_steps
            FROM StepScreen
            WHERE timestamp >= datetime('now', '-24 hours')
            GROUP BY hour
            ORDER BY hour ASC;
        """)

        rows = cursor.fetchall()

        return {
            "labels": [row["hour"] for row in rows],  # Hours (e.g., '2024-03-11 15:00')
            "steps": [row["total_steps"] for row in rows]  # Step counts
        }

def fetch_work_life_balance_trends():
    """Fetch hourly steps & average CPU usage trends from the last 24 hours."""
    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("""
            SELECT 
                strftime('%H', p.timestamp) AS hour, 
                ROUND(AVG(p.cpu_usage), 2) AS avg_cpu_usage, 
                COALESCE(SUM(s.steps), 0) AS total_steps
            FROM PC_usage p
            LEFT JOIN StepScreen s ON strftime('%H', p.timestamp) = strftime('%H', s.timestamp)
            WHERE p.timestamp >= datetime('now', '-24 hours')
            GROUP BY hour
            ORDER BY hour;
        """)

        rows = cursor.fetchall()

        return {
            "labels": [f"{row['hour']}:00" for row in rows],  # Format hours
            "cpu_usage": [row['avg_cpu_usage'] for row in rows],  # CPU usage
            "steps": [row['total_steps'] for row in rows]  # Step counts
        }