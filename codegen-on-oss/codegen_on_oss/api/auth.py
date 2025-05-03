"""
Authentication middleware for the API.

This module provides authentication middleware for the API endpoints.
"""

import os
import logging
import secrets
from typing import Optional, List, Dict, Any, Callable
from functools import wraps

from fastapi import FastAPI, Depends, HTTPException, Security, status
from fastapi.security import APIKeyHeader, OAuth2PasswordBearer
from jose import JWTError, jwt
from datetime import datetime, timedelta
from pydantic import BaseModel

logger = logging.getLogger(__name__)

# Configuration
API_KEY_NAME = os.environ.get("CODEGEN_API_KEY_NAME", "X-API-Key")
API_KEY = os.environ.get("CODEGEN_API_KEY")
JWT_SECRET_KEY = os.environ.get("CODEGEN_JWT_SECRET_KEY", secrets.token_hex(32))
JWT_ALGORITHM = "HS256"
JWT_EXPIRATION_MINUTES = int(os.environ.get("CODEGEN_JWT_EXPIRATION_MINUTES", "30"))

# Security schemes
api_key_header = APIKeyHeader(name=API_KEY_NAME, auto_error=False)
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token", auto_error=False)

# Models
class TokenData(BaseModel):
    """Token data model."""
    username: Optional[str] = None
    scopes: List[str] = []


class User(BaseModel):
    """User model."""
    username: str
    disabled: bool = False
    scopes: List[str] = []


# In-memory user database (replace with a real database in production)
fake_users_db = {
    "admin": {
        "username": "admin",
        "hashed_password": "$2b$12$EixZaYVK1fsbw1ZfbX3OXePaWxn96p36WQoeG6Lruj3vjPGga31lW",  # "password"
        "disabled": False,
        "scopes": ["admin", "read", "write"],
    }
}


def sanitize_github_token(token: Optional[str]) -> Optional[str]:
    """
    Sanitize a GitHub token to prevent command injection.
    
    Args:
        token: GitHub token to sanitize.
        
    Returns:
        Sanitized token or None if the token is invalid.
    """
    if token is None:
        return None
    
    # Remove any non-alphanumeric characters
    sanitized_token = ''.join(c for c in token if c.isalnum() or c in '-_')
    
    # Check if the token was modified during sanitization
    if sanitized_token != token:
        logger.warning("GitHub token was sanitized due to invalid characters")
    
    # Validate token length (GitHub tokens are typically 40 characters)
    if len(sanitized_token) < 30:
        logger.warning("GitHub token is suspiciously short")
        return None
    
    return sanitized_token


def create_access_token(data: Dict[str, Any], expires_delta: Optional[timedelta] = None) -> str:
    """
    Create a JWT access token.
    
    Args:
        data: Data to encode in the token.
        expires_delta: Token expiration time.
        
    Returns:
        JWT token.
    """
    to_encode = data.copy()
    
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=JWT_EXPIRATION_MINUTES)
    
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, JWT_SECRET_KEY, algorithm=JWT_ALGORITHM)
    
    return encoded_jwt


async def get_current_user(token: str = Depends(oauth2_scheme)) -> User:
    """
    Get the current user from a JWT token.
    
    Args:
        token: JWT token.
        
    Returns:
        User object.
        
    Raises:
        HTTPException: If the token is invalid or the user is not found.
    """
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    
    if token is None:
        raise credentials_exception
    
    try:
        payload = jwt.decode(token, JWT_SECRET_KEY, algorithms=[JWT_ALGORITHM])
        username: str = payload.get("sub")
        
        if username is None:
            raise credentials_exception
        
        token_scopes = payload.get("scopes", [])
        token_data = TokenData(username=username, scopes=token_scopes)
    except JWTError:
        raise credentials_exception
    
    user = fake_users_db.get(token_data.username)
    
    if user is None:
        raise credentials_exception
    
    return User(
        username=user["username"],
        disabled=user["disabled"],
        scopes=user["scopes"],
    )


async def get_current_active_user(current_user: User = Depends(get_current_user)) -> User:
    """
    Get the current active user.
    
    Args:
        current_user: Current user.
        
    Returns:
        User object.
        
    Raises:
        HTTPException: If the user is disabled.
    """
    if current_user.disabled:
        raise HTTPException(status_code=400, detail="Inactive user")
    
    return current_user


async def verify_api_key(api_key: str = Security(api_key_header)) -> bool:
    """
    Verify an API key.
    
    Args:
        api_key: API key to verify.
        
    Returns:
        True if the API key is valid.
        
    Raises:
        HTTPException: If the API key is invalid.
    """
    if API_KEY is None:
        # API key authentication is disabled
        return True
    
    if api_key is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="API key is required",
            headers={"WWW-Authenticate": API_KEY_NAME},
        )
    
    if api_key != API_KEY:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid API key",
            headers={"WWW-Authenticate": API_KEY_NAME},
        )
    
    return True


def configure_auth(app: FastAPI) -> None:
    """
    Configure authentication for the API.
    
    Args:
        app: FastAPI application.
    """
    @app.post("/token")
    async def login_for_access_token(form_data: OAuth2PasswordBearer = Depends()):
        """
        Get an access token.
        
        Args:
            form_data: OAuth2 password bearer.
            
        Returns:
            Access token.
            
        Raises:
            HTTPException: If the username or password is invalid.
        """
        user = fake_users_db.get(form_data.username)
        
        if user is None:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid username or password",
                headers={"WWW-Authenticate": "Bearer"},
            )
        
        # In a real application, you would verify the password here
        
        access_token_expires = timedelta(minutes=JWT_EXPIRATION_MINUTES)
        access_token = create_access_token(
            data={"sub": user["username"], "scopes": user["scopes"]},
            expires_delta=access_token_expires,
        )
        
        return {"access_token": access_token, "token_type": "bearer"}


def requires_auth(func: Callable) -> Callable:
    """
    Decorator to require authentication for an endpoint.
    
    Args:
        func: Function to decorate.
        
    Returns:
        Decorated function.
    """
    @wraps(func)
    async def wrapper(*args, **kwargs):
        # Check if API key authentication is enabled
        if API_KEY is not None:
            # Get the API key from the request
            api_key = kwargs.get("api_key")
            
            if api_key is None:
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="API key is required",
                    headers={"WWW-Authenticate": API_KEY_NAME},
                )
            
            if api_key != API_KEY:
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="Invalid API key",
                    headers={"WWW-Authenticate": API_KEY_NAME},
                )
        
        return await func(*args, **kwargs)
    
    return wrapper

