"""
Authentication API endpoints.
"""
from datetime import timedelta
from fastapi import APIRouter, Depends, HTTPException, status, Request
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.database import get_db
from app.api.deps import get_current_admin
from app.core.config import settings
from app.core.rate_limiter import limiter
from app.core.security import verify_password, create_access_token
from app.schemas.schemas import Token, LoginRequest, AdminResponse, AdminUpdate
from app.services.crud import get_admin_by_username, update_admin


router = APIRouter()


@router.post("/login", response_model=Token)
@limiter.limit("5/minute")
async def login(
    request: Request,
    login_data: LoginRequest,
    db: AsyncSession = Depends(get_db)
):
    """
    Authenticate admin and return JWT token.
    
    Args:
        login_data: Login credentials (username and password)
        db: Database session
        
    Returns:
        Token: JWT access token
        
    Raises:
        HTTPException: If authentication fails
    """
    # Get admin by username
    admin = await get_admin_by_username(db, login_data.username)
    
    if not admin:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    # Verify password
    if not verify_password(login_data.password, admin.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    # Create access token
    access_token_expires = timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        data={"sub": admin.id},
        expires_delta=access_token_expires
    )
    
    return Token(
        access_token=access_token,
        token_type="bearer",
        expires_in=settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60
    )


@router.get("/me", response_model=AdminResponse)
async def get_current_admin_profile(
    current_admin = Depends(get_current_admin)
):
    """
    Get current authenticated admin profile.
    
    Returns:
        AdminResponse: Current admin details (excluding password)
    """
    return current_admin


@router.put("/profile", response_model=AdminResponse)
async def update_admin_profile(
    profile_data: AdminUpdate,
    current_admin = Depends(get_current_admin),
    db: AsyncSession = Depends(get_db)
):
    """
    Update current admin profile.
    
    Args:
        profile_data: Profile data to update
        current_admin: Current authenticated admin
        db: Database session
        
    Returns:
        AdminResponse: Updated admin details
    """
    updated_admin = await update_admin(db, current_admin.id, profile_data)
    
    if not updated_admin:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Admin not found"
        )
    
    return updated_admin
