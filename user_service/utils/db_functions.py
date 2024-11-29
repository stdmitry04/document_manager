import sqlite3

db_name = "database/user.db"
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


def create_user_insert(cursor, first_name, last_name, username, email_address, user_group, salt):
    """Insert a new user"""
    cursor.execute("""INSERT INTO users (first_name, last_name, username, email_address, user_group, salt) 
                      VALUES (?, ?, ?, ?, ?, ?)""",
                   (first_name, last_name, username, email_address, user_group, salt))
    cursor.connection.commit()


def password_insert(cursor, user_id, hashed_password):
    """Insert a new password"""
    cursor.execute("""INSERT INTO passwords (user_id, password_hash) 
                      VALUES (?, ?)""",
                   (user_id, hashed_password))
    cursor.connection.commit()


def get_user_info(cursor, username):
    """Get user info for login"""
    cursor.execute("""SELECT u.id, u.username, p.password_hash, u.salt 
                      FROM users u 
                      JOIN passwords p ON u.id = p.user_id 
                      WHERE u.username = ?
                      ORDER BY p.id DESC
                      LIMIT 1""", (username,))
    return cursor.fetchone()