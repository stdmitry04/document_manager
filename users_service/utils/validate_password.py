import re


def validate_password(password, username, first_name, last_name):
    if len(password) < 8:
        return "Password must be at least 8 characters long."
    if not re.search(r"[A-Z]", password):
        return "Password must contain at least one uppercase letter."
    if not re.search(r"[a-z]", password):
        return "Password must contain at least one lowercase letter."
    if not re.search(r"[0-9]", password):
        return "Password must contain at least one digit."
    if username in password or first_name in password or last_name in password:
        return "Password cannot contain your username, first name, or last name."
    return None
