from flask import Flask, request, jsonify
from utils.hasher import hash_pass
from utils.validate_password import validate_password
from utils.generate_jwt import generate_jwt
from utils.db_functions import *
import sqlite3

app = Flask(__name__)
create_db()

@app.route('/create_user', methods=['POST'])
def create_user():
    """Create a new user."""
    print("Received request to create user")
    if request.is_json:
        data = request.get_json()
        print("Request data (JSON):", data)
    else:
        data = request.form
        print("Request data (Form):", data)

    first_name = data.get('first_name')
    last_name = data.get('last_name')
    username = data.get('username')
    email_address = data.get('email_address')
    group = data.get('group')
    password = data.get('password')
    salt = data.get('salt')

    # Check if any field is missing
    if not all(field is not None for field in [first_name, last_name, username, email_address, group, password, salt]):
        print("Error: Missing required fields")
        return jsonify({'error': 'All fields are required'})

    # Validate password
    print("Validating password...")
    password_error = validate_password(password, username, first_name, last_name)
    if password_error:
        print("Password validation failed:", password_error)
        return jsonify({'status': 4, 'pass_hash': 'NULL'})

    hashed_password = hash_pass(password, salt)
    print("Generated hashed password:", hashed_password)

    try:
        with get_db_connection() as conn:
            cursor = conn.cursor()

            # Insert user info into DB
            print("Inserting user data into database...")
            create_user_insert(cursor, first_name, last_name, username, email_address, group, salt)

            user_id = cursor.lastrowid
            print("User created with ID:", user_id)

            # Insert a password into DB
            print("Inserting hashed password into database...")
            password_insert(cursor, user_id, hashed_password)

        return jsonify({'status': 1, 'pass_hash': hashed_password})

    except sqlite3.IntegrityError as e:
        error_message = str(e)
        print("Database error:", error_message)

        # Handle unique constraint violation for username or email
        if "users.username" in error_message:
            return jsonify({'status': 2, 'pass_hash': 'NULL'})
        elif "users.email_address" in error_message:
            return jsonify({'status': 3, 'pass_hash': 'NULL'})

@app.route('/login', methods=['POST'])
def login_user():
    """Log in a user."""
    print("Received login request")
    if request.is_json:
        data = request.get_json()
        print("Request data (JSON):", data)
    else:
        data = request.form
        print("Request data (Form):", data)

    username = data.get('username')
    password = data.get('password')

    if not username or not password:
        print("Error: Missing username or password")
        return jsonify({'status': 2, 'message': 'Username and password are required'})

    with get_db_connection() as conn:
        cursor = conn.cursor()

        # Retrieve user info
        print(f"Fetching user info for username: {username}")
        user = get_user_info(cursor, username)

    if not user:
        print("Error: User not found")
        return jsonify({'status': 2, 'jwt': 'NULL'})

    user_id, db_username, db_password_hash, db_salt = user
    print(f"Retrieved user data: {user}")

    # Hash the provided password with the salt stored in the database
    hashed_password = hash_pass(password, db_salt)
    print("Hashed provided password:", hashed_password)

    # Compare the hashed password with the stored hash
    if hashed_password == db_password_hash:
        print("Password match, generating JWT...")
        jwt_token = generate_jwt(username)
        print("Generated JWT:", jwt_token)
        return jsonify({'status': 1, 'jwt': jwt_token})
    else:
        print("Error: Password mismatch")
        return jsonify({'status': 2, 'jwt': 'NULL'})

@app.route('/clear', methods=['GET'])
def clear():
    """Clear the database"""
    print("Received request to clear database")
    create_db()
    print("Database cleared")
    return "Database cleared"

if __name__ == "__main__":
    print("Starting Flask application...")
    app.run(host='0.0.0.0', port=9000, debug=True)
