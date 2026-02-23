"""
API dependencies for authentication and authorization.
"""
from typing import Optional
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.database import get_db
from app.models.models import Admin
from app.core.security import decode_access_token
from app.services.crud import get_admin_by_id


# HTTP Bearer security scheme
security_bearer = HTTPBearer(auto_error=False)


async def get_current_admin(
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(security_bearer),
    db: AsyncSession = Depends(get_db)
) -> Admin:
    """
    Get current authenticated admin from JWT token.
    
    Args:
        credentials: HTTP Authorization credentials
        db: Database session
        
    Returns:
        Admin: Current authenticated admin
        
    Raises:
        HTTPException: If authentication fails
    """
    if not credentials:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Not authenticated",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    token = credentials.credentials
    
    try:
        payload = decode_access_token(token)
        admin_id: str = payload.get("sub")
        
        if admin_id is None:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid authentication credentials",
                headers={"WWW-Authenticate": "Bearer"},
            )
            
    except HTTPException:
        raise
    except Exception:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid authentication credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    admin = await get_admin_by_id(db, admin_id)
    
    if admin is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User not found",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    return admin


async def get_current_active_admin(
    current_admin: Admin = Depends(get_current_admin)
) -> Admin:
    """
    Verify current admin is active (can add more checks here).
    
    Args:
        current_admin: Current authenticated admin
        
    Returns:
        Admin: Current active admin
    """
    # Add any additional checks here (e.g., is_active flag)
    return current_admin
