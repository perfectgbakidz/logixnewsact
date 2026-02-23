"""
CRUD operations for database models.
"""
from typing import Optional, List, Any
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update, delete, func, desc, asc
from sqlalchemy.orm import selectinload

from app.models.models import Admin, Region, SubZone, Post
from app.schemas.schemas import (
    AdminCreate, AdminUpdate,
    RegionCreate, RegionUpdate,
    SubZoneCreate, SubZoneUpdate,
    PostCreate, PostUpdate
)
from app.core.security import get_password_hash


# ============== Admin CRUD ==============

async def create_admin(db: AsyncSession, admin_data: AdminCreate) -> Admin:
    """Create a new admin user."""
    db_admin = Admin(
        username=admin_data.username,
        hashed_password=get_password_hash(admin_data.password),
        full_name=admin_data.full_name,
        email=admin_data.email,
        avatar_url=admin_data.avatar_url,
        role=admin_data.role
    )
    db.add(db_admin)
    await db.commit()
    await db.refresh(db_admin)
    return db_admin


async def get_admin_by_id(db: AsyncSession, admin_id: str) -> Optional[Admin]:
    """Get admin by ID."""
    result = await db.execute(select(Admin).where(Admin.id == admin_id))
    return result.scalar_one_or_none()


async def get_admin_by_username(db: AsyncSession, username: str) -> Optional[Admin]:
    """Get admin by username."""
    result = await db.execute(select(Admin).where(Admin.username == username))
    return result.scalar_one_or_none()


async def update_admin(
    db: AsyncSession, 
    admin_id: str, 
    admin_data: AdminUpdate
) -> Optional[Admin]:
    """Update admin details."""
    update_data = admin_data.model_dump(exclude_unset=True)
    
    await db.execute(
        update(Admin)
        .where(Admin.id == admin_id)
        .values(**update_data)
    )
    await db.commit()
    
    return await get_admin_by_id(db, admin_id)


async def delete_admin(db: AsyncSession, admin_id: str) -> bool:
    """Delete an admin."""
    result = await db.execute(
        delete(Admin).where(Admin.id == admin_id)
    )
    await db.commit()
    return result.rowcount > 0


# ============== Region CRUD ==============

async def create_region(db: AsyncSession, region_data: RegionCreate) -> Region:
    """Create a new region."""
    db_region = Region(
        name=region_data.name,
        image=region_data.image
    )
    db.add(db_region)
    await db.commit()
    await db.refresh(db_region)
    return db_region


async def get_region_by_id(db: AsyncSession, region_id: str) -> Optional[Region]:
    """Get region by ID with sub-zones."""
    result = await db.execute(
        select(Region)
        .options(selectinload(Region.sub_zones))
        .where(Region.id == region_id)
    )
    return result.scalar_one_or_none()


async def get_region_by_name(db: AsyncSession, name: str) -> Optional[Region]:
    """Get region by name."""
    result = await db.execute(select(Region).where(Region.name == name))
    return result.scalar_one_or_none()


async def get_all_regions(db: AsyncSession) -> List[Region]:
    """Get all regions with their sub-zones."""
    result = await db.execute(
        select(Region).options(selectinload(Region.sub_zones))
    )
    return result.scalars().all()


async def update_region(
    db: AsyncSession, 
    region_id: str, 
    region_data: RegionUpdate
) -> Optional[Region]:
    """Update region details."""
    update_data = region_data.model_dump(exclude_unset=True)
    
    await db.execute(
        update(Region)
        .where(Region.id == region_id)
        .values(**update_data)
    )
    await db.commit()
    
    return await get_region_by_id(db, region_id)


async def delete_region(db: AsyncSession, region_id: str) -> bool:
    """Delete a region and its sub-zones."""
    result = await db.execute(
        delete(Region).where(Region.id == region_id)
    )
    await db.commit()
    return result.rowcount > 0


# ============== SubZone CRUD ==============

async def create_sub_zone(
    db: AsyncSession, 
    region_id: str, 
    zone_data: SubZoneCreate
) -> SubZone:
    """Create a new sub-zone for a region."""
    db_zone = SubZone(
        region_id=region_id,
        name=zone_data.name,
        image=zone_data.image
    )
    db.add(db_zone)
    await db.commit()
    await db.refresh(db_zone)
    return db_zone


async def get_sub_zone_by_id(db: AsyncSession, zone_id: str) -> Optional[SubZone]:
    """Get sub-zone by ID."""
    result = await db.execute(
        select(SubZone).where(SubZone.id == zone_id)
    )
    return result.scalar_one_or_none()


async def get_sub_zones_by_region(
    db: AsyncSession, 
    region_id: str
) -> List[SubZone]:
    """Get all sub-zones for a region."""
    result = await db.execute(
        select(SubZone).where(SubZone.region_id == region_id)
    )
    return result.scalars().all()


async def update_sub_zone(
    db: AsyncSession, 
    zone_id: str, 
    zone_data: SubZoneUpdate
) -> Optional[SubZone]:
    """Update sub-zone details."""
    update_data = zone_data.model_dump(exclude_unset=True)
    
    await db.execute(
        update(SubZone)
        .where(SubZone.id == zone_id)
        .values(**update_data)
    )
    await db.commit()
    
    return await get_sub_zone_by_id(db, zone_id)


async def delete_sub_zone(db: AsyncSession, zone_id: str) -> bool:
    """Delete a sub-zone."""
    result = await db.execute(
        delete(SubZone).where(SubZone.id == zone_id)
    )
    await db.commit()
    return result.rowcount > 0


# ============== Post CRUD ==============

