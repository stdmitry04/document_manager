import base64
import hmac
import hashlib
import json


def verify_jwt(jwt_token):
    try:
        header_b64, payload_b64, signature = jwt_token.split('.')

        with open("key.txt", "r") as key_file:
            secret_key = key_file.read().strip()

        expected_signature = hmac.new(
            secret_key.encode(),
            f"{header_b64}.{payload_b64}".encode(),
            hashlib.sha256
        ).hexdigest()

        payload = base64.urlsafe_b64decode(payload_b64).decode('utf-8')
        payload_data = json.loads(payload)

        if expected_signature != signature:
            return False
        return payload_data.get("username")

    except Exception as e:
        print(f"Error in JWT verification: {e}")
        return False