"""
Analytics API endpoints.
"""
from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.database import get_db
from app.api.deps import get_current_admin
from app.schemas.schemas import AnalyticsResponse
from app.services.crud import get_analytics


router = APIRouter()


@router.get("", response_model=AnalyticsResponse)
async def get_site_analytics(
    current_admin = Depends(get_current_admin),
    db: AsyncSession = Depends(get_db)
):
    """
    Get site-wide analytics (Admin only).
    
    Returns statistics including:
    - Total posts count
    - Total views count
    - Total regions count
    - Total sub-zones count
    - Total admins count
    - Breaking news count
    - Editor's choice count
    - Top news count
    - Trending posts count
    
    Returns:
        AnalyticsResponse: Site-wide analytics data
    """
    analytics_data = await get_analytics(db)
    return AnalyticsResponse(**analytics_data)
