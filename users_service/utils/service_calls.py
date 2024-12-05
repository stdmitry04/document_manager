import requests


LOG_SERVICE = "http://logging-service:9003"


def log_user_creation(username):
    """Log search event"""
    try:
        requests.post(
            f'{LOG_SERVICE}/log',
            json={
                'event': 'user_creation',
                'username': username,
                'filename': 'NULL'
            }
        )
    except:
        pass


def log_user_login(username):
    """Log search event"""
    try:
        requests.post(
            f'{LOG_SERVICE}/log',
            json={
                'event': 'login',
                'username': username,
                'filename': 'NULL'
            }
        )
    except:
        pass