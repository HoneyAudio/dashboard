import sqlite3
from contextlib import closing

def create_connection(db_file):
    """
    Create a database connection to the SQLite database.
    """
    conn = sqlite3.connect(db_file)
    return conn

def create_tables(conn):
    """
    Create tables in the SQLite database.
    """
    cursor = conn.cursor()

    # Voice Table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS voice (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            elevenlabs_voice_id TEXT NOT NULL,
            gender TEXT CHECK(gender IN ('male', 'female')) NOT NULL,
            language_id INTEGER,
            FOREIGN KEY(language_id) REFERENCES language(id),
            UNIQUE(name, gender, language_id)
        )
    ''')

    # Language Table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS language (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            code TEXT NOT NULL UNIQUE
        )
    ''')

    # Name Table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS name (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            gender TEXT CHECK(gender IN ('male', 'female')) NOT NULL,
            language_id INTEGER,
            FOREIGN KEY(language_id) REFERENCES language(id),
            UNIQUE(name, gender, language_id)
        )
    ''')

    # Category Table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS category (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            language_id INTEGER,
            FOREIGN KEY(language_id) REFERENCES language(id),
            UNIQUE(name, language_id)
        )
    ''')

    # Personal Table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS personal (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name_id INTEGER,
            text TEXT,
            type TEXT CHECK(type IN ('greeting', 'morning', 'day', 'evening', 'night')),
            audio_file TEXT,
            FOREIGN KEY(name_id) REFERENCES name(id)
        )
    ''')

    # General Table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS general (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            category_id INTEGER,
            theme_name TEXT,
            topic_name TEXT,
            text TEXT,
            audio_file TEXT,
            symbols INTEGER,
            gender TEXT CHECK(gender IN ('male', 'female')) NOT NULL,
            FOREIGN KEY(category_id) REFERENCES category(id)
        )
    ''')

    conn.commit()

def execute_query(conn, query, params=()):
    """
    Execute a SQL query with optional parameters.
    """
    with closing(conn.cursor()) as cursor:
        cursor.execute(query, params)
        conn.commit()

def fetch_all(conn, query, params=()):
    """
    Fetch all results from a SQL query.
    """
    with closing(conn.cursor()) as cursor:
        cursor.execute(query, params)
        return cursor.fetchall()

def fetch_one(conn, query, params=()):
    """
    Fetch one result from a SQL query.
    """
    with closing(conn.cursor()) as cursor:
        cursor.execute(query, params)
        return cursor.fetchone()
