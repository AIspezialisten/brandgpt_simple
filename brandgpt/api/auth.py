from datetime import datetime, timedelta
from typing import Optional, Union
from jose import JWTError, jwt
from passlib.context import CryptContext
from fastapi import Depends, HTTPException, status, Header
from fastapi.security import OAuth2PasswordBearer, HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.orm import Session
from brandgpt.models import User, get_db
from brandgpt.config import settings
import logging

logger = logging.getLogger(__name__)

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/auth/token", auto_error=False)
http_bearer = HTTPBearer(auto_error=False)


def verify_password(plain_password: str, hashed_password: str) -> bool:
    return pwd_context.verify(plain_password, hashed_password)


def get_password_hash(password: str) -> str:
    # Bcrypt has a 72 byte limit, truncate if necessary
    if len(password.encode('utf-8')) > 72:
        password = password.encode('utf-8')[:72].decode('utf-8', errors='ignore')
    return pwd_context.hash(password)


def create_access_token(data: dict, expires_delta: Optional[timedelta] = None):
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=settings.access_token_expire_minutes)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, settings.secret_key, algorithm=settings.algorithm)
    return encoded_jwt


async def get_current_user_jwt(
    token: str = Depends(oauth2_scheme),
    db: Session = Depends(get_db)
) -> Optional[User]:
    """Get user from JWT token."""
    if not token:
        return None
    
    try:
        payload = jwt.decode(token, settings.secret_key, algorithms=[settings.algorithm])
        username: str = payload.get("sub")
        if username is None:
            return None
    except JWTError:
        return None
    
    user = db.query(User).filter(User.username == username).first()
    return user


async def get_current_user_api_key(
    authorization: Optional[str] = Header(None),
    db: Session = Depends(get_db)
) -> Optional[User]:
    """Get user from API key in Authorization header."""
    logger.info(f"=== API KEY AUTH DEBUG ===")
    logger.info(f"Authorization header: {authorization[:20] + '...' if authorization and len(authorization) > 20 else authorization}")
    
    if not authorization:
        logger.info("No authorization header provided")
        return None
    
    # Support both "Bearer API_KEY" and "API_KEY" formats
    api_key = authorization
    if authorization.startswith("Bearer "):
        api_key = authorization[7:]
        logger.info("Extracted API key from Bearer format")
    
    logger.info(f"API key (first 10 chars): {api_key[:10]}...")
    
    if not api_key.startswith("bgpt_"):
        logger.info("API key does not start with 'bgpt_'")
        return None
    
    logger.info("API key format is valid, querying database...")
    
    try:
        # Debug the database query
        from sqlalchemy import text
        logger.info(f"Database engine: {db.bind}")
        
        # Check if users table exists and has api_key column
        result = db.execute(text("SELECT name FROM sqlite_master WHERE type='table' AND name='users'"))
        table_exists = result.fetchone() is not None
        logger.info(f"Users table exists: {table_exists}")
        
        if table_exists:
            # Check table structure
            result = db.execute(text("PRAGMA table_info(users)"))
            columns = result.fetchall()
            column_names = [col[1] for col in columns]
            logger.info(f"Users table columns: {column_names}")
            logger.info(f"Has api_key column: {'api_key' in column_names}")
            
            # Count total users
            result = db.execute(text("SELECT COUNT(*) FROM users"))
            total_users = result.scalar()
            logger.info(f"Total users in database: {total_users}")
            
            # Check for users with API keys
            result = db.execute(text("SELECT COUNT(*) FROM users WHERE api_key IS NOT NULL"))
            users_with_keys = result.scalar()
            logger.info(f"Users with API keys: {users_with_keys}")
        
        user = db.query(User).filter(User.api_key == api_key).first()
        logger.info(f"User found: {user.username if user else None}")
        return user
        
    except Exception as e:
        logger.error(f"Database query error: {str(e)}")
        logger.error(f"Exception type: {type(e)}")
        import traceback
        logger.error(f"Traceback: {traceback.format_exc()}")
        return None


async def get_current_user(
    jwt_user: Optional[User] = Depends(get_current_user_jwt),
    api_key_user: Optional[User] = Depends(get_current_user_api_key),
    db: Session = Depends(get_db)
) -> User:
    """
    Dual authentication: Try JWT first, then API key.
    Supports both web users (JWT) and server-to-server (API key) authentication.
    """
    # Try JWT authentication first
    if jwt_user:
        return jwt_user
    
    # Try API key authentication
    if api_key_user:
        return api_key_user
    
    # No valid authentication found
    raise HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials. Use JWT token or API key.",
        headers={"WWW-Authenticate": "Bearer"},
    )


def authenticate_user(db: Session, username: str, password: str) -> Optional[User]:
    user = db.query(User).filter(User.username == username).first()
    if not user or not verify_password(password, user.hashed_password):
        return None
    return user