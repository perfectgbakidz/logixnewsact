"""
Posts API endpoints.
"""
from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, status, Query, Request
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.database import get_db
from app.api.deps import get_current_admin
from app.core.rate_limiter import limiter
from app.schemas.schemas import (
    PostCreate, PostUpdate, PostResponse, 
    PostDetailResponse, PostListResponse
)
from app.services.crud import (
    create_post, get_post_by_id, get_posts,
    update_post, delete_post, increment_post_views
)


router = APIRouter()


@router.get("", response_model=PostListResponse)
@limiter.limit("120/minute")
async def list_posts(
    request: Request,
    page: int = Query(1, ge=1, description="Page number"),
    page_size: int = Query(20, ge=1, le=100, description="Items per page"),
    category: Optional[str] = Query(None, description="Filter by category"),
    is_breaking: Optional[bool] = Query(None, description="Filter breaking news"),
    is_editors_choice: Optional[bool] = Query(None, description="Filter editor's choice"),
    is_top_news: Optional[bool] = Query(None, description="Filter top news"),
    is_trending: Optional[bool] = Query(None, description="Filter trending"),
    order_by: str = Query("created_at", description="Order by field"),
    order_desc: bool = Query(True, description="Descending order"),
    db: AsyncSession = Depends(get_db)
):
    """
    Get all posts with filtering and pagination.
    
    Query Parameters:
        - page: Page number (default: 1)
        - page_size: Items per page (default: 20, max: 100)
        - category: Filter by category/region name
        - is_breaking: Filter breaking news
        - is_editors_choice: Filter editor's choice
        - is_top_news: Filter top news
        - is_trending: Filter trending posts
        - order_by: Field to order by (default: created_at)
        - order_desc: Descending order (default: true)
    
    Returns:
        PostListResponse: Paginated list of posts
    """
    skip = (page - 1) * page_size
    
    posts, total = await get_posts(
        db=db,
        skip=skip,
        limit=page_size,
        category=category,
        is_breaking=is_breaking,
        is_editors_choice=is_editors_choice,
        is_top_news=is_top_news,
        is_trending=is_trending,
        order_by=order_by,
        order_desc=order_desc
    )
    
    total_pages = (total + page_size - 1) // page_size
    
    return PostListResponse(
        items=posts,
        total=total,
        page=page,
        page_size=page_size,
        total_pages=total_pages
    )


@router.get("/{post_id}", response_model=PostDetailResponse)
@limiter.limit("120/minute")
async def get_post(
    request: Request,
    post_id: str,
    db: AsyncSession = Depends(get_db)
):
    """
    Get a single post by ID.
    
    Args:
        post_id: Post unique identifier
        
    Returns:
        PostDetailResponse: Post details with admin info
        
    Raises:
        HTTPException: If post not found
    """
    post = await get_post_by_id(db, post_id, include_admin=True)
    
    if not post:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Post not found"
        )
    
    return post


@router.post("/{post_id}/view")
@limiter.limit("120/minute")
async def increment_view_count(
    request: Request,
    post_id: str,
    db: AsyncSession = Depends(get_db)
):
    """
    Increment post view count.
    
    Args:
        post_id: Post unique identifier
        
    Returns:
        dict: Success message
        
    Raises:
        HTTPException: If post not found
    """
    success = await increment_post_views(db, post_id)
    
    if not success:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Post not found"
        )
    
    return {"message": "View count incremented successfully"}


# ============== Protected Admin Endpoints ==============

@router.post("", response_model=PostResponse, status_code=status.HTTP_201_CREATED)
async def create_new_post(
    post_data: PostCreate,
    current_admin = Depends(get_current_admin),
    db: AsyncSession = Depends(get_db)
):
    """
    Create a new post (Admin only).
    
    Args:
        post_data: Post data to create
        current_admin: Authenticated admin
        db: Database session
        
    Returns:
        PostResponse: Created post details
    """
    post = await create_post(db, post_data, admin_id=current_admin.id)
    return post


@router.put("/{post_id}", response_model=PostResponse)
async def update_existing_post(
    post_id: str,
    post_data: PostUpdate,
    current_admin = Depends(get_current_admin),
    db: AsyncSession = Depends(get_db)
):
    """
    Update an existing post (Admin only).
    
    Args:
        post_id: Post unique identifier
        post_data: Post data to update
        current_admin: Authenticated admin
        db: Database session
        
    Returns:
        PostResponse: Updated post details
        
    Raises:
        HTTPException: If post not found
    """
    post = await update_post(db, post_id, post_data)
    
    if not post:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Post not found"
        )
    
    return post


@router.delete("/{post_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_existing_post(
    post_id: str,
    current_admin = Depends(get_current_admin),
    db: AsyncSession = Depends(get_db)
):
    """
    Delete a post (Admin only).
    
    Args:
        post_id: Post unique identifier
        current_admin: Authenticated admin
        db: Database session
        
    Raises:
        HTTPException: If post not found
    """
    success = await delete_post(db, post_id)
    
    if not success:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Post not found"
        )
    
    return None
