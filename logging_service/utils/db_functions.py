import sqlite3
from datetime import datetime


db_name = "database/logs.db"
sql_file = "database/init_db.sql"


def create_db():
    """Create the database and tables from an SQL file."""
    with sqlite3.connect(db_name) as conn:
        with open(sql_file, 'r') as sql_startup:
            init_db = sql_startup.read()
        cursor = conn.cursor()
        cursor.executescript(init_db)
        conn.commit()


def get_db_connection():
    """Create a new database connection."""
    conn = sqlite3.connect(db_name)
    conn.row_factory = sqlite3.Row
    return conn


def add_log(cursor, event, username, filename=None):
    """Add a new log"""
    cursor.execute("""
        INSERT INTO logs (event, username, filename, timestamp)
        VALUES (?, ?, ?, ?)
    """, (event, username, filename, datetime.now()))
    cursor.connection.commit()


def get_logs_by_username(cursor, username):
    """Get all logs for a corresponding username"""
    cursor.execute("""
        SELECT id, event, username, filename
        FROM logs
        WHERE username = ?
        ORDER BY timestamp ASC
    """, (username,))
    logs = cursor.fetchall()

    return {
        i + 1: {
            'event': log['event'],
            'user': log['username'],
            'filename': log['filename'] or 'NULL'
        }
        for i, log in enumerate(logs)
    }


def get_logs_by_filename(cursor, filename):
    """Get all logs for a corresponding filename"""
    cursor.execute("""
        SELECT id, event, username, filename
        FROM logs
        WHERE filename = ?
        ORDER BY timestamp ASC
    """, (filename,))
    logs = cursor.fetchall()

    return {
        i + 1: {
            'event': log['event'],
            'user': log['username'],
            'filename': log['filename']
        }
        for i, log in enumerate(logs)
    }


def get_document_modifications(cursor, filename):
    """Get modification information for a document"""
    # get total modifications
    cursor.execute("""
        SELECT COUNT(*) as total_mods
        FROM logs
        WHERE filename = ? 
        AND event IN ('document_creation', 'document_edit')
    """, (filename,))
    total_mods = cursor.fetchone()['total_mods']

    # get last modifier
    cursor.execute("""
        SELECT username
        FROM logs
        WHERE filename = ?
        AND event IN ('document_creation', 'document_edit')
        ORDER BY timestamp DESC
        LIMIT 1
    """, (filename,))
    last_mod = cursor.fetchone()

    if not last_mod:
        return None

    return {
        'total_modifications': total_mods,
        'last_modifier': last_mod['username']
    }