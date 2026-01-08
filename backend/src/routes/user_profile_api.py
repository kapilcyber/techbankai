"""User profile API routes (view & update current user profile)."""
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from pydantic import BaseModel, Field
from typing import Optional

from src.config.database import get_postgres_db
from src.middleware.auth_middleware import get_current_user
from src.models.user_db import User
from src.models.user import UserResponse
from src.utils.logger import get_logger


logger = get_logger(__name__)
router = APIRouter(prefix="/api/user", tags=["User Profile"])


class UserProfileUpdate(BaseModel):
    """Fields that a user is allowed to update on their profile."""
    name: Optional[str] = Field(None, min_length=2, max_length=100)
    dob: Optional[str] = None
    state: Optional[str] = None
    city: Optional[str] = None
    pincode: Optional[str] = None


@router.get("/profile", response_model=UserResponse)
async def get_profile(
    current_user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_postgres_db),
):
    """Get the current authenticated user's profile."""
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
            created_at=user.created_at,
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Get profile error: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")


@router.put("/profile", response_model=UserResponse)
async def update_profile(
    profile_update: UserProfileUpdate,
    current_user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_postgres_db),
):
    """Update the current authenticated user's profile."""
    try:
        query = select(User).where(User.email == current_user["email"])
        result = await db.execute(query)
        user = result.scalar_one_or_none()
        if not user:
            raise HTTPException(status_code=404, detail="User not found")

        # Apply updates only for provided fields
        if profile_update.name is not None:
            user.name = profile_update.name
        if profile_update.dob is not None:
            user.dob = profile_update.dob
        if profile_update.state is not None:
            user.state = profile_update.state
        if profile_update.city is not None:
            user.city = profile_update.city
        if profile_update.pincode is not None:
            user.pincode = profile_update.pincode

        await db.commit()
        await db.refresh(user)

        logger.info(f"Updated profile for user: {user.email}")

        return UserResponse(
            id=user.id,
            name=user.name,
            email=user.email,
            mode=user.mode or "user",
            created_at=user.created_at,
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Update profile error: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")


