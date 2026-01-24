"""
Custom exceptions for the application.
"""

class HashingError(Exception):
    """Custom exception for hashing errors."""
    pass

class AuthenticationError(Exception):
    """Custom exception for authentication errors."""
    pass

class UserAlreadyExistsError(Exception):
    """Custom exception for user already exists errors."""
    pass
