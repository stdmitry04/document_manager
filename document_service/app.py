from flask import Flask, request, jsonify
from utils.db_functions import *
import os
import json
import requests
from functools import wraps
import hashlib
# from utils.jwt_validation import *
from utils.service_calls import *

app = Flask(__name__)
create_db()

DOCS_DIR = 'documents'


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


@app.route('/create_document', methods=['POST'])
@auth
def create_document(username):
    """Create a new document"""
    if request.is_json:
        data = request.get_json()
    else:
        data = request.form

    try:
        filename = data.get('filename')
        body = data.get('body')
        groups = json.loads(data.get('groups'))

        # create the document
        file_path = os.path.join(DOCS_DIR, filename)
        with open(file_path, 'w', newline='\n') as f:
            f.write(body)

        # save document data to db
        with get_db_connection() as conn:
            cursor = conn.cursor()
            doc_id = insert_document(cursor, filename, username)

            # store document groups
            for group in groups.values():
                insert_group(cursor, doc_id, group)

        return jsonify({"status": 1})
    except Exception as e:
        print(f"Error creating document: {e}")
        return jsonify({"status": 2})


@app.route('/edit_document', methods=['POST'])
@auth
def edit_document(username):
    """Edit the document"""
    if request.is_json:
        data = request.get_json()
    else:
        data = request.form

    try:
        filename = data.get('filename')
        body = data.get('body')

        # check if the user is authorized with endpoint from user service
        response = requests.get(f"http://users-service:9000/check_group/", )
        if response.status_code != 200 or not response.json().get("authorized"):
            return jsonify({"status": 3})

        # append to the document
        file_path = os.path.join(DOCS_DIR, filename)
        with open(file_path, 'a', newline='\n') as f:
            f.write(body)

        # hash the file
        with open(f"documents/{filename}", 'rb') as f:
            new_hash = hashlib.sha256(f.read()).hexdigest()

        with get_db_connection() as conn:
            cursor = conn.cursor()
            # update metadata
            success = update_document(cursor, filename, username, new_hash)

        return jsonify({'status': 1 if success else 2})
    except Exception as e:
        print(f"Error editing document: {e}")
        return jsonify({"status": 2})


@app.route('/get_document_info', methods=['GET'])
def get_document_info():
    """Get document metadata - used by search service"""
    filename = request.args.get('filename')
    if not filename:
        return jsonify({'status': 2})

    with get_db_connection() as conn:
        cursor = conn.cursor()
        doc_info = get_document_metadata(cursor, filename)
    if not doc_info:
        return jsonify({'status': 2})

    return jsonify({
        'status': 1,
        'owner': doc_info['owner'],
        'last_mod': doc_info['last_modified_by'],
        'total_mod': doc_info['total_modifications'],
        'hash': doc_info['file_hash'],
        'groups': doc_info['groups']
    })


@app.route('/clear', methods=['GET'])
def clear():
    """Clear the database"""
    print("Received request to clear database")
    create_db()
    print("Database cleared")
    return "Database cleared"


if __name__ == "__main__":
    create_db()
    app.run(host='0.0.0.0', port=9001)
