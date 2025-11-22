import sqlite3
from sqlite3 import Connection
import sys
import threading
from typing import Optional

DATABASE_URL = "ragatouille.db"
lock = threading.Lock()

def get_db_connection() -> Connection:
    with lock:
        conn = sqlite3.connect(DATABASE_URL, check_same_thread=False)
        conn.row_factory = sqlite3.Row
        return conn

def create_tables(conn: Optional[Connection] = None):
    if conn is None:
        conn = get_db_connection()
        close_conn = True
    else:
        close_conn = False
        
    cursor = conn.cursor()
    
    
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS collections (
        id TEXT PRIMARY KEY,
        name TEXT NOT NULL,
        description TEXT,
        enabled BOOLEAN,
        import_type TEXT DEFAULT 'NONE',
        model TEXT,
        settings TEXT
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
        topic TEXT,
        message TEXT
    )
    """)
    
    conn.commit()
    if close_conn:
        conn.close()

if __name__ == "__main__":
    create_tables()
