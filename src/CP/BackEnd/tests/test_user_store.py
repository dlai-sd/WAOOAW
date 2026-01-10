"""
Tests for user store
"""

import pytest

from datetime import datetime

from api.auth.user_store import UserStore, get_user_store
from models.user import UserCreate


pytestmark = pytest.mark.unit


def test_create_user():
    """Test creating a new user"""
    store = UserStore()
    user_data = UserCreate(
        email="test@example.com",
        name="Test User",
        picture="https://example.com/pic.jpg",
        provider="google",
        provider_id="google123"
    )
    
    user = store.create_user(user_data)
    
    assert user.id is not None
    assert user.email == "test@example.com"
    assert user.name == "Test User"
    assert user.picture == "https://example.com/pic.jpg"
    assert user.provider == "google"
    assert user.provider_id == "google123"
    assert isinstance(user.created_at, datetime)
    assert isinstance(user.last_login_at, datetime)


def test_get_user_by_id():
    """Test getting user by ID"""
    store = UserStore()
    user_data = UserCreate(
        email="test@example.com",
        name="Test User",
        provider="google",
        provider_id="google123"
    )
    created_user = store.create_user(user_data)
    
    # Get by ID
    user = store.get_user_by_id(created_user.id)
    
    assert user is not None
    assert user.id == created_user.id
    assert user.email == created_user.email


def test_get_user_by_id_not_found():
    """Test getting non-existent user by ID"""
    store = UserStore()
    user = store.get_user_by_id("nonexistent-id")
    assert user is None


def test_get_user_by_email():
    """Test getting user by email"""
    store = UserStore()
    user_data = UserCreate(
        email="test@example.com",
        name="Test User",
        provider="google",
        provider_id="google123"
    )
    created_user = store.create_user(user_data)
    
    # Get by email
    user = store.get_user_by_email("test@example.com")
    
    assert user is not None
    assert user.email == "test@example.com"
    assert user.id == created_user.id


def test_get_user_by_email_not_found():
    """Test getting non-existent user by email"""
    store = UserStore()
    user = store.get_user_by_email("nonexistent@example.com")
    assert user is None


def test_get_user_by_provider():
    """Test getting user by provider"""
    store = UserStore()
    user_data = UserCreate(
        email="test@example.com",
        name="Test User",
        provider="google",
        provider_id="google123"
    )
    created_user = store.create_user(user_data)
    
    # Get by provider
    user = store.get_user_by_provider("google", "google123")
    
    assert user is not None
    assert user.provider == "google"
    assert user.provider_id == "google123"
    assert user.id == created_user.id


def test_get_user_by_provider_not_found():
    """Test getting non-existent user by provider"""
    store = UserStore()
    user = store.get_user_by_provider("google", "nonexistent123")
    assert user is None


def test_update_last_login():
    """Test updating last login timestamp"""
    store = UserStore()
    user_data = UserCreate(
        email="test@example.com",
        name="Test User",
        provider="google",
        provider_id="google123"
    )
    user = store.create_user(user_data)
    
    original_login = user.last_login_at
    
    # Wait a tiny bit and update
    import time
    time.sleep(0.01)
    
    store.update_last_login(user.id)
    
    # Get updated user
    updated_user = store.get_user_by_id(user.id)
    
    assert updated_user.last_login_at > original_login


def test_update_last_login_nonexistent_user():
    """Test updating last login for non-existent user"""
    store = UserStore()
    # Should not raise exception
    store.update_last_login("nonexistent-id")


def test_get_or_create_user_creates_new():
    """Test get_or_create creates new user when not found"""
    store = UserStore()
    user_data = UserCreate(
        email="test@example.com",
        name="Test User",
        provider="google",
        provider_id="google123"
    )
    
    user = store.get_or_create_user(user_data)
    
    assert user.email == "test@example.com"
    assert user.id is not None


def test_get_or_create_user_finds_by_provider():
    """Test get_or_create finds existing user by provider"""
    store = UserStore()
    user_data = UserCreate(
        email="test@example.com",
        name="Test User",
        provider="google",
        provider_id="google123"
    )
    
    # Create user
    original_user = store.create_user(user_data)
    original_login = original_user.last_login_at
    
    # Wait and get_or_create
    import time
    time.sleep(0.01)
    
    user = store.get_or_create_user(user_data)
    
    # Should be same user
    assert user.id == original_user.id
    # Last login should be updated
    assert user.last_login_at > original_login


def test_get_or_create_user_finds_by_email():
    """Test get_or_create finds existing user by email"""
    store = UserStore()
    
    # Create user with one provider
    user_data1 = UserCreate(
        email="test@example.com",
        name="Test User",
        provider="google",
        provider_id="google123"
    )
    original_user = store.create_user(user_data1)
    
    # Try to get_or_create with different provider but same email
    user_data2 = UserCreate(
        email="test@example.com",
        name="Test User",
        provider="github",
        provider_id="github456"
    )
    
    user = store.get_or_create_user(user_data2)
    
    # Should be same user
    assert user.id == original_user.id


def test_get_user_store_singleton():
    """Test get_user_store returns singleton"""
    store1 = get_user_store()
    store2 = get_user_store()
    
    assert store1 is store2
