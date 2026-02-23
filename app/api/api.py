"""
Main API router configuration.
"""
from fastapi import APIRouter

from app.api.endpoints import auth, posts, regions, analytics, storage


# Create main API router
api_router = APIRouter(prefix="/api")

# Include endpoint routers
api_router.include_router(auth.router, prefix="/auth", tags=["Authentication"])
api_router.include_router(posts.router, prefix="/posts", tags=["Posts"])
api_router.include_router(regions.router, prefix="/regions", tags=["Regions"])
api_router.include_router(analytics.router, prefix="/analytics", tags=["Analytics"])
api_router.include_router(storage.router, prefix="/storage", tags=["Storage"])
api_router.include_router(storage.router, tags=["Uploads"])
