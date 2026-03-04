"""
In-memory user store (replace with database in production)
"""

import uuid
from datetime import datetime
from typing import Dict, Optional

from models.user import User, UserCreate


class UserStore:
    """Simple in-memory user storage"""

    def __init__(self):
        self._users: Dict[str, User] = {}
        self._email_index: Dict[str, str] = {}  # email -> user_id
        self._provider_index: Dict[str, str] = {}  # provider:provider_id -> user_id

    def create_user(self, user_data: UserCreate) -> User:
        """Create a new user"""
        user_id = str(uuid.uuid4())

        user = User(
            id=user_id,
            email=user_data.email,
            name=user_data.name,
            picture=user_data.picture,
            provider=user_data.provider,
            provider_id=user_data.provider_id,
            created_at=datetime.utcnow(),
            last_login_at=datetime.utcnow(),
        )

        self._users[user_id] = user
        self._email_index[user_data.email] = user_id
        provider_key = f"{user_data.provider}:{user_data.provider_id}"
        self._provider_index[provider_key] = user_id

        return user

    def get_user_by_id(self, user_id: str) -> Optional[User]:
        """Get user by ID"""
        return self._users.get(user_id)

    def get_user_by_email(self, email: str) -> Optional[User]:
        """Get user by email"""
        user_id = self._email_index.get(email)
        if user_id:
            return self._users.get(user_id)
        return None

    def get_user_by_provider(self, provider: str, provider_id: str) -> Optional[User]:
        """Get user by provider and provider ID"""
        provider_key = f"{provider}:{provider_id}"
        user_id = self._provider_index.get(provider_key)
        if user_id:
            return self._users.get(user_id)
        return None

    def alias_user_id(self, user: User, alias_id: str) -> None:
        """Register *alias_id* as a secondary key for *user*.

        Used when an external stable UUID (e.g. Plant's customer_id) must be
        resolvable via get_user_by_id() even though the user was originally
        created with a different in-memory UUID.  Idempotent: calling twice
        with the same alias is safe.
        """
        if alias_id and alias_id not in self._users:
            self._users[alias_id] = user

    def update_last_login(self, user_id: str):
        """Update user's last login timestamp"""
        user = self._users.get(user_id)
        if user:
            user.last_login_at = datetime.utcnow()

    def update_profile(self, user_id: str, updates: dict) -> "User | None":
        """Update profile fields for a user and return the updated User."""
        user = self._users.get(user_id)
        if not user:
            return None
        updated = user.model_copy(update=updates)
        self._users[user_id] = updated
        return updated

    def get_or_create_user(self, user_data: UserCreate) -> User:
        """Get existing user or create new one"""
        # Try to find by provider ID first
        user = self.get_user_by_provider(user_data.provider, user_data.provider_id)

        if not user:
            # Try to find by email
            user = self.get_user_by_email(user_data.email)

        if not user:
            # Create new user
            user = self.create_user(user_data)
        else:
            # Update last login
            self.update_last_login(user.id)

        return user


# Global user store instance
user_store = UserStore()


def get_user_store() -> UserStore:
    """Get user store instance"""
    return user_store
