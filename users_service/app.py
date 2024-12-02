from flask import Flask, request, jsonify
from utils.hasher import hash_pass
from utils.validate_password import validate_password
from utils.generate_jwt import generate_jwt
from utils.db_functions import *
from utils.jwt_validation import *
import sqlite3

app = Flask(__name__)
create_db()


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
    group = data.get('group')
    password = data.get('password')
    salt = data.get('salt')

    # check if any field is missing
    if not all(field is not None for field in [first_name, last_name, username, email_address, group, password, salt]):
        return jsonify({'error': 'All fields are required'})

    # validate password
    password_error = validate_password(password, username, first_name, last_name)
    if password_error:
        return jsonify({'status': 4, 'pass_hash': 'NULL'})

    hashed_password = hash_pass(password, salt)
    try:
        with get_db_connection() as conn:
            cursor = conn.cursor()

            # insert user info into DB
            create_user_insert(cursor, first_name, last_name, username, email_address, group, salt)

            user_id = cursor.lastrowid

            password_insert(cursor, user_id, hashed_password)

        return jsonify({'status': 1, 'pass_hash': hashed_password})

    except sqlite3.IntegrityError as e:
        error_message = str(e)

        # handle unique constraint violation for username or email
        if "users.username" in error_message:
            return jsonify({'status': 2, 'pass_hash': 'NULL'})
        elif "users.email_address" in error_message:
            return jsonify({'status': 3, 'pass_hash': 'NULL'})


@app.route('/login', methods=['POST'])
def login_user():
    """Log in a user."""
    if request.is_json:
        data = request.get_json()
    else:
        data = request.form

    username = data.get('username')
    password = data.get('password')

    if not username or not password:
        return jsonify({'status': 2, 'message': 'Username and password are required'})

    with get_db_connection() as conn:
        cursor = conn.cursor()

        # retrieve user info
        user = get_user_info(cursor, username)

    if not user:
        return jsonify({'status': 2, 'jwt': 'NULL'})

    user_id, db_username, db_password_hash, db_salt = user

    # hash the provided password with the salt stored in the database
    hashed_password = hash_pass(password, db_salt)

    # compare the hashed password with the stored hash
    if hashed_password == db_password_hash:
        jwt_token = generate_jwt(username)
        return jsonify({'status': 1, 'jwt': jwt_token})
    else:
        return jsonify({'status': 2, 'jwt': 'NULL'})


@app.route('/check_group', methods=['POST'])
def check_group():
    if request.is_json:
        data = request.get_json()
    else:
        data = request.form

    username = data.get('username')
    allowed_groups = data.get('groups')

    with get_db_connection() as conn:
        cursor = conn.cursor()

        # fetch the group user belongs to
        group = get_users_group(cursor, username)

        if not group:
            return jsonify({"authorized": False})

        return jsonify({"authorized": group['user_group'] in allowed_groups})


@app.route('/verify_jwt', methods=['GET'])
def verify_jwt_route():
    """Verify JWT"""
    jwt_token = request.headers.get('Authorization')
    if not jwt_token:
        return jsonify({'status': 2, 'username': None})

    try:
        username = verify_jwt(jwt_token)
        if username:
            return jsonify({'status': 1, 'username': username})
        else:
            return jsonify({'status': 2, 'username': None})
    except Exception as e:
        print(f"JWT validation error: {e}")
        return jsonify({'status': 2, 'username': None})


@app.route('/get_user_group', methods=['GET'])
def get_user_group_route():
    username = request.args.get('username')
    if not username:
        return jsonify({'status': 2, 'group': None})

    with get_db_connection() as conn:
        cursor = conn.cursor()
        group = get_users_group(cursor, username)

        if group:
            group_dict = {'user_group': group['user_group']}
            return jsonify({'status': 1, 'group': group_dict})
        return jsonify({'status': 2, 'group': None})


@app.route('/clear', methods=['GET'])
def clear():
    """Clear the database"""
    create_db()
    return "Database cleared"


if __name__ == "__main__":
    app.run(host='0.0.0.0', port=9000)
