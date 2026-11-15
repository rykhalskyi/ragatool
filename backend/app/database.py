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
        topic TEXT,
        message TEXT
    )
    """)

    cursor.execute("""
    CREATE TABLE IF NOT EXISTS settings (
        name TEXT PRIMARY KEY,
        value TEXT,
        description TEXT
    )
    """)

    cursor.execute("""
    INSERT OR IGNORE INTO settings (name, value, description) 
    VALUES ('TwoStepImport', 'False', 'Divide import to 2 steps. Collect and preview data and then make import')
    """)

    cursor.execute("""
    INSERT OR IGNORE INTO settings (name, value, description) 
    VALUES ('CrawlDepth', '1', 'URL Import Depth of crawl')
    """)

    cursor.execute("""
    INSERT OR IGNORE INTO settings (name, value, description)
    VALUES ('JsRenderMode', 'auto', 'Render URLs with headless Chromium: auto, always, or off')
    """)

    cursor.execute("""
    INSERT OR IGNORE INTO settings (name, value, description)
    VALUES ('RenderWaitMs', '1500', 'Milliseconds to wait after a rendered page loads')
    """)

    cursor.execute("""
    INSERT OR IGNORE INTO settings (name, value, description)
    VALUES ('MinStaticTextChars', '300', 'Render when static extraction yields fewer characters than this')
    """)

    cursor.execute("""
    INSERT OR IGNORE INTO settings (name, value, description)
    VALUES ('MaxCrawlPages', '100', 'Maximum number of pages fetched per URL import')
    """)

    cursor.execute("""
    INSERT OR IGNORE INTO settings (name, value, description)
    VALUES ('RequestTimeoutSec', '20', 'HTTP request and browser render timeout in seconds')
    """)

    cursor.execute("""
    INSERT OR IGNORE INTO settings (name, value, description)
    VALUES ('CrawlRequestDelayMs', '300', 'Delay in milliseconds between crawl requests')
    """)

    cursor.execute("""
    INSERT OR IGNORE INTO settings (name, value, description)
    VALUES ('RespectRobotsTxt', 'True', 'Honor robots.txt rules while crawling')
    """)

    cursor.execute("""
    INSERT OR IGNORE INTO settings (name, value, description)
    VALUES ('AllowSubdomains', 'False', 'Allow crawling subdomains of the start URL')
    """)

    cursor.execute("""
    INSERT OR IGNORE INTO settings (name, value, description)
    VALUES ('RerankEnabled', 'True', 'Rerank vector search results with a cross-encoder. More precise but slower.')
    """)

    cursor.execute("""
    INSERT OR IGNORE INTO settings (name, value, description)
    VALUES ('RetrievalFetchK', '40', 'Number of candidates fetched from the vector store before reranking')
    """)

    cursor.execute("""
    CREATE TABLE IF NOT EXISTS files (
        id TEXT PRIMARY KEY,
        timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
        collection_id TEXT,
        path TEXT,
        source TEXT
    )
    """)
    
    cursor.execute(""" 
    CREATE TABLE IF NOT EXISTS summary (
        id TEXT PRIMARY KEY,
        collection_id TEXT,
        type INTEGER,
        summary TEXT,
        metadata TEXT
    )
    """)

    cursor.execute("""
    CREATE TABLE IF NOT EXISTS auth_users (
        id TEXT PRIMARY KEY,
        username TEXT NOT NULL UNIQUE,
        password_hash TEXT NOT NULL,
        session_version INTEGER NOT NULL DEFAULT 1,
        created_at DATETIME DEFAULT CURRENT_TIMESTAMP
    )
    """)

    cursor.execute("""
    CREATE TABLE IF NOT EXISTS api_tokens (
        id TEXT PRIMARY KEY,
        name TEXT NOT NULL,
        token_hash TEXT NOT NULL UNIQUE,
        prefix TEXT NOT NULL,
        created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
        last_used_at DATETIME,
        revoked_at DATETIME
    )
    """)

    cursor.execute("""
    CREATE TABLE IF NOT EXISTS sessions (
        id TEXT PRIMARY KEY,
        user_id TEXT NOT NULL,
        token_hash TEXT NOT NULL UNIQUE,
        created_at INTEGER NOT NULL,
        expires_at INTEGER NOT NULL,
        session_version INTEGER NOT NULL
    )
    """)

    conn.commit()
    if close_conn:
        conn.close()

if __name__ == "__main__":
    create_tables()
