from flask import Flask, request, jsonify
from utils.service_calls import *
from utils.db_functions import *
from functools import wraps

app = Flask(__name__)
create_db()


def auth(f):
    @wraps(f)
    def auth_wrapper(*args, **kwargs):
        jwt_token = request.headers.get('Authorization')
        if not jwt_token:
            print(jwt_token)
            return jsonify({'status': 2})

        is_valid, username = verify_jwt(jwt_token)
        if not is_valid:
            print(is_valid)
            return jsonify({'status': 2})

        return f(username, *args, **kwargs)

    return auth_wrapper


@app.route('/search', methods=['GET'])
@auth
def search(username):
    """Search endpoint that gets document metadata"""
    filename = request.args.get('filename')
    if not filename:
        return jsonify({'status': 2, 'data': 'NULL'})

    # get the document metadata
    doc_info = get_document_info(filename)
    if not doc_info:
        return jsonify({'status': 2, 'data': 'NULL'})

    # get user's group, check authorization
    user_group = get_user_group(username)
    if not user_group['user_group'] or user_group['user_group'] not in doc_info.get('groups', []):
        return jsonify({'status': 3, 'data': 'NULL'})

    # log the search
    log_search(username, filename)

    return jsonify({
        'status': 1,
        'data': {
            'filename': filename,
            'owner': doc_info['owner'],
            'last_mod': doc_info['last_mod'],
            'total_mod': doc_info['total_mod'],
            'hash': doc_info['hash']
        }
    })


@app.route('/clear', methods=['GET'])
def clear():
    """Clear the database"""
    create_db()
    return "Database cleared"


if __name__ == "__main__":
    app.run(host='0.0.0.0', port=9002)
