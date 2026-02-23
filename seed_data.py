"""
Seed script for Logic NewsAct backend.

This script is idempotent:
- Creates tables if they do not exist.
- Creates/updates one default admin.
- Creates regions and sub-zones from a fixed catalog.
- Creates sample posts if missing (matched by title).
"""

import asyncio
import sys
from typing import Dict, List

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.core.security import get_password_hash
from app.db.database import AsyncSessionLocal, init_db
from app.models.models import Admin, Post, Region, SubZone


DEFAULT_ADMIN = {
    "username": "admin",
    "password": "admin123",
    "full_name": "System Administrator",
    "email": "admin@logicnewsact.ng",
    "avatar_url": None,
    "role": "Editor-in-Chief",
}

REGION_ZONE_MAP: Dict[str, List[str]] = {
    "IbileLogic": ["Lagos", "Ogun", "Oyo", "Osun", "Ekiti", "Ondo"],
    "ArewaLogic": ["Kano", "Kaduna", "Katsina", "Sokoto", "Zamfara"],
    "NaijaLogic": ["Abuja", "Nasarawa", "Niger", "Plateau"],
    "NigerDeltaLogic": ["Rivers", "Delta", "Bayelsa", "Akwa Ibom"],
}

SAMPLE_POSTS = [
    {
        "title": "Breaking: Major Infrastructure Project Announced",
        "excerpt": "Government unveils an ambitious infrastructure plan for the region.",
        "content": (
            "<p>Officials announced a multi-year infrastructure rollout focused on roads, "
            "power, and digital access across priority states.</p>"
        ),
        "author": "Logic NewsAct Desk",
        "date": "January 15, 2024",
        "category": "IbileLogic",
        "image_url": None,
        "read_time": "5 min read",
        "views": 0,
        "is_breaking": True,
        "is_editors_choice": False,
        "is_top_news": True,
        "is_trending": False,
    },
    {
        "title": "Tech Innovation Hub Opens in Lagos",
        "excerpt": "A new tech hub opens to support startups and digital talent.",
        "content": (
            "<p>The center provides shared workspace, mentorship, and seed support for "
            "early-stage founders.</p>"
        ),
        "author": "Business Correspondent",
        "date": "January 14, 2024",
        "category": "IbileLogic",
        "image_url": None,
        "read_time": "4 min read",
        "views": 0,
        "is_breaking": False,
        "is_editors_choice": False,
        "is_top_news": False,
        "is_trending": True,
    },
    {
        "title": "Agricultural Reform Shows Early Promise",
        "excerpt": "New farming support programs report improved yields in pilot zones.",
        "content": (
            "<p>Initial outcomes show better productivity, with expanded irrigation and "
            "training for smallholder farmers.</p>"
        ),
        "author": "Northern Bureau",
        "date": "January 13, 2024",
        "category": "ArewaLogic",
        "image_url": None,
        "read_time": "6 min read",
        "views": 0,
        "is_breaking": False,
        "is_editors_choice": True,
        "is_top_news": False,
        "is_trending": False,
    },
    {
        "title": "Education Sector Receives Major Funding",
        "excerpt": "Budget increase targets school facilities and teacher training.",
        "content": (
            "<p>Education stakeholders welcomed the allocation, citing urgent needs in "
            "classroom expansion and instructional materials.</p>"
        ),
        "author": "Policy Reporter",
        "date": "January 12, 2024",
        "category": "NaijaLogic",
        "image_url": None,
        "read_time": "5 min read",
        "views": 0,
        "is_breaking": False,
        "is_editors_choice": False,
        "is_top_news": False,
        "is_trending": True,
    },
    {
        "title": "Community Projects Expand in the Niger Delta",
        "excerpt": "New local investment commitments focus on health and waterways.",
        "content": (
            "<p>Community leaders outlined joint priorities around clinics, schools, and "
            "transport access in riverine areas.</p>"
        ),
        "author": "Delta Correspondent",
        "date": "January 11, 2024",
        "category": "NigerDeltaLogic",
        "image_url": None,
        "read_time": "7 min read",
        "views": 0,
        "is_breaking": False,
        "is_editors_choice": False,
        "is_top_news": True,
        "is_trending": False,
    },
]


