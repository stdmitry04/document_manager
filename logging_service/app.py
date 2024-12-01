from flask import Flask, request, jsonify
from utils.db_functions import *
from utils.service_calls import *
from functools import wraps

app = Flask(__name__)
create_db()


def auth(f):
    @wraps(f)
    def auth_wrapper(*args, **kwargs):
        jwt_token = request.headers.get('Authorization')
        if not jwt_token:
            return jsonify({'status': 2})

        is_valid, username = verify_jwt(jwt_token)
        if not is_valid:
            return jsonify({'status': 2})

        return f(username, *args, **kwargs)

    return auth_wrapper


@app.route('/log', methods=['POST'])
def log():
    """Log an event"""
    if request.is_json:
        data = request.get_json()
    else:
        data = request.form

    event = data.get('event')
    username = data.get('username')
    filename = data.get('filename')

    if not event or not username:
        return jsonify({'status': 2})

    with get_db_connection() as conn:
        cursor = conn.cursor()
        add_log(cursor, event, username, filename)
        return jsonify({'status': 1})


@app.route('/view_log', methods=['GET'])
@auth
def view_log(requesting_username):
    """View logs for a username or filename"""
    # Get query parameters
    username = request.args.get('username')
    filename = request.args.get('filename')
    print(username,requesting_username)

    with get_db_connection() as conn:
        cursor = conn.cursor()

        if username:
            print('went to username')
            # User can only view their own logs
            if username != requesting_username:
                return jsonify({'status': 3, 'data': 'NULL'})
            logs = get_logs_by_username(cursor, username)

        elif filename:
            print('went to filename')
            # User must have access to document to view its logs
            if not can_view_document(requesting_username, filename):
                return jsonify({'status': 3, 'data': 'NULL'})
            logs = get_logs_by_filename(cursor, filename)

        else:
            return jsonify({'status': 2, 'data': 'NULL'})

        return jsonify({
            'status': 1,
            'data': logs
        })


@app.route('/get_modifications', methods=['GET'])
def get_modifications():
    """Get document modification info for search service"""
    filename = request.args.get('filename')
    if not filename:
        return jsonify({'status': 2})

    with get_db_connection() as conn:
        cursor = conn.cursor()
        mod_info = get_document_modifications(cursor, filename)
        if not mod_info:
            return jsonify({'status': 2})

        return jsonify({
            'status': 1,
            **mod_info
        })


@app.route('/clear', methods=['GET'])
def clear():
    """Clear the database"""
    create_db()
    return "Database cleared"


if __name__ == "__main__":
    create_db()  # Ensure database exists on startup
    app.run(host='0.0.0.0', port=9003)
