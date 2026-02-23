"""
SQLAlchemy database models.
"""
import uuid
from datetime import datetime, timezone
from typing import List, Optional

from sqlalchemy import (
    Column, String, Text, Integer, Boolean, DateTime, ForeignKey, 
    func, Index
)
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship, Mapped, mapped_column

from app.db.database import Base


def generate_uuid() -> str:
    """Generate a UUID string."""
    return str(uuid.uuid4())


def utc_now() -> datetime:
    """Return current UTC datetime."""
    return datetime.now(timezone.utc)


class Admin(Base):
    """Administrator accounts model."""
    __tablename__ = "admins"
    
    id: Mapped[str] = mapped_column(
        String(36), 
        primary_key=True, 
        default=generate_uuid
    )
    username: Mapped[str] = mapped_column(
        String(50), 
        unique=True, 
        nullable=False,
        index=True
    )
    hashed_password: Mapped[str] = mapped_column(Text, nullable=False)
    full_name: Mapped[str] = mapped_column(String(100), nullable=False)
    email: Mapped[str] = mapped_column(String(100), nullable=False)
    avatar_url: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    role: Mapped[str] = mapped_column(
        String(20), 
        default="Editor",
        nullable=False
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False
    )
    
    # Relationships
    posts: Mapped[List["Post"]] = relationship(
        "Post", 
        back_populates="admin",
        lazy="selectin"
    )
    
    def __repr__(self) -> str:
        return f"<Admin(id={self.id}, username={self.username})>"


class Region(Base):
    """Geopolitical regions model."""
    __tablename__ = "regions"
    
    id: Mapped[str] = mapped_column(
        String(36), 
        primary_key=True, 
        default=generate_uuid
    )
    name: Mapped[str] = mapped_column(String(100), nullable=False, unique=True)
    image: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False
    )
    
    # Relationships
    sub_zones: Mapped[List["SubZone"]] = relationship(
        "SubZone", 
        back_populates="region",
        cascade="all, delete-orphan",
        lazy="selectin"
    )
    
    def __repr__(self) -> str:
        return f"<Region(id={self.id}, name={self.name})>"


class SubZone(Base):
    """Sub-zones/states within regions model."""
    __tablename__ = "sub_zones"
    
    id: Mapped[str] = mapped_column(
        String(36), 
        primary_key=True, 
        default=generate_uuid
    )
    region_id: Mapped[str] = mapped_column(
        String(36), 
        ForeignKey("regions.id", ondelete="CASCADE"),
        nullable=False,
        index=True
    )
    name: Mapped[str] = mapped_column(String(100), nullable=False)
    image: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False
    )
    
    # Relationships
    region: Mapped["Region"] = relationship(
        "Region", 
        back_populates="sub_zones"
    )
    
    def __repr__(self) -> str:
        return f"<SubZone(id={self.id}, name={self.name})>"


class Post(Base):
    """News posts/dispatches model."""
    __tablename__ = "posts"
    
    id: Mapped[str] = mapped_column(
        String(36), 
        primary_key=True, 
        default=generate_uuid
    )
    title: Mapped[str] = mapped_column(String(255), nullable=False, index=True)
    excerpt: Mapped[str] = mapped_column(Text, nullable=False)
    content: Mapped[str] = mapped_column(Text, nullable=False)
    author: Mapped[str] = mapped_column(String(100), nullable=False)
    date: Mapped[str] = mapped_column(String(50), nullable=False)
    category: Mapped[str] = mapped_column(
        String(100), 
        nullable=False,
        index=True
    )
    image_url: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    read_time: Mapped[str] = mapped_column(
        String(20), 
        default="5 min read",
        nullable=False
    )
    views: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    is_breaking: Mapped[bool] = mapped_column(
        Boolean, 
        default=False, 
        nullable=False,
        index=True
    )
    is_editors_choice: Mapped[bool] = mapped_column(
        Boolean, 
        default=False, 
        nullable=False,
        index=True
    )
    is_top_news: Mapped[bool] = mapped_column(
        Boolean, 
        default=False, 
        nullable=False,
        index=True
    )
    is_trending: Mapped[bool] = mapped_column(
        Boolean, 
        default=False, 
        nullable=False,
        index=True
    )
    admin_id: Mapped[Optional[str]] = mapped_column(
        String(36),
        ForeignKey("admins.id", ondelete="SET NULL"),
        nullable=True
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
        index=True
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False
    )
    
    # Relationships
    admin: Mapped[Optional["Admin"]] = relationship(
        "Admin", 
        back_populates="posts"
    )
    
    # Indexes for common queries
    __table_args__ = (
        Index('idx_posts_breaking_created', 'is_breaking', 'created_at'),
        Index('idx_posts_editors_choice', 'is_editors_choice', 'created_at'),
        Index('idx_posts_top_news', 'is_top_news', 'created_at'),
        Index('idx_posts_trending', 'is_trending', 'created_at'),
        Index('idx_posts_category_created', 'category', 'created_at'),
    )
    
    def __repr__(self) -> str:
        return f"<Post(id={self.id}, title={self.title[:30]}...)>"
