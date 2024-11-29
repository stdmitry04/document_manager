import sqlite3

db_name = "project1.db"
sql_file = "project1.sql"


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
    conn.row_factory = sqlite3.Row  # allow row access by column name
    return conn


def get_user_by_username(username):
    """Gets the user by their username from the database."""
    with get_db_connection() as conn:
        cursor = conn.cursor()
        # cursor.execute('SELECT * FROM users WHERE username = ?', (username,))
        cursor.execute("""SELECT u.id, u.first_name, u.last_name, u.username, p.password_hash, u.salt 
                          FROM users u 
                          JOIN passwords p ON u.id = p.user_id 
                          WHERE u.username = ?
                          ORDER BY p.id DESC
                          LIMIT 1""", (username,))
        user = cursor.fetchone()
    return user


def update_username(old_username, new_username):
    """Updates the username in the database."""
    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute('UPDATE users SET username = ? WHERE username = ?',
                       (new_username, old_username))
        conn.commit()


def update_password(username, new_password):
    """Updates the password for the user."""
    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute(
            'UPDATE passwords SET password_hash = ? WHERE user_id = (SELECT id FROM users WHERE username = ?)',
            (new_password, username))
        conn.commit()


def get_previous_passwords(user_id):
    """Retrieve previous password hashes for a user."""
    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("""SELECT password_hash FROM passwords 
                          WHERE user_id = ?""", (user_id,))
        return [row['password_hash'] for row in cursor.fetchall()]


def get_user_data(username):
    """Get user data based on provided username"""
    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("""SELECT username, email_address, first_name, last_name FROM users WHERE username = ?""",
                       (username,))

        try:
            user = cursor.fetchone()
            data = {'username': user['username'],
                    'email_address': user['email_address'],
                    'first_name': user['first_name'],
                    'last_name': user['last_name']
                    }
            return data
        except Exception as e:
            return None


def create_user_insert(cursor, first_name, last_name, username, email_address, moderator, salt):
    cursor.execute("""INSERT INTO users (first_name, last_name, username, email_address, moderator, salt) 
                      VALUES (?, ?, ?, ?, ?, ?)""",
                   (first_name, last_name, username, email_address, moderator, salt))
    cursor.connection.commit()


def password_insert(cursor, user_id, hashed_password):
    cursor.execute("""INSERT INTO passwords (user_id, password_hash) 
                      VALUES (?, ?)""",
                   (user_id, hashed_password))
    cursor.connection.commit()


def get_user_info(cursor, username):
    cursor.execute("""SELECT u.id, u.username, p.password_hash, u.moderator, u.salt 
                      FROM users u 
                      JOIN passwords p ON u.id = p.user_id 
                      WHERE u.username = ?
                      ORDER BY p.id DESC
                      LIMIT 1""", (username,))
    user = cursor.fetchone()
    return user


def post_info_insert(cursor, title, body, post_id):
    cursor.execute("""INSERT INTO posts (title, body, post_id)
                      VALUES (?, ?, ?)""",
                   (title, body, post_id))
    cursor.connection.commit()


def tag_insert(cursor, tag):
    cursor.execute("""INSERT OR IGNORE INTO tags (tag_name)
                      VALUES (?)""", (tag,))
    cursor.connection.commit()


def posts_tags_insert(cursor, post_id, tag_id):
    cursor.execute("INSERT OR IGNORE INTO posts_tagged (post_id, tag_id) VALUES (?, ?)", (post_id, tag_id))
    cursor.connection.commit()


def get_post_by_id(cursor, post_id):
    cursor.execute("SELECT p.title, p.body FROM posts p WHERE p.post_id = ?", (post_id,))
    post = cursor.fetchone()
    return post


def users_posts_insert(cursor, user_id, post_id):
    cursor.execute("INSERT OR IGNORE INTO users_posts (user_id, post_id) VALUES (?, ?)", (user_id, post_id))
    cursor.connection.commit()


def get_post_with_user_id(cursor, user_id, post_id):
    cursor.execute("SELECT user_id, post_id FROM users_posts WHERE user_id = ? AND post_id = ?",
                   (user_id, post_id))
    post = cursor.fetchone()

    return post is not None


def get_post_user_id(cursor, user_id, post_id):
    cursor.execute("SELECT user_id, post_id FROM users_posts WHERE user_id = ? AND post_id = ?",
                   (user_id, post_id))
    post = cursor.fetchone()

    return post


