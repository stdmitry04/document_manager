import json
import base64
import hmac
import hashlib


def generate_jwt(username, moderator):
    """Generates a JWT for the logged-in user using HMAC SHA-256"""

    with open("key.txt", "r") as key_file:
        secret_key = key_file.read().strip()

    header = json.dumps({"alg": "HS256", "typ": "JWT"}).encode('utf-8')

    payload = {
        "username": username,
        "access": "True"
    }
    # print(moderator, type(moderator))
    if moderator == 'True':
        payload["moderator"] = "True"

    # print(payload)

    payload_b64 = base64.urlsafe_b64encode(json.dumps(payload).encode('utf-8')).decode('utf-8')
    header_b64 = base64.urlsafe_b64encode(header).decode('utf-8')
    message = f"{header_b64}.{payload_b64}"
    signature = hmac.new(secret_key.encode('utf-8'), message.encode('utf-8'), hashlib.sha256).hexdigest()
    jwt_token = f"{message}.{signature}"
    return jwt_token
