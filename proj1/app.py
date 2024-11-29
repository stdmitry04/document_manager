import sqlite3
from flask import Flask, request, jsonify
from helpers.hasher import hash_pass
from helpers.validatate_password import validate_password
from helpers.generate_jwt import generate_jwt
from helpers.jwt_validation import verify_jwt
from helpers.db_functions import *
import json

app = Flask(__name__)

# create the database
create_db()


@app.route('/', methods=['GET'])
def index():
    """Get all users."""
    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM users;")
        result = cursor.fetchall()
    return jsonify([dict(row) for row in result])


@app.route('/create_user', methods=['POST'])
def create_user():
    """Create a new user."""
    if request.is_json:
        data = request.get_json()
    else:
        data = request.form

    first_name = data.get('first_name')
    last_name = data.get('last_name')
    username = data.get('username')
    email_address = data.get('email_address')
    password = data.get('password')
    moderator = data.get('moderator')
    salt = data.get('salt')

    # Check if any field is missing
    if not all(field is not None for field in
               [first_name, last_name, username, email_address, password, moderator, salt]):
        return jsonify({'error': 'All fields are required'})

    # Validate password
    password_error = validate_password(password, username, first_name, last_name)
    if password_error:
        return jsonify({'status': 4, 'pass_hash': 'NULL'})

    hashed_password = hash_pass(password, salt)

    try:
        with get_db_connection() as conn:
            cursor = conn.cursor()

            # insert user info into DB
            create_user_insert(cursor, first_name, last_name, username, email_address, moderator, salt)

            user_id = cursor.lastrowid

            # insert a password into DB
            password_insert(cursor, user_id, hashed_password)

        return jsonify({'status': 1, 'pass_hash': hashed_password})

    except sqlite3.IntegrityError as e:
        error_message = str(e)

        # Handle unique constraint violation for username or email
        if "users.username" in error_message:
            return jsonify({'status': 2, 'pass_hash': 'NULL'})
        elif "users.email_address" in error_message:
            return jsonify({'status': 3, 'pass_hash': 'NULL'})


@app.route('/login', methods=['POST'])
def login_user():
    """Log in a user."""
    if request.is_json:
        data = request.json
        username = data.get('username')
        password = data.get('password')
    else:
        username = request.form.get('username')
        password = request.form.get('password')

    if not username or not password:
        return jsonify({'status': 2, 'message': 'Username and password are required'})

    with get_db_connection() as conn:
        cursor = conn.cursor()

        # retrieve user info
        user = get_user_info(cursor, username)

    if not user:
        return jsonify({'status': 2, 'jwt': 'NULL'})

    user_id, db_username, db_password_hash, moderator, db_salt = user

    # Hash the provided password with the salt stored in the database
    hashed_password = hash_pass(password, db_salt)

    # Compare the hashed password with the stored hash
    if hashed_password == db_password_hash:
        # Successful login, generate a JWT
        jwt_token = generate_jwt(username, moderator)
        return jsonify({'status': 1, 'jwt': jwt_token})
    else:
        return jsonify({'status': 2, 'jwt': 'NULL'})


@app.route('/update', methods=['POST'])
def update_user():
    """Update user information (username or password)."""
    if request.is_json:
        data = request.get_json()
    else:
        data = request.form

    old_username = data.get('username')
    new_username = data.get('new_username')
    old_password = data.get('password')
    new_password = data.get('new_password')
    jwt_token = data.get('jwt')

    username_jwt, is_moderator = verify_jwt(jwt_token)
    if username_jwt != old_username:
        return jsonify({"status": 3})  # JWT authorization failed

    user = get_user_by_username(old_username)

    if not user:
        return jsonify({"status": 2})  # incorrect username/password

    if new_username:
        if old_username != username_jwt:
            return jsonify({"status": 2})

        update_username(old_username, new_username)
        return jsonify({"status": 1})

    elif new_password:
        salt = user['salt']
        hashed_password = hash_pass(old_password, salt)
        if hashed_password != user['password_hash']:
            return jsonify({"status": 2})

        password_error = validate_password(new_password, user['username'], user['first_name'], user['last_name'])
        if password_error:
            return jsonify({'status': 2})  # Status code 2 for invalid password

        previous_passwords = get_previous_passwords(user['id'])
        new_hashed_password = hash_pass(new_password, salt)

        if new_hashed_password in previous_passwords:
            return jsonify({"status": 2})  # Can't use old password

        update_password(old_username, hash_pass(new_password, salt))  # Hash the new password
        return jsonify({"status": 1})

    return jsonify({"status": 2})  # Invalid input: new password or new username were not given


@app.route('/view', methods=['POST'])
def view():
    if request.is_json:
        data = request.get_json()
    else:
        data = request.form

    jwt = data["jwt"]
    username, is_moderator = verify_jwt(jwt)
    data = get_user_data(username)
    if data is not None:
        return jsonify({'status': 1, 'data': data})
    else:
        return jsonify({'status': 2, 'data': 'NULL'})


