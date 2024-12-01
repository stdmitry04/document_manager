import requests

USER_SERVICE = "http://localhost:9000"
DOC_SERVICE = "http://localhost:9001"


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
        response = requests.get(
            f"{USER_SERVICE}/get_user_group", params={'username': username})
        result = response.json()
        return result.get('group') if result['status'] == 1 else None
    except:
        return None


def can_view_document(username, filename):
    """Check if the user can view document logs"""
    try:
        user_group = get_user_group(username)
        if not user_group:
            return False

        response = requests.get(
            f"{DOC_SERVICE}/get_document_info", params={'filename': filename})
        doc_info = response.json()
        return user_group in doc_info.get('groups', [])
    except:
        return False