import hashlib
from hashlib import sha256


def hash_pass(text, salt):
    text = text + salt
    return sha256(text.encode('utf-8')).hexdigest()


def check_password(text, salt, hashed_pass):
    return hash_pass(text, salt) == hashed_pass