@app.route('/clear', methods=['GET'])
def clear():
    create_db()
    return "Database cleared"


@app.route('/create_post', methods=['POST'])
def create_post():
    token = request.headers.get('Authorization')
    if token:
        result = verify_jwt(token)
        if result:
            username, is_moderator = result
            if username is None or is_moderator is None:
                return jsonify({'status': 2})
        else:
            return jsonify({'status': 2})
    else:
        return jsonify({'status': 2})

    title = request.form.get('title')
    body = request.form.get('body')
    post_id = request.form.get('post_id')
    tags = request.form.get('tags')

    if not title or not body or not post_id:
        return jsonify({'status': 2})

    with get_db_connection() as conn:
        cursor = conn.cursor()

        # retrieve user info to get his id
        user_info = get_user_info(cursor, username)
        if not user_info:
            return jsonify({'status': 2})

        # insert a post with relation to its creator
        users_posts_insert(cursor, user_info['id'], post_id)

        # insert post info into db
        post_info_insert(cursor, title, body, post_id)

        if tags:
            tags_dict = json.loads(tags)
            for tag_key, tag_value in tags_dict.items():
                # insert the tag if it doesn't exist and get the id of it
                cursor.execute("SELECT tag_id FROM tags WHERE tag_name = ?", (tag_value,))
                tag_result = cursor.fetchone()

                if tag_result:
                    tag_id = tag_result[0]
                else:
                    tag_insert(cursor, tag_value)
                    cursor.execute("SELECT tag_id FROM tags WHERE tag_name = ?", (tag_value,))
                    tag_id = cursor.fetchone()[0]

                # like tag to post
                posts_tags_insert(cursor, post_id, tag_id)

    return jsonify({'status': 1})  # success


@app.route('/view_post/<post_id>', methods=['GET'])
def view_post(post_id):
    token = request.headers.get('Authorization')
    if not token:
        return jsonify({'status': 2, "data": 'NULL'})
    result = verify_jwt(token)
    if not result:
        return jsonify({'status': 2, "data": 'NULL'})

    username, is_moderator = result
    request_fields = request.args.to_dict()

    with get_db_connection() as conn:
        cursor = conn.cursor()

        # retrieve user info
        user_info = get_user_info(cursor, username)
        if not user_info:
            return jsonify({'status': 2, "data": 'NULL'})

        # retrieve post info
        post = get_post_by_id(cursor, post_id)
        if not post:
            return jsonify({'status': 2, "data": 'NULL'})

        # retrieve post id - user id relationship
        post_to_user_relation = get_post_user_id(cursor, user_info['id'], post_id)
        if not post_to_user_relation:
            # get followed users if post is not of the user's
            followed_users = get_followed_users(cursor, user_info['id'])

            # retrieve post owner's user_id
            cursor.execute("""
                SELECT user_id 
                FROM users_posts 
                WHERE post_id = ?
            """, (post_id,))
            post_owner = cursor.fetchone()

            if not post_owner or post_owner['user_id'] not in followed_users:
                return jsonify({'status': 2, "data": 'NULL'})

        response_data = {}

        if request_fields.get('title'):
            response_data['title'] = post['title']

        if request_fields.get('body'):
            response_data['body'] = post['body']

        if request_fields.get('tags'):
            response_data['tags'] = get_post_tags(cursor, post_id)

        if request_fields.get('owner'):
            # retrieve post owner's username
            cursor.execute("""
                SELECT u.username 
                FROM users u 
                JOIN users_posts up ON u.id = up.user_id 
                WHERE up.post_id = ?
            """, (post_id,))
            owner = cursor.fetchone()
            response_data['owner'] = owner['username'] if owner else None

        if request_fields.get('likes'):
            response_data['likes'] = get_post_likes_count(cursor, post_id)

        return jsonify({'status': 1, 'data': response_data})


@app.route('/search', methods=['GET'])
def post_search():
    token = request.headers.get('Authorization')
    if token:
        result = verify_jwt(token)
        if result:
            username, is_moderator = result
        else:
            return jsonify({'status': 2, "data": 'NULL'})
    else:
        return jsonify({'status': 2, "data": 'NULL'})

    request_fields = request.args.to_dict()
    feed = request_fields.get('feed') or request.form.get('feed')
    tag = request_fields.get('tag') or request.form.get('tag')
    # feed = request.form.get('feed')
    # tag = request.form.get('tag')
    # print(feed, tag)

    with get_db_connection() as conn:
        cursor = conn.cursor()

        user_info = get_user_info(cursor, username)
        followed_users = get_followed_users(cursor, user_info['id'])

        posts = None

        if feed is not None:
            # get the 5 most recent posts from the users the requester follows
            posts = get_posts_of_followed_users(cursor, followed_users)

        elif tag is not None:
            # get posts with specific tag from followed users
            posts = get_posts_by_tags(cursor, tag, followed_users)

        # format the data for the response
        response_data = {}
        for post in posts:
            response_data[post['post_id']] = {
                'title': post['title'],
                'body': post['body'],
                'tags': get_post_tags(cursor, post['post_id']),
                'owner': get_user_username_by_id(cursor, post['user_id']),
                'likes': get_post_likes_count(cursor, post['post_id']),
            }

        return jsonify({'status': 1, 'data': response_data})


