# game/auth/validators.py - Input validators for user registration forms

import re

def validate_name(name):
    """Validates name input."""
    if not name:
        return "Name is required."
    trimmed = name.strip()
    if len(trimmed) < 2:
        return "Name must be at least 2 characters."
    if len(trimmed) > 30:
        return "Name is too long."
    return None

def validate_email(email):
    """Validates email format."""
    if not email:
        return "Email is required."
    trimmed = email.strip().lower()
    # Simple RFC 5322 regex
    pattern = r'^[^@\s]+@[^@\s]+\.[^@\s]+$'
    if not re.match(pattern, trimmed):
        return "Invalid email address format."
    return None

def validate_password(password, confirm_password):
    """Validates password policy and match."""
    if not password:
        return "Password is required."
    if len(password) < 6:
        return "Password must be at least 6 characters."
    if password != confirm_password:
        return "Passwords do not match."
    return None
