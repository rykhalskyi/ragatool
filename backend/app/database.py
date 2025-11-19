import sqlite3
from sqlite3 import Connection
import sys
import threading

DATABASE_URL = "ragatouille.db"
lock = threading.Lock()

def get_db_connection() -> Connection:
    with lock:
        conn = sqlite3.connect(DATABASE_URL, check_same_thread=False)
        conn.row_factory = sqlite3.Row
        return conn

def create_tables():
    conn = get_db_connection()
    cursor = conn.cursor()
    
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS collections (
        id TEXT PRIMARY KEY,
        name TEXT NOT NULL,
        description TEXT,
        model TEXT,
        chunk_size INTEGER,
        chunk_overlap INTEGER,
        enabled BOOLEAN,
        import_type TEXT DEFAULT 'NONE',
        locked BOOLEAN
    )
    """)

    cursor.execute("""
    CREATE TABLE IF NOT EXISTS tasks (
        id TEXT PRIMARY KEY,
        collectionId TEXT,
        name TEXT NOT NULL,
        startTime INTEGER,
        status TEXT
    )
    """)

    cursor.execute("""
    CREATE TABLE IF NOT EXISTS logs (
        id TEXT PRIMARY KEY,
        timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
        collectionId TEXT,
        collectionName TEXT,
        message TEXT
    )
    """)
    
    conn.commit()
    conn.close()

if __name__ == "__main__":
    create_tables()
