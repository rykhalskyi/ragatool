import sqlite3
from sqlite3 import Connection

DATABASE_URL = "ragatouille.db"

def get_db_connection() -> Connection:
    conn = sqlite3.connect(DATABASE_URL)
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
        enabled BOOLEAN
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
    
    conn.commit()
    conn.close()

if __name__ == "__main__":
    create_tables()
