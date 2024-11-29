from flask import Flask, request, jsonify
from utils.hasher import hash_pass
from utils.validate_password import validate_password
from utils.generate_jwt import generate_jwt
from utils.db_functions import *

app = Flask(__name__)


@app.route('/clear', methods=['GET'])
def clear():
    """Clear the database"""
    create_db()
    return "Database cleared"


if __name__ == "__main__":
    app.run(host='0.0.0.0', port=9003)
