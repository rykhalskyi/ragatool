import os
import sqlite3
from contextlib import contextmanager
from sqlite3 import Connection
import sys
import threading
from typing import Iterator, Optional

DATABASE_URL = os.getenv("DATABASE_PATH", "ragatouille.db")
lock = threading.Lock()

def get_db_connection() -> Connection:
    with lock:
        conn = sqlite3.connect(DATABASE_URL, check_same_thread=False, timeout=10)
        conn.row_factory = sqlite3.Row
        conn.execute("PRAGMA busy_timeout = 10000")
        return conn


@contextmanager
def db_session() -> Iterator[Connection]:
    """Open a connection, commit on success, roll back on error, and close."""
    conn = get_db_connection()
    try:
        yield conn
        conn.commit()
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()

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
    INSERT OR IGNORE INTO settings (name, value, description)
    VALUES ('UrlImportRecentFilters', '[]', 'Recently used URL import filter regular expressions (JSON array)')
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

    try:
        # Ragatool is single-user; enforce it at the storage layer.
        cursor.execute(
            "CREATE UNIQUE INDEX IF NOT EXISTS auth_users_single ON auth_users ((1))"
        )
    except sqlite3.IntegrityError:
        print(
            "WARNING: auth_users has multiple rows; single-user index not created.",
            flush=True,
        )

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

    cursor.execute("""
    CREATE TABLE IF NOT EXISTS llm_profiles (
        id TEXT PRIMARY KEY,
        name TEXT NOT NULL,
        provider TEXT NOT NULL,
        base_url TEXT NOT NULL,
        api_key TEXT NOT NULL,
        model TEXT NOT NULL,
        temperature REAL NOT NULL DEFAULT 0.2,
        max_tokens INTEGER NOT NULL DEFAULT 2048,
        connect_timeout_seconds INTEGER NOT NULL DEFAULT 30,
        read_timeout_seconds INTEGER NOT NULL DEFAULT 120,
        is_active BOOLEAN NOT NULL DEFAULT 0,
        created_at TEXT NOT NULL,
        updated_at TEXT
    )
    """)

    cursor.execute("""
    CREATE UNIQUE INDEX IF NOT EXISTS llm_profiles_single_active
    ON llm_profiles ((1)) WHERE is_active = 1
    """)

    conn.commit()
    if close_conn:
        conn.close()

if __name__ == "__main__":
    create_tables()
