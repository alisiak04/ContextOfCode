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
            SELECT 
                strftime('%Y-%m-%d %H:00', timestamp) AS hour,
                MAX(steps) - MIN(steps) AS total_steps
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
    
def fetch_pc_usage_trends():
    """Fetch CPU, Memory, and Disk usage trends from the last 24 hours."""
    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("""
            SELECT 
                strftime('%H', timestamp) AS hour, 
                ROUND(AVG(cpu_usage), 2) AS avg_cpu_usage, 
                ROUND(AVG(memory_usage), 2) AS avg_memory_usage,
                ROUND(AVG(disk_usage), 2) AS avg_disk_usage
            FROM PC_usage
            WHERE timestamp >= datetime('now', '-24 hours')
            GROUP BY hour
            ORDER BY hour;
        """)

        rows = cursor.fetchall()

        return {
            "labels": [f"{row['hour']}:00" for row in rows],  # Hours formatted
            "cpu_usage": [row['avg_cpu_usage'] for row in rows],  # Avg CPU usage
            "memory_usage": [row['avg_memory_usage'] for row in rows],  # Avg Memory usage
            "disk_usage": [row['avg_disk_usage'] for row in rows]  # Avg Disk usage
        }