async def upsert_default_admin(db: AsyncSession) -> Admin:
    """Create admin if missing, otherwise keep existing and update profile fields."""
    result = await db.execute(
        select(Admin).where(Admin.username == DEFAULT_ADMIN["username"])
    )
    admin = result.scalar_one_or_none()

    if admin is None:
        admin = Admin(
            username=DEFAULT_ADMIN["username"],
            hashed_password=get_password_hash(DEFAULT_ADMIN["password"]),
            full_name=DEFAULT_ADMIN["full_name"],
            email=DEFAULT_ADMIN["email"],
            avatar_url=DEFAULT_ADMIN["avatar_url"],
            role=DEFAULT_ADMIN["role"],
        )
        db.add(admin)
        await db.commit()
        await db.refresh(admin)
        print("Created default admin: username=admin password=admin123")
        return admin

    admin.full_name = DEFAULT_ADMIN["full_name"]
    admin.email = DEFAULT_ADMIN["email"]
    admin.avatar_url = DEFAULT_ADMIN["avatar_url"]
    admin.role = DEFAULT_ADMIN["role"]
    await db.commit()
    await db.refresh(admin)
    print("Default admin already exists; refreshed profile fields.")
    return admin


async def upsert_regions_and_zones(db: AsyncSession) -> Dict[str, Region]:
    """Ensure regions and sub-zones exist. Returns region map by name."""
    region_map: Dict[str, Region] = {}
    created_regions = 0
    created_zones = 0

    for region_name, zones in REGION_ZONE_MAP.items():
        region_result = await db.execute(select(Region).where(Region.name == region_name))
        region = region_result.scalar_one_or_none()

        if region is None:
            region = Region(name=region_name, image=None)
            db.add(region)
            await db.flush()
            created_regions += 1

        region_map[region_name] = region

        for zone_name in zones:
            zone_result = await db.execute(
                select(SubZone).where(
                    SubZone.region_id == region.id,
                    SubZone.name == zone_name,
                )
            )
            zone = zone_result.scalar_one_or_none()
            if zone is None:
                db.add(SubZone(region_id=region.id, name=zone_name, image=None))
                created_zones += 1

    await db.commit()
    print(f"Regions ensured: {len(REGION_ZONE_MAP)} (new: {created_regions})")
    print(f"Sub-zones ensured: {sum(len(v) for v in REGION_ZONE_MAP.values())} (new: {created_zones})")
    return region_map


async def upsert_sample_posts(db: AsyncSession, admin_id: str) -> None:
    """Insert sample posts by title if they do not already exist."""
    created_posts = 0

    for post_data in SAMPLE_POSTS:
        result = await db.execute(select(Post).where(Post.title == post_data["title"]))
        existing = result.scalar_one_or_none()
        if existing is not None:
            continue

        db.add(
            Post(
                **post_data,
                admin_id=admin_id,
            )
        )
        created_posts += 1

    await db.commit()
    print(f"Sample posts ensured: {len(SAMPLE_POSTS)} (new: {created_posts})")


async def seed_database() -> None:
    """Run all seed steps."""
    print("=" * 60)
    print("Logic NewsAct database seeding")
    print("=" * 60)

    if settings.is_supabase:
        host = settings.DATABASE_URL.split("@")[-1].split("/")[0]
        print(f"Database target: Supabase ({host})")
    else:
        print("Database target: Local PostgreSQL/MySQL-compatible URL")

    try:
        await init_db()
        print("Database tables initialized.")
    except Exception as exc:
        print(f"Failed to initialize database tables: {exc}")
        print("Check DATABASE_URL and database network/access settings.")
        sys.exit(1)

    async with AsyncSessionLocal() as db:
        try:
            admin = await upsert_default_admin(db)
            await upsert_regions_and_zones(db)
            await upsert_sample_posts(db, admin.id)
        except Exception as exc:
            await db.rollback()
            print(f"Seeding failed: {exc}")
            raise

    print("=" * 60)
    print("Seeding completed.")
    print("Default admin login: username=admin password=admin123")
    print("Change the default password in production.")
    print("=" * 60)


if __name__ == "__main__":
    asyncio.run(seed_database())