@app.route('/like', methods=['POST'])
def like():
    token = request.headers.get('Authorization')
    if token:
        result = verify_jwt(token)
        if result:
            username, is_moderator = result
        else:
            return jsonify({'status': 2})
    else:
        return jsonify({'status': 2})

    # get post_id from the request
    post_id = request.form.get('post_id')
    if not post_id:
        # return jsonify({'status': 2})
        return jsonify({'status': 2, 'error': 'post id error'})

    with get_db_connection() as conn:
        cursor = conn.cursor()

        user_id = get_user_info(cursor, username)['id']
        # retrieve followed users
        followed_users = get_followed_users(cursor, user_id)

        # check if the post is of followed users
        post_belongs_to_followed_users = is_post_of_followed_user(cursor, post_id, followed_users)
        if not post_belongs_to_followed_users:
            # return jsonify({'status': 2})
            return jsonify({'status': 2, 'error': 'post does not belong '})

        # like the post
        like_post(cursor, user_id, post_id)
        return jsonify({'status': 1})


@app.route('/follow', methods=['POST'])
def follow():
    token = request.headers.get('Authorization')
    if token:
        result = verify_jwt(token)
        if result:
            username, is_moderator = result
        else:
            return jsonify({'status': 2})
    else:
        return jsonify({'status': 2})

    # retrieve user's username
    username_to_follow = request.form.get('username')
    if not username_to_follow:
        return jsonify({'status': 2})

    with get_db_connection() as conn:
        cursor = conn.cursor()

        follower = get_user_info(cursor, username)['id']
        followed = get_user_info(cursor, username_to_follow)
        if not followed:
            return jsonify({'status': 2})
        else:
            followed = get_user_info(cursor, username_to_follow)['id']

        # check if there is already a connection
        already_follows = check_if_follows(cursor, follower, followed)
        if already_follows:
            return jsonify({'status': 2})

        # follow a requested user
        follow_user(cursor, follower, followed)

    return jsonify({'status': 1})


@app.route('/delete', methods=['POST'])
def delete():
    token = request.headers.get('Authorization')
    if token:
        username, is_moderator = verify_jwt(token)
        if not username:
            return jsonify({'status': 2})
    else:
        return jsonify({'status': 2})

    # request_fields = request.args.to_dict()
    # username_delete = request_fields.get('username')
    # post_id = request_fields.get('post_id')
    if request.is_json:
        data = request.get_json()
    else:
        data = request.form

    username_delete = data.get('username')
    post_id = data.get('post_id')

    if not username_delete and not post_id:
        return jsonify({'status': 2})

    with get_db_connection() as conn:
        cursor = conn.cursor()

        if username_delete:
            if username != username_delete:
                print('case 1')
                return jsonify({'status': 2})  # user can only delete his account

            user = get_user_info(cursor, username)
            if not user:
                print('case 2')
                return jsonify({'status': 2})

            # delete user
            delete_user(cursor, user['id'])

            return jsonify({'status': 1})

        elif post_id:

            user = get_user_info(cursor, username)
            if not user:
                print('case 3')
                return jsonify({'status': 2})

            post_user_relationship = get_post_user_id(cursor, user['id'], post_id)
            if not post_user_relationship:
                print('case 4')
                return jsonify({'status': 2})  # failed to fetch a post with a corresponding owner id

            if post_user_relationship['user_id'] != user['id'] and not is_moderator:
                print('case 5')
                return jsonify({'status': 2})  # post does not belong to the user

            # retrieve a post by post_id
            post = get_post_by_id(cursor, post_id)

            if not post:
                print('case 6')
                return jsonify({'status': 2})  # post does not exist

            # delete the post
            delete_post(cursor, post_id)

            return jsonify({'status': 1})  # Post deleted successfully


# @app.route('/exists', methods=['GET'])
# def check_exists():
#     if request.is_json:
#         data = request.get_json()
#     else:
#         data = request.form
#
#     username = data.get('username')
#     post_id = data.get('post_id')
#
#     with get_db_connection() as conn:
#         cursor = conn.cursor()
#
#         if username:
#             cursor.execute("SELECT * FROM users WHERE username = ?", (username,))
#             row = cursor.fetchone()
#             exists = bool(row)
#         elif post_id:
#             cursor.execute("SELECT * FROM posts WHERE post_id = ?", (post_id,))
#             row = cursor.fetchone()
#             exists = bool(row)
#         else:
#             exists = False
#
#         return jsonify({'exists': exists})

if __name__ == '__main__':
    app.run(debug=True)