async def create_post(
    db: AsyncSession, 
    post_data: PostCreate,
    admin_id: Optional[str] = None
) -> Post:
    """Create a new post."""
    db_post = Post(
        title=post_data.title,
        excerpt=post_data.excerpt,
        content=post_data.content,
        author=post_data.author,
        date=post_data.date,
        category=post_data.category,
        image_url=post_data.image_url,
        read_time=post_data.read_time,
        is_breaking=post_data.is_breaking,
        is_editors_choice=post_data.is_editors_choice,
        is_top_news=post_data.is_top_news,
        is_trending=post_data.is_trending,
        admin_id=admin_id
    )
    db.add(db_post)
    await db.commit()
    await db.refresh(db_post)
    return db_post


async def get_post_by_id(
    db: AsyncSession, 
    post_id: str,
    include_admin: bool = False
) -> Optional[Post]:
    """Get post by ID."""
    query = select(Post).where(Post.id == post_id)
    
    if include_admin:
        query = query.options(selectinload(Post.admin))
    
    result = await db.execute(query)
    return result.scalar_one_or_none()


async def get_posts(
    db: AsyncSession,
    skip: int = 0,
    limit: int = 20,
    category: Optional[str] = None,
    is_breaking: Optional[bool] = None,
    is_editors_choice: Optional[bool] = None,
    is_top_news: Optional[bool] = None,
    is_trending: Optional[bool] = None,
    order_by: str = "created_at",
    order_desc: bool = True
) -> tuple[List[Post], int]:
    """Get posts with filtering and pagination."""
    query = select(Post)
    count_query = select(func.count(Post.id))
    
    # Apply filters
    if category:
        query = query.where(Post.category == category)
        count_query = count_query.where(Post.category == category)
    
    if is_breaking is not None:
        query = query.where(Post.is_breaking == is_breaking)
        count_query = count_query.where(Post.is_breaking == is_breaking)
    
    if is_editors_choice is not None:
        query = query.where(Post.is_editors_choice == is_editors_choice)
        count_query = count_query.where(Post.is_editors_choice == is_editors_choice)
    
    if is_top_news is not None:
        query = query.where(Post.is_top_news == is_top_news)
        count_query = count_query.where(Post.is_top_news == is_top_news)
    
    if is_trending is not None:
        query = query.where(Post.is_trending == is_trending)
        count_query = count_query.where(Post.is_trending == is_trending)
    
    # Get total count
    count_result = await db.execute(count_query)
    total = count_result.scalar()
    
    # Apply ordering
    order_column = getattr(Post, order_by, Post.created_at)
    if order_desc:
        query = query.order_by(desc(order_column))
    else:
        query = query.order_by(asc(order_column))
    
    # Apply pagination
    query = query.offset(skip).limit(limit)
    
    result = await db.execute(query)
    posts = result.scalars().all()
    
    return list(posts), total


async def update_post(
    db: AsyncSession, 
    post_id: str, 
    post_data: PostUpdate
) -> Optional[Post]:
    """Update post details."""
    update_data = post_data.model_dump(exclude_unset=True)
    
    if not update_data:
        return await get_post_by_id(db, post_id)
    
    await db.execute(
        update(Post)
        .where(Post.id == post_id)
        .values(**update_data)
    )
    await db.commit()
    
    return await get_post_by_id(db, post_id)


async def delete_post(db: AsyncSession, post_id: str) -> bool:
    """Delete a post."""
    result = await db.execute(
        delete(Post).where(Post.id == post_id)
    )
    await db.commit()
    return result.rowcount > 0


async def increment_post_views(db: AsyncSession, post_id: str) -> bool:
    """Increment post view count."""
    result = await db.execute(
        update(Post)
        .where(Post.id == post_id)
        .values(views=Post.views + 1)
    )
    await db.commit()
    return result.rowcount > 0


# ============== Analytics ==============

async def get_analytics(db: AsyncSession) -> dict:
    """Get site-wide analytics."""
    # Total posts
    posts_result = await db.execute(select(func.count(Post.id)))
    total_posts = posts_result.scalar()
    
    # Total views
    views_result = await db.execute(select(func.sum(Post.views)))
    total_views = views_result.scalar() or 0
    
    # Total regions
    regions_result = await db.execute(select(func.count(Region.id)))
    total_regions = regions_result.scalar()
    
    # Total sub-zones
    zones_result = await db.execute(select(func.count(SubZone.id)))
    total_sub_zones = zones_result.scalar()
    
    # Total admins
    admins_result = await db.execute(select(func.count(Admin.id)))
    total_admins = admins_result.scalar()
    
    # Breaking news count
    breaking_result = await db.execute(
        select(func.count(Post.id)).where(Post.is_breaking == True)
    )
    breaking_count = breaking_result.scalar()
    
    # Editor's choice count
    editors_choice_result = await db.execute(
        select(func.count(Post.id)).where(Post.is_editors_choice == True)
    )
    editors_choice_count = editors_choice_result.scalar()
    
    # Top news count
    top_news_result = await db.execute(
        select(func.count(Post.id)).where(Post.is_top_news == True)
    )
    top_news_count = top_news_result.scalar()
    
    # Trending count
    trending_result = await db.execute(
        select(func.count(Post.id)).where(Post.is_trending == True)
    )
    trending_count = trending_result.scalar()
    
    return {
        "total_posts": total_posts,
        "total_views": total_views,
        "total_regions": total_regions,
        "total_sub_zones": total_sub_zones,
        "total_admins": total_admins,
        "breaking_news_count": breaking_count,
        "editors_choice_count": editors_choice_count,
        "top_news_count": top_news_count,
        "trending_count": trending_count
    }
