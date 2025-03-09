import sqlite3

DATABASE = "healthworkbalance.db"

def get_db_connection():
    conn = sqlite3.connect(DATABASE)
    conn.row_factory = sqlite3.Row  # Allows access to columns by name
    return conn

def init_db():
    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.executescript(open("schema.sql").read())  # Loads your schema
        conn.commit()