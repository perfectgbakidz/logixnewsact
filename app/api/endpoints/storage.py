"""
Storage API endpoints for file uploads.
"""
from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, status, UploadFile, File, Form

from app.api.deps import get_current_admin
from app.services.storage import upload_image, delete_image
from app.core.config import settings


router = APIRouter()

ALLOWED_IMAGE_MIME_TYPES = {"image/jpeg", "image/png", "image/webp"}


def _detect_image_mime(file_bytes: bytes) -> Optional[str]:
    """Detect supported image MIME type by magic bytes."""
    if file_bytes.startswith(b"\xff\xd8\xff"):
        return "image/jpeg"
    if file_bytes.startswith(b"\x89PNG\r\n\x1a\n"):
        return "image/png"
    if len(file_bytes) > 12 and file_bytes[:4] == b"RIFF" and file_bytes[8:12] == b"WEBP":
        return "image/webp"
    return None


def _validate_image_upload(
    file: UploadFile,
    content: bytes,
    max_size_mb: int
) -> str:
    """Validate image MIME and size, returning detected MIME type."""
    if len(content) > max_size_mb * 1024 * 1024:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"File too large. Maximum size is {max_size_mb}MB."
        )

    detected_mime = _detect_image_mime(content)
    declared_mime = file.content_type or ""

    if detected_mime is None or declared_mime not in ALLOWED_IMAGE_MIME_TYPES:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid image file. Allowed types: image/jpeg, image/png, image/webp"
        )

    if detected_mime != declared_mime:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="File MIME type mismatch."
        )

    return detected_mime


@router.post("/upload", status_code=status.HTTP_201_CREATED)
async def upload_file(
    file: UploadFile = File(..., description="File to upload"),
    folder: str = Form(default="posts", description="Folder path within bucket"),
    bucket: str = Form(default=settings.SUPABASE_STORAGE_BUCKET, description="Storage bucket name"),
    current_admin = Depends(get_current_admin)
):
    """
    Upload a file to storage (Admin only).

    Supports images (jpg, png, gif, webp, svg).

    Args:
        file: File to upload
        folder: Folder path within bucket (default: "images")
        bucket: Storage bucket name (default: "public")

    Returns:
        dict: Upload result with URL and path
    """
    content = await file.read()
    _validate_image_upload(file=file, content=content, max_size_mb=5)

    # Upload file
    result = await upload_image(
        file_content=content,
        filename=file.filename or "upload.jpg",
        folder=folder,
        bucket=bucket
    )

    if not result.get("success"):
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=result.get("error", "Failed to upload file")
        )

    return {
        "success": True,
        "url": result["url"],
        "path": result["path"],
        "bucket": result["bucket"],
        "provider": result["provider"]
    }


@router.delete("/upload/delete")
async def delete_file(
    url: str,
    bucket: str = settings.SUPABASE_STORAGE_BUCKET,
    current_admin = Depends(get_current_admin)
):
    """
    Delete a file from storage (Admin only).

    Args:
        url: File URL to delete
        bucket: Storage bucket name (default: "public")

    Returns:
        dict: Deletion result
    """
    success = await delete_image(url, bucket)

    if not success:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to delete file"
        )

    return {
        "success": True,
        "message": "File deleted successfully"
    }


@router.post("/upload/avatar", status_code=status.HTTP_201_CREATED)
async def upload_avatar(
    file: UploadFile = File(..., description="Avatar image to upload"),
    current_admin = Depends(get_current_admin)
):
    """
    Upload admin avatar (Admin only).

    Args:
        file: Avatar image file

    Returns:
        dict: Upload result with avatar URL
    """
    content = await file.read()
    _validate_image_upload(file=file, content=content, max_size_mb=2)

    # Upload to avatars folder
    result = await upload_image(
        file_content=content,
        filename=file.filename or "avatar.jpg",
        folder="avatars",
        bucket=settings.SUPABASE_STORAGE_BUCKET
    )

    if not result.get("success"):
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=result.get("error", "Failed to upload avatar")
        )

    return {
        "success": True,
        "avatar_url": result["url"],
        "path": result["path"]
    }


@router.post("/upload/post-image", status_code=status.HTTP_201_CREATED)
async def upload_post_image(
    file: UploadFile = File(..., description="Post image to upload"),
    current_admin = Depends(get_current_admin)
):
    """
    Upload post image (Admin only).

    Args:
        file: Post image file

    Returns:
        dict: Upload result with image URL
    """
    content = await file.read()
    _validate_image_upload(file=file, content=content, max_size_mb=5)

    # Upload to posts folder
    result = await upload_image(
        file_content=content,
        filename=file.filename or "post.jpg",
        folder="posts",
        bucket=settings.SUPABASE_STORAGE_BUCKET
    )

    if not result.get("success"):
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=result.get("error", "Failed to upload image")
        )

    return {
        "success": True,
        "image_url": result["url"],
        "path": result["path"]
    }
