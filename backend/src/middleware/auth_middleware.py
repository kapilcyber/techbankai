"""Authentication middleware for JWT token handling."""
from fastapi import HTTPException, Security, Depends
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from jose import JWTError, jwt
from datetime import datetime, timedelta
from typing import Optional
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, delete

from src.config.database import get_postgres_db
from src.config.settings import settings
from src.models.token_blacklist import TokenBlacklist

# JWT Configuration from settings
JWT_SECRET_KEY = settings.jwt_secret_key
JWT_ALGORITHM = settings.jwt_algorithm
JWT_EXPIRATION_HOURS = settings.jwt_expiration_hours

security = HTTPBearer()


def create_access_token(data: dict, expires_delta: Optional[timedelta] = None):
    """Create JWT access token."""
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(hours=JWT_EXPIRATION_HOURS)
    
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, JWT_SECRET_KEY, algorithm=JWT_ALGORITHM)
    return encoded_jwt


def decode_access_token(token: str):
    """Decode and verify JWT token."""
    try:
        payload = jwt.decode(token, JWT_SECRET_KEY, algorithms=[JWT_ALGORITHM])
        return payload
    except JWTError:
        return None


async def blacklist_token(token: str, exp: Optional[datetime] = None, db: Optional[AsyncSession] = None):
    """Blacklist a JWT token until its expiration."""
    if db is None:
        # Get database session if not provided
        async for session in get_postgres_db():
            db = session
            break
    
    expires_at = exp if exp else datetime.utcnow() + timedelta(hours=JWT_EXPIRATION_HOURS)
    
    blacklist_entry = TokenBlacklist(
        token=token,
        expires_at=expires_at
    )
    
    db.add(blacklist_entry)
    await db.commit()


async def is_token_blacklisted(token: str, db: Optional[AsyncSession] = None) -> bool:
    """Check if token is blacklisted."""
    if db is None:
        # Get database session if not provided
        async for session in get_postgres_db():
            db = session
            try:
                query = select(TokenBlacklist).where(TokenBlacklist.token == token)
                result = await db.execute(query)
                existing = result.scalar_one_or_none()
                if not existing:
                    return False
                # Expire old blacklist entries proactively
                if existing.expires_at < datetime.utcnow():
                    await db.execute(delete(TokenBlacklist).where(TokenBlacklist.id == existing.id))
                    await db.commit()
                    return False
                return True
            finally:
                await db.close()
            break
        return False
    else:
        query = select(TokenBlacklist).where(TokenBlacklist.token == token)
        result = await db.execute(query)
        existing = result.scalar_one_or_none()
        if not existing:
            return False
        # Expire old blacklist entries proactively
        if existing.expires_at < datetime.utcnow():
            await db.execute(delete(TokenBlacklist).where(TokenBlacklist.id == existing.id))
            await db.commit()
            return False
        return True


async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Security(security),
    db: AsyncSession = Depends(get_postgres_db)
):
    """Get current user from JWT token."""
    token = credentials.credentials
    if await is_token_blacklisted(token, db):
        raise HTTPException(status_code=401, detail="Token has been revoked")
    payload = decode_access_token(token)
    
    if payload is None:
        raise HTTPException(status_code=401, detail="Invalid authentication credentials")
    
    user_email = payload.get("sub")
    user_mode = payload.get("mode", "user")
    
    if user_email is None:
        raise HTTPException(status_code=401, detail="Invalid authentication credentials")
    
    return {
        "email": user_email,
        "mode": user_mode,
        "user_id": payload.get("user_id")
    }


async def get_admin_user(current_user: dict = Depends(get_current_user)):
    """Verify user is admin."""
    if current_user.get("mode") != "admin":
        raise HTTPException(
            status_code=403, 
            detail="Admin access required. This endpoint is restricted to admin users only. Please contact your administrator or use /api/resumes/upload/user-profile for regular uploads."
        )
    return current_user

