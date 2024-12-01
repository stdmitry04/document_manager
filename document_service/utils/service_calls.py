import requests

USER_SERVICE = "http://localhost:9000"


def verify_jwt(jwt_token):
    """Verify JWT"""
    try:
        response = requests.get(f"{USER_SERVICE}/verify_jwt", headers={'Authorization': jwt_token})
        result = response.json()
        return result['status'] == 1, result.get('username')
    except:
        return False, None


def get_user_group(username):
    """Get user's group"""
    try:
        response = requests.get(f"{USER_SERVICE}/get_user_group", params={'username': username})
        result = response.json()
        if result['status'] == 1:
            return result['group']
        return None
    except:
        return None
