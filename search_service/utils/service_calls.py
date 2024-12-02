import requests

# USER_SERVICE = "http://localhost:9000"
# DOC_SERVICE = "http://localhost:9001"
# LOG_SERVICE = "http://localhost:9003"
USER_SERVICE = "http://users-service:9000"
DOC_SERVICE = "http://document-service:9001"
LOG_SERVICE = "http://logging-service:9003"


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


def get_document_info(filename):
    """Get document metadata"""
    try:
        response = requests.get(
            f"{DOC_SERVICE}/get_document_info", params={'filename': filename})
        result = response.json()
        print(result)
        return result if result['status'] == 1 else None
    except:
        return None


def log_search(username, filename):
    """Log search event"""
    try:
        requests.post(
            f'{LOG_SERVICE}/log',
            json={
                'event': 'document_search',
                'username': username,
                'filename': filename
            }
        )
    except:
        pass
