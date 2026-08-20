# game/auth/auth_manager.py - Secure password hashing and verification

import hashlib
import os
import secrets

def generate_salt():
    """Generates a secure cryptographically strong random salt string."""
    return secrets.token_hex(16)

def hash_password(password, salt):
    """Hashes a password with a unique salt using SHA-256."""
    salted = (password + salt).encode('utf-8')
    return hashlib.sha256(salted).hexdigest()

def verify_password(password, stored_hash, salt):
    """Verifies a password against the stored hash and salt."""
    calc_hash = hash_password(password, salt)
    return secrets.compare_digest(stored_hash, calc_hash)
