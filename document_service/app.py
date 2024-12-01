from flask import Flask, request, jsonify
from utils.db_functions import *
from utils.service_calls import *
import os
import json
import requests
from functools import wraps
import hashlib
import shutil

app = Flask(__name__)
create_db()

DOCS_DIR = 'documents'


def reset_docs_directory():
    """
    Resets the documents directory.
    """
    if os.path.exists(DOCS_DIR):
        shutil.rmtree(DOCS_DIR)

    os.makedirs(DOCS_DIR)


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

        # create document
        file_path = os.path.join(DOCS_DIR, filename)
        with open(file_path, 'w', newline='\n') as f:
            f.write(body)

        # calculate hash
        with open(file_path, 'rb') as f:

            file_hash = hashlib.sha256(f.read()).hexdigest()

        # save document information into db
        with get_db_connection() as conn:
            cursor = conn.cursor()
            doc_id = insert_document(cursor, filename, username, file_hash)

            # insert document groups into db
            for group in groups.values():
                insert_group(cursor, doc_id, group)

        log_creation(username, filename)
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

        # get document groups
        with get_db_connection() as conn:
            cursor = conn.cursor()
            doc_info = get_document_metadata(cursor, filename)
            if not doc_info:
                return jsonify({"status": 2})

        user_group = get_user_group(username)
        if not user_group or user_group['user_group'] not in doc_info['groups']:
            return jsonify({"status": 3})

        # append to document
        file_path = os.path.join(DOCS_DIR, filename)
        with open(file_path, 'a', newline='\n') as f:
            f.write(body)

        # calculate new hash
        with open(file_path, 'rb') as f:
            new_hash = hashlib.sha256(f.read()).hexdigest()

        # update metadata
        with get_db_connection() as conn:
            cursor = conn.cursor()
            success = update_document(cursor, filename, username, new_hash)

        if success:
            log_edit(username, filename)
            return jsonify({'status': 1})
        return jsonify({'status': 2})

    except Exception as e:
        print(f"Error editing document: {e}")
        return jsonify({"status": 2})


@app.route('/get_document_info', methods=['GET'])
def get_document_info():
    """Get document metadata"""
    filename = request.args.get('filename')
    if not filename:
        return jsonify({'status': 2})

    with get_db_connection() as conn:
        cursor = conn.cursor()
        # get the document metadata
        doc_info = get_document_metadata(cursor, filename)

        if not doc_info:
            return jsonify({'status': 2})

        # recalculate file hash
        file_path = os.path.join(DOCS_DIR, filename)
        try:
            with open(file_path, 'rb') as f:
                current_hash = hashlib.sha256(f.read()).hexdigest()
                doc_info['file_hash'] = current_hash
        except FileNotFoundError:
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
    """Clear the database and documents directory"""
    create_db()
    reset_docs_directory()
    return "Database and documents cleared"


if __name__ == "__main__":
    app.run(host='0.0.0.0', port=9001)
