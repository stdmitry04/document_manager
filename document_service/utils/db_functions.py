import sqlite3
from datetime import datetime

db_name = "database/documents.db"
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


def insert_document(cursor, filename, username, file_hash):
    cursor.execute('INSERT INTO documents (filename, owner, file_hash, last_modified_by)'
                   'VALUES (?, ?, ?, ?)',
                   (filename, username, file_hash, username))
    cursor.connection.commit()
    doc_id = cursor.lastrowid
    return doc_id


def insert_group(cursor, doc_id, group):
    cursor.execute('INSERT INTO document_groups (document_id, group_name) VALUES (?,?)', (doc_id, group))
    cursor.connection.commit()


def get_allowed_groups(cursor, filename):
    cursor.execute('''
        SELECT dg.group_name 
        FROM documents d
        JOIN document_groups dg ON d.id = dg.document_id
        WHERE d.filename = ?
    ''', (filename,))
    allowed_groups = [row[0] for row in cursor.fetchall()]
    return allowed_groups


def get_document_metadata(cursor, filename):
    """Get document metadata and groups"""
    cursor.execute("""
        SELECT d.*, GROUP_CONCAT(dg.group_name) as groups
        FROM documents d
        LEFT JOIN document_groups dg ON d.id = dg.document_id
        WHERE d.filename = ?
        GROUP BY d.id
    """, (filename,))

    doc = cursor.fetchone()
    if doc:
        return {
            'filename': doc['filename'],
            'owner': doc['owner'],
            'file_hash': doc['file_hash'],
            'last_modified_by': doc['last_modified_by'],
            'total_modifications': doc['total_modifications'],
            'groups': doc['groups'].split(',') if doc['groups'] else []
        }
    return None


def update_document(cursor, filename, modifier, new_hash):
    """Update document metadata"""
    cursor.execute("""
        UPDATE documents 
        SET file_hash = ?, 
            last_modified_by = ?,
            last_modified_at = ?,
            total_modifications = total_modifications + 1
        WHERE filename = ?
    """, (new_hash, modifier, datetime.now(), filename))
    cursor.connection.commit()
    return cursor.rowcount > 0
