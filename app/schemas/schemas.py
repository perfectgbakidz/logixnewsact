"""
Pydantic schemas for request/response validation.
"""
from datetime import datetime
from typing import Optional, List
from pydantic import BaseModel, Field, EmailStr, ConfigDict, field_validator
import bleach


# ============== Base Schemas ==============

class BaseSchema(BaseModel):
    """Base schema with common configuration."""
    model_config = ConfigDict(from_attributes=True, populate_by_name=True)


# ============== Admin Schemas ==============

class AdminBase(BaseSchema):
    """Base admin schema."""
    username: str = Field(..., min_length=3, max_length=50)
    full_name: str = Field(..., min_length=1, max_length=100)
    email: EmailStr
    avatar_url: Optional[str] = None
    role: str = Field(default="Editor", max_length=20)


class AdminCreate(AdminBase):
    """Schema for creating a new admin."""
    password: str = Field(..., min_length=8, max_length=100)


class AdminUpdate(BaseSchema):
    """Schema for updating admin details."""
    full_name: Optional[str] = Field(None, max_length=100)
    email: Optional[EmailStr] = None
    avatar_url: Optional[str] = None
    role: Optional[str] = Field(None, max_length=20)


class AdminInDB(AdminBase):
    """Schema for admin in database (includes hashed password)."""
    id: str
    hashed_password: str
    created_at: datetime


class AdminResponse(AdminBase):
    """Schema for admin response (excludes sensitive data)."""
    id: str
    created_at: datetime


# ============== Region Schemas ==============

class RegionBase(BaseSchema):
    """Base region schema."""
    name: str = Field(..., min_length=1, max_length=100)
    image: Optional[str] = None


class RegionCreate(RegionBase):
    """Schema for creating a new region."""
    pass


class RegionUpdate(BaseSchema):
    """Schema for updating a region."""
    name: Optional[str] = Field(None, max_length=100)
    image: Optional[str] = None


class RegionResponse(RegionBase):
    """Schema for region response."""
    id: str
    created_at: datetime


class RegionWithZonesResponse(RegionResponse):
    """Schema for region response with sub-zones."""
    sub_zones: List["SubZoneResponse"] = []


# ============== SubZone Schemas ==============

class SubZoneBase(BaseSchema):
    """Base sub-zone schema."""
    name: str = Field(..., min_length=1, max_length=100)
    image: Optional[str] = None


class SubZoneCreate(SubZoneBase):
    """Schema for creating a new sub-zone."""
    pass


class SubZoneUpdate(BaseSchema):
    """Schema for updating a sub-zone."""
    name: Optional[str] = Field(None, max_length=100)
    image: Optional[str] = None


class SubZoneResponse(SubZoneBase):
    """Schema for sub-zone response."""
    id: str
    region_id: str
    created_at: datetime


# ============== Post Schemas ==============

def sanitize_html(content: str) -> str:
    """Sanitize HTML content to prevent XSS attacks."""
    allowed_tags = [
        'p', 'br', 'strong', 'b', 'em', 'i', 'u', 'h1', 'h2', 'h3', 
        'h4', 'h5', 'h6', 'ul', 'ol', 'li', 'a', 'img', 'blockquote',
        'code', 'pre', 'span', 'div'
    ]
    allowed_attrs = {
        '*': ['class', 'style'],
        'a': ['href', 'title', 'target'],
        'img': ['src', 'alt', 'title', 'width', 'height']
    }
    return bleach.clean(content, tags=allowed_tags, attributes=allowed_attrs, strip=True)


class PostBase(BaseSchema):
    """Base post schema."""
    title: str = Field(..., min_length=1, max_length=255)
    excerpt: str = Field(..., min_length=1)
    content: str = Field(..., min_length=1)
    author: str = Field(..., min_length=1, max_length=100)
    date: str = Field(
        default_factory=lambda: datetime.now().strftime("%B %d, %Y"),
        max_length=50
    )
    category: str = Field(..., min_length=1, max_length=100)
    image_url: Optional[str] = Field(default=None, validation_alias="imageUrl")
    read_time: str = Field(
        default="5 min read",
        max_length=20,
        validation_alias="readTime"
    )
    is_breaking: bool = Field(default=False, validation_alias="isBreaking")
    is_editors_choice: bool = Field(default=False, validation_alias="isEditorsChoice")
    is_top_news: bool = Field(default=False, validation_alias="isTopNews")
    is_trending: bool = Field(default=False, validation_alias="isTrending")


class PostCreate(PostBase):
    """Schema for creating a new post."""

    @field_validator("content")
    @classmethod
    def validate_content(cls, value: str) -> str:
        """Sanitize content HTML."""
        return sanitize_html(value)


class PostUpdate(BaseSchema):
    """Schema for updating a post."""
    title: Optional[str] = Field(None, max_length=255)
    excerpt: Optional[str] = None
    content: Optional[str] = None
    author: Optional[str] = Field(None, max_length=100)
    date: Optional[str] = Field(None, max_length=50)
    category: Optional[str] = Field(None, max_length=100)
    image_url: Optional[str] = Field(default=None, validation_alias="imageUrl")
    read_time: Optional[str] = Field(
        default=None,
        max_length=20,
        validation_alias="readTime"
    )
    is_breaking: Optional[bool] = Field(default=None, validation_alias="isBreaking")
    is_editors_choice: Optional[bool] = Field(default=None, validation_alias="isEditorsChoice")
    is_top_news: Optional[bool] = Field(default=None, validation_alias="isTopNews")
    is_trending: Optional[bool] = Field(default=None, validation_alias="isTrending")
    
    @field_validator("content")
    @classmethod
    def validate_content(cls, v: Optional[str]) -> Optional[str]:
        """Sanitize content HTML if provided."""
        if v:
            return sanitize_html(v)
        return v


class PostResponse(PostBase):
    """Schema for post response."""
    id: str
    views: int
    created_at: datetime
    updated_at: datetime


class PostDetailResponse(PostResponse):
    """Schema for detailed post response."""
    admin: Optional[AdminResponse] = None


class PostListResponse(BaseSchema):
    """Schema for paginated post list response."""
    items: List[PostResponse]
    total: int
    page: int
    page_size: int
    total_pages: int


# ============== Auth Schemas ==============

class Token(BaseSchema):
    """Schema for JWT token response."""
    access_token: str
    token_type: str = "bearer"
    expires_in: int


class TokenPayload(BaseSchema):
    """Schema for JWT token payload."""
    sub: Optional[str] = None
    exp: Optional[datetime] = None


class LoginRequest(BaseSchema):
    """Schema for login request."""
    username: str
    password: str


# ============== Analytics Schemas ==============

class AnalyticsResponse(BaseSchema):
    """Schema for analytics response."""
    total_posts: int
    total_views: int
    total_regions: int
    total_sub_zones: int
    total_admins: int
    breaking_news_count: int
    editors_choice_count: int
    top_news_count: int
    trending_count: int


# Resolve forward references
RegionWithZonesResponse.model_rebuild()
