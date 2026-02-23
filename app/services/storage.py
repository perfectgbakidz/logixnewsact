"""
Supabase Storage service for file uploads.
Supports both Supabase Storage and local file storage fallback.
"""
import os
import uuid
import aiofiles
from typing import Optional, BinaryIO
from datetime import datetime
from pathlib import Path

from app.core.config import settings

# Try to import supabase, but don't fail if not available
try:
    from supabase import create_client, Client
    SUPABASE_AVAILABLE = True
except ImportError:
    SUPABASE_AVAILABLE = False


class StorageService:
    """Storage service for file uploads."""

    def __init__(self):
        self.supabase: Optional[Client] = None
        self.use_supabase = False
        self.local_storage_path = Path("uploads")

        # Initialize Supabase client if credentials are available
        if SUPABASE_AVAILABLE and settings.SUPABASE_URL and settings.SUPABASE_SERVICE_KEY:
            try:
                self.supabase = create_client(
                    settings.SUPABASE_URL,
                    settings.SUPABASE_SERVICE_KEY
                )
                self.use_supabase = True
            except Exception as e:
                print(f"Warning: Could not initialize Supabase client: {e}")
                self.use_supabase = False

        # Ensure local storage directory exists
        if not self.use_supabase:
            self.local_storage_path.mkdir(parents=True, exist_ok=True)

    def _generate_filename(self, original_filename: str, folder: str) -> str:
        """Generate a unique filename."""
        ext = original_filename.split('.')[-1] if '.' in original_filename else ''
        unique_id = str(uuid.uuid4())[:8]
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        return f"{folder}/{timestamp}_{unique_id}.{ext}" if ext else f"{folder}/{timestamp}_{unique_id}"

    async def upload_file(
        self,
        file_content: bytes,
        filename: str,
        bucket: str = "public",
        folder: str = "images",
        content_type: Optional[str] = None
    ) -> dict:
        """
        Upload a file to storage.

        Args:
            file_content: File bytes to upload
            filename: Original filename
            bucket: Storage bucket name
            folder: Folder path within bucket
            content_type: MIME type of the file

        Returns:
            dict: Upload result with 'url', 'path', and 'bucket'
        """
        storage_path = self._generate_filename(filename, folder)

        if self.use_supabase:
            return await self._upload_to_supabase(
                file_content, storage_path, bucket, content_type
            )
        else:
            return await self._upload_local(
                file_content, storage_path, bucket
            )

    async def _upload_to_supabase(
        self,
        file_content: bytes,
        storage_path: str,
        bucket: str,
        content_type: Optional[str] = None
    ) -> dict:
        """Upload file to Supabase Storage."""
        try:
            # Ensure bucket exists
            try:
                self.supabase.storage.get_bucket(bucket)
            except Exception:
                # Try to create bucket if it doesn't exist
                try:
                    self.supabase.storage.create_bucket(
                        bucket,
                        options={"public": True}
                    )
                except Exception as e:
                    print(f"Warning: Could not create bucket: {e}")

            # Upload file
            result = self.supabase.storage.from_(bucket).upload(
                path=storage_path,
                file=file_content,
                file_options={"content-type": content_type or "application/octet-stream"}
            )

            # Get public URL
            public_url = self.supabase.storage.from_(bucket).get_public_url(storage_path)

            return {
                "success": True,
                "url": public_url,
                "path": storage_path,
                "bucket": bucket,
                "provider": "supabase"
            }

        except Exception as e:
            # Fallback to local storage
            print(f"Supabase upload failed, falling back to local: {e}")
            return await self._upload_local(file_content, storage_path, bucket)

    async def _upload_local(
        self,
        file_content: bytes,
        storage_path: str,
        bucket: str
    ) -> dict:
        """Upload file to local storage."""
        bucket_path = self.local_storage_path / bucket
        bucket_path.mkdir(parents=True, exist_ok=True)

        file_path = bucket_path / storage_path.replace("/", os.sep)
        file_path.parent.mkdir(parents=True, exist_ok=True)

        async with aiofiles.open(file_path, 'wb') as f:
            await f.write(file_content)

        # Return relative URL
        return {
            "success": True,
            "url": f"/uploads/{bucket}/{storage_path}",
            "path": str(file_path),
            "bucket": bucket,
            "provider": "local"
        }

    async def delete_file(self, path: str, bucket: str = "public") -> bool:
        """
        Delete a file from storage.

        Args:
            path: File path or URL
            bucket: Storage bucket name

        Returns:
            bool: True if deleted successfully
        """
        if self.use_supabase:
            try:
                # Extract path from URL if needed
                if path.startswith("http"):
                    # Parse path from Supabase URL
                    path = path.split(f"/{bucket}/")[-1]

                self.supabase.storage.from_(bucket).remove([path])
                return True
            except Exception as e:
                print(f"Error deleting from Supabase: {e}")
                return False
        else:
            # Local file deletion
            try:
                if path.startswith("/uploads/"):
                    path = path.replace("/uploads/", "")

                file_path = self.local_storage_path / path.replace("/", os.sep)
                if file_path.exists():
                    file_path.unlink()
                    return True
                return False
            except Exception as e:
                print(f"Error deleting local file: {e}")
                return False

    def get_public_url(self, path: str, bucket: str = "public") -> str:
        """Get public URL for a file."""
        if self.use_supabase:
            return self.supabase.storage.from_(bucket).get_public_url(path)
        else:
            return f"/uploads/{bucket}/{path}"


# Global storage service instance
storage_service = StorageService()


# Convenience functions
async def upload_image(
    file_content: bytes,
    filename: str,
    folder: str = "images",
    bucket: str = "public"
) -> dict:
    """Upload an image file."""
    # Determine content type from filename
    ext = filename.split('.')[-1].lower() if '.' in filename else ''
    content_type_map = {
        'jpg': 'image/jpeg',
        'jpeg': 'image/jpeg',
        'png': 'image/png',
        'gif': 'image/gif',
        'webp': 'image/webp',
        'svg': 'image/svg+xml'
    }
    content_type = content_type_map.get(ext, 'image/jpeg')

    return await storage_service.upload_file(
        file_content=file_content,
        filename=filename,
        bucket=bucket,
        folder=folder,
        content_type=content_type
    )


async def delete_image(url: str, bucket: str = "public") -> bool:
    """Delete an image by URL."""
    return await storage_service.delete_file(url, bucket)
