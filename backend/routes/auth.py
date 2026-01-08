from fastapi import APIRouter, HTTPException, Depends
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from passlib.context import CryptContext
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from src.models.user import UserCreate, UserLogin, UserResponse
from src.models.user_db import User
from src.config.database import get_postgres_db
from src.middleware.auth_middleware import create_access_token, get_current_user, blacklist_token, decode_access_token
from datetime import datetime
from src.utils.logger import get_logger

logger = get_logger(__name__)
router = APIRouter(prefix="/api/auth", tags=["Authentication"])

# Password hashing
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

def hash_password(password: str) -> str:
    return pwd_context.hash(password)

def verify_password(plain_password: str, hashed_password: str) -> bool:
    return pwd_context.verify(plain_password, hashed_password)

@router.post("/signup", response_model=UserResponse)
async def signup(user: UserCreate, db: AsyncSession = Depends(get_postgres_db)):
    """Register a new user"""
    try:
        # Check if user already exists
        query = select(User).where(User.email == user.email.lower())
        result = await db.execute(query)
        existing_user = result.scalar_one_or_none()
        if existing_user:
            raise HTTPException(status_code=409, detail="User with this email already exists")
        
        # Create new user
        new_user = User(
            name=user.name,
            email=user.email.lower(),
            password_hash=hash_password(user.password),
            dob=user.dob,
            state=user.state,
            city=user.city,
            pincode=user.pincode,
            mode="user"  # All signups are regular users
        )
        
        # Insert into database
        db.add(new_user)
        await db.commit()
        await db.refresh(new_user)
        
        logger.info(f"New user registered: {user.email}")
        
        return UserResponse(
            id=new_user.id,
            name=new_user.name,
            email=new_user.email,
            mode=new_user.mode,
            created_at=new_user.created_at
        )
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Signup error: {e}", exc_info=True)
        # Return more detailed error in development
        error_detail = str(e)
        if "users" in error_detail.lower() and "does not exist" in error_detail.lower():
            error_detail = "Database table 'users' does not exist. Please restart the backend to create tables."
        raise HTTPException(status_code=500, detail=f"Internal server error: {error_detail}")

@router.post("/login")
async def login(credentials: UserLogin, db: AsyncSession = Depends(get_postgres_db)):
    """Login user and return JWT token"""
    try:
        # Find user by email
        query = select(User).where(User.email == credentials.email.lower())
        result = await db.execute(query)
        user = result.scalar_one_or_none()
        if not user:
            raise HTTPException(status_code=401, detail="Invalid email or password")
        
        # Verify password
        if not verify_password(credentials.password, user.password_hash):
            raise HTTPException(status_code=401, detail="Invalid email or password")
        
        # Create JWT token
        token_data = {
            "sub": user.email,
            "user_id": str(user.id),
            "mode": user.mode or "user"
        }
        access_token = create_access_token(token_data)
        
        logger.info(f"User logged in: {user.email}")
        
        return {
            "access_token": access_token,
            "token_type": "bearer",
            "user": {
                "id": user.id,
                "name": user.name,
                "email": user.email,
                "mode": user.mode or "user"
            }
        }
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Login error: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")

@router.get("/me", response_model=UserResponse)
async def get_current_user_info(
    current_user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_postgres_db)
):
    """Get current user information"""
    try:
        query = select(User).where(User.email == current_user["email"])
        result = await db.execute(query)
        user = result.scalar_one_or_none()
        if not user:
            raise HTTPException(status_code=404, detail="User not found")
        
        return UserResponse(
            id=user.id,
            name=user.name,
            email=user.email,
            mode=user.mode or "user",
            created_at=user.created_at
        )
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Get user error: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")

@router.post("/logout")
async def logout(
    credentials: HTTPAuthorizationCredentials = Depends(HTTPBearer()),
    current_user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_postgres_db)
):
    """Logout user by blacklisting current JWT token"""
    try:
        token = credentials.credentials
        payload = decode_access_token(token)
        exp = None
        if payload and payload.get("exp"):
            try:
                exp = datetime.utcfromtimestamp(payload["exp"])
            except Exception:
                exp = None
        await blacklist_token(token, exp, db)
        logger.info(f"User logged out: {current_user['email']}")
        return {"message": "Successfully logged out"}
    except Exception as e:
        logger.error(f"Logout error: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")
