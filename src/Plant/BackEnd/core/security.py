"""
Security utilities - JWT, password hashing, RBAC helpers
"""

from datetime import datetime, timedelta
from typing import Optional
from passlib.context import CryptContext
from jose import JWTError, jwt

from core.config import settings

# Password hashing
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


def get_password_hash(password: str) -> str:
    """
    Hash a plain password using bcrypt.
    
    Args:
        password: Plain text password
        
    Returns:
        str: Hashed password
        
    Example:
        hashed = get_password_hash("mypassword")
    """
    return pwd_context.hash(password)


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """
    Verify a plain password against its hash.
    
    Args:
        plain_password: Plain text password
        hashed_password: Bcrypt hash
        
    Returns:
        bool: True if password matches hash
        
    Example:
        if verify_password("mypassword", hashed):
            print("Password is correct")
    """
    return pwd_context.verify(plain_password, hashed_password)


def create_access_token(
    data: dict,
    expires_delta: Optional[timedelta] = None
) -> str:
    """
    Create JWT access token.
    
    Args:
        data: Claims to encode in token
        expires_delta: Token expiration time (default: 30 minutes)
        
    Returns:
        str: JWT token
        
    Example:
        token = create_access_token({"sub": user_id})
    """
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(
            minutes=settings.access_token_expire_minutes
        )
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(
        to_encode,
        settings.secret_key,
        algorithm=settings.algorithm
    )
    return encoded_jwt


def verify_token(token: str) -> Optional[dict]:
    """
    Verify and decode JWT token.
    
    Args:
        token: JWT token string
        
    Returns:
        dict: Decoded claims if valid, None if invalid
        
    Example:
        claims = verify_token(token)
        if claims:
            user_id = claims.get("sub")
    """
    try:
        payload = jwt.decode(
            token,
            settings.secret_key,
            algorithms=[settings.algorithm]
        )
        return payload
    except JWTError:
        return None


def get_auth_examples() -> dict:
    """
    Provide authentication examples in multiple languages.
    
    Returns:
        dict: Examples for authentication in Python, JavaScript, and Java.
    """
    return {
        "Python": """
import requests

url = "http://localhost:8000/api/v1/agents/"
headers = {
    "Authorization": "Bearer YOUR_ACCESS_TOKEN"
}
response = requests.get(url, headers=headers)
print(response.json())
""",
        "JavaScript": """
fetch('http://localhost:8000/api/v1/agents/', {
    method: 'GET',
    headers: {
        'Authorization': 'Bearer YOUR_ACCESS_TOKEN'
    }
})
.then(response => response.json())
.then(data => console.log(data));
""",
        "Java": """
import java.net.HttpURLConnection;
import java.net.URL;

public class Main {
    public static void main(String[] args) throws Exception {
        URL url = new URL("http://localhost:8000/api/v1/agents/");
        HttpURLConnection conn = (HttpURLConnection) url.openConnection();
        conn.setRequestMethod("GET");
        conn.setRequestProperty("Authorization", "Bearer YOUR_ACCESS_TOKEN");
        System.out.println(conn.getResponseCode());
    }
}
"""
    }