def get_post_tags(cursor, post_id):
    cursor.execute("""SELECT t.tag_name
                      FROM posts_tagged pt
                      JOIN tags t ON pt.tag_id = t.tag_id
                      WHERE pt.post_id = ?;
                      """, (post_id,))
    tags = [tag[0] for tag in cursor.fetchall()]
    return tags


def get_posts_of_followed_users(cursor, followed_users):
    placeholders = ['?'] * len(followed_users)
    placeholders = ', '.join(placeholders)

    cursor.execute("""
        SELECT p.post_id, p.title, p.body, up.user_id
        FROM posts p
        JOIN users_posts up ON p.post_id = up.post_id
        WHERE up.user_id IN ({})
        ORDER BY p.time_created DESC
        LIMIT 5
    """.format(placeholders), tuple(followed_users))

    posts = cursor.fetchall()
    posts_dict = []

    for post in posts:
        post_dict = {
            'post_id': post[0],
            'title': post[1],
            'body': post[2],
            'user_id': post[3]
        }
        posts_dict.append(post_dict)

    return posts_dict


def get_posts_by_tags(cursor, tag_name, followed_users):
    placeholders = ['?'] * len(followed_users)
    placeholders = ', '.join(placeholders)

    cursor.execute("""
        SELECT p.post_id, p.title, p.body, up.user_id
        FROM posts p
        JOIN posts_tagged pt ON p.post_id = pt.post_id
        JOIN tags t ON pt.tag_id = t.tag_id
        JOIN users_posts up ON p.post_id = up.post_id
        WHERE t.tag_name = ? AND up.user_id IN ({})
    """.format(placeholders), (tag_name, *followed_users))

    posts = cursor.fetchall()
    posts_dict = []

    for post in posts:
        post_dict = {
            'post_id': post[0],
            'title': post[1],
            'body': post[2],
            'user_id': post[3]
        }
        posts_dict.append(post_dict)

    return posts_dict


def check_if_follows(cursor, username, username_followed):
    cursor.execute("SELECT * FROM followed_users WHERE follower_user_id = ? AND followed_user_id = ?",
                   (username, username_followed))
    connection = cursor.fetchone()

    return connection is not None


def follow_user(cursor, follower_user_id, followed_user_id):
    cursor.execute("""INSERT INTO followed_users (follower_user_id, followed_user_id)
                      VALUES (?, ?)""", (follower_user_id, followed_user_id))
    cursor.connection.commit()


def get_followed_users(cursor, user_id):
    cursor.execute("""SELECT followed_user_id FROM followed_users WHERE follower_user_id = ?""", (user_id,))

    followed_users = cursor.fetchall()
    followed_user_ids = [user[0] for user in followed_users]
    followed_user_ids.append(user_id)
    return followed_user_ids


def is_post_of_followed_user(cursor, post_id, followed_users):
    placeholders = ['?'] * len(followed_users)
    placeholders = ', '.join(placeholders)

    cursor.execute("""SELECT p.post_id FROM posts p JOIN users_posts up ON p.post_id = up.post_id
                      WHERE p.post_id = ?
                      AND up.user_id in ({})""".format(placeholders), (post_id, *followed_users))

    post = cursor.fetchone()
    return True if post else False


def like_post(cursor, user_id, post_id):
    cursor.execute("""INSERT INTO post_likes (user_id, post_id)
                      VALUES (?, ?)""", (user_id, post_id))
    cursor.connection.commit()


def get_post_likes_count(cursor, post_id):
    cursor.execute("""SELECT COUNT(*) AS number_of_likes
                      FROM post_likes WHERE post_id = ?""", (post_id,))
    likes = cursor.fetchone()
    return likes['number_of_likes'] if likes else 0


def delete_user(cursor, user_id):
    cursor.execute("""DELETE FROM users WHERE id = ?""", (user_id,))
    cursor.connection.commit()


def delete_post(cursor, post_id):
    cursor.execute("""DELETE FROM posts WHERE post_id = ?""", (post_id,))
    cursor.connection.commit()


def get_user_username_by_id(cursor, user_id):
    cursor.execute("""SELECT username FROM users WHERE id = ?""", (user_id,))
    user = cursor.fetchone()
    return user['username'] if user else None