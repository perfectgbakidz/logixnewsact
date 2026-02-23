"""
Seed data script for Logic NewsAct backend.
Run this script to populate the database with initial data.

Supports both local PostgreSQL and Supabase.
"""
import asyncio
import os
import sys
from datetime import datetime, timezone

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.db.database import AsyncSessionLocal, init_db
from app.models.models import Admin, Region, SubZone, Post
from app.core.security import get_password_hash
from app.core.config import settings


async def check_admin_exists(db: AsyncSession) -> bool:
    """Check if admin user already exists."""
    result = await db.execute(select(Admin).where(Admin.username == "admin"))
    return result.scalar_one_or_none() is not None


async def create_initial_admin(db: AsyncSession):
    """Create initial admin user."""
    # Check if admin already exists
    if await check_admin_exists(db):
        print("⚠️  Admin user 'admin' already exists, skipping...")
        result = await db.execute(select(Admin).where(Admin.username == "admin"))
        return result.scalar_one()

    admin = Admin(
        username="admin",
        hashed_password=get_password_hash("admin123"),  # Change in production!
        full_name="System Administrator",
        email="admin@logicnewsact.ng",
        role="Editor-in-Chief"
    )
    db.add(admin)
    await db.commit()
    print("✓ Created initial admin user (username: admin, password: admin123)")
    return admin


async def create_regions(db: AsyncSession):
    """Create initial regions."""
    regions_data = [
        {"name": "IbileLogic", "image": None},
        {"name": "ArewaLogic", "image": None},
        {"name": "NaijaLogic", "image": None},
        {"name": "NigerDeltaLogic", "image": None},
    ]
    
    regions = []
    for data in regions_data:
        region = Region(**data)
        db.add(region)
        regions.append(region)
    
    await db.commit()
    print(f"✓ Created {len(regions)} regions")
    return regions


async def create_sub_zones(db: AsyncSession, regions):
    """Create sub-zones for regions."""
    zones_data = {
        "IbileLogic": ["Lagos", "Ogun", "Oyo", "Osun", "Ekiti", "Ondo"],
        "ArewaLogic": ["Kano", "Kaduna", "Katsina", "Sokoto", "Zamfara"],
        "NaijaLogic": ["Abuja", "Nasarawa", "Niger", "Plateau"],
        "NigerDeltaLogic": ["Rivers", "Delta", "Bayelsa", "Akwa Ibom"],
    }
    
    zones_count = 0
    for region in regions:
        zone_names = zones_data.get(region.name, [])
        for zone_name in zone_names:
            zone = SubZone(
                region_id=region.id,
                name=zone_name,
                image=None
            )
            db.add(zone)
            zones_count += 1
    
    await db.commit()
    print(f"✓ Created {zones_count} sub-zones")


async def create_sample_posts(db: AsyncSession, admin_id: str):
    """Create sample posts."""
    posts_data = [
        {
            "title": "Breaking: Major Infrastructure Project Announced",
            "excerpt": "Government unveils ambitious new infrastructure plan for the region.",
            "content": "<p>In a landmark announcement today, government officials revealed a comprehensive infrastructure development plan...</p>",
            "author": "John Doe",
            "date": "January 15, 2024",
            "category": "IbileLogic",
            "read_time": "5 min read",
            "is_breaking": True,
            "is_top_news": True,
        },
        {
            "title": "Tech Innovation Hub Opens in Lagos",
            "excerpt": "New technology center aims to boost local startup ecosystem.",
            "content": "<p>A state-of-the-art technology innovation hub was inaugurated yesterday...</p>",
            "author": "Jane Smith",
            "date": "January 14, 2024",
            "category": "IbileLogic",
            "read_time": "4 min read",
            "is_trending": True,
        },
        {
            "title": "Agricultural Reform Shows Promise",
            "excerpt": "New farming initiatives report early success in northern regions.",
            "content": "<p>Recent agricultural reforms have shown promising results...</p>",
            "author": "Ahmed Musa",
            "date": "January 13, 2024",
            "category": "ArewaLogic",
            "read_time": "6 min read",
            "is_editors_choice": True,
        },
        {
            "title": "Education Sector Receives Major Funding",
            "excerpt": "New budget allocation aims to improve schools across the nation.",
            "content": "<p>The education sector has received a significant boost...</p>",
            "author": "Sarah Johnson",
            "date": "January 12, 2024",
            "category": "NaijaLogic",
            "read_time": "5 min read",
            "is_trending": True,
        },
        {
            "title": "Oil Industry Developments in Niger Delta",
            "excerpt": "New policies aim to benefit local communities in oil-producing regions.",
            "content": "<p>The Niger Delta region is seeing new developments...</p>",
            "author": "Peter Okon",
            "date": "January 11, 2024",
            "category": "NigerDeltaLogic",
            "read_time": "7 min read",
            "is_top_news": True,
        },
    ]
    
    for data in posts_data:
        post = Post(
            **data,
            admin_id=admin_id,
            views=0,
            image_url=None
        )
        db.add(post)
    
    await db.commit()
    print(f"✓ Created {len(posts_data)} sample posts")


async def seed_database():
    """Main function to seed the database."""
    print("=" * 60)
    print("Logic NewsAct - Database Seeding")
    print("=" * 60)

    # Show database info
    if settings.is_supabase:
        print("\n📡 Using Supabase database")
        print(f"   URL: {settings.DATABASE_URL.split('@')[1].split('/')[0]}")
    else:
        print("\n🐘 Using local PostgreSQL database")

    # Initialize database tables
    print("\nInitializing database tables...")
    try:
        await init_db()
        print("✓ Tables created successfully")
    except Exception as e:
        print(f"\n✗ Error creating tables: {e}")
        print("\nTroubleshooting:")
        if settings.is_supabase:
            print("  - Check your Supabase connection string in .env")
            print("  - Ensure your IP is allowed in Supabase Dashboard > Database > Network")
            print("  - For IPv4-only networks, enable the IPv4 addon in Supabase")
        else:
            print("  - Ensure PostgreSQL is running locally")
            print("  - Check your DATABASE_URL in .env")
        sys.exit(1)

    async with AsyncSessionLocal() as db:
        try:
            # Create admin
            admin = await create_initial_admin(db)

            # Create regions
            regions = await create_regions(db)

            # Create sub-zones
            await create_sub_zones(db, regions)

            # Create sample posts
            await create_sample_posts(db, admin.id)

            print("\n" + "=" * 60)
            print("✓ Database seeding completed successfully!")
            print("=" * 60)
            print("\nInitial Admin Credentials:")
            print("  Username: admin")
            print("  Password: admin123")
            print("\n⚠️  IMPORTANT: Change the default password in production!")
            print("=" * 60)

        except Exception as e:
            print(f"\n✗ Error seeding database: {e}")
            await db.rollback()
            raise


if __name__ == "__main__":
    asyncio.run(seed_database())
