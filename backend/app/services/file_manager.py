"""
Secure file manager with automatic cleanup and TTL enforcement
Files are temporary and deleted after processing or TTL expiration
"""
import os
import time
import logging
from pathlib import Path
from typing import Optional, Tuple
from datetime import datetime, timedelta
from app.config import settings

logger = logging.getLogger(__name__)


class FileManager:
    """Manages temporary file storage with automatic cleanup"""

    def __init__(self):
        """Initialize file manager"""
        self.upload_dir = Path(settings.upload_dir)
        self.upload_dir.mkdir(exist_ok=True, parents=True)
        logger.info(f"📁 File manager initialized: {self.upload_dir}")

    def save_upload(self, document_id: str, content: bytes, extension: str) -> Tuple[Path, float]:
        """
        Save uploaded file with metadata for TTL tracking

        Args:
            document_id: Unique document identifier
            content: File content bytes
            extension: File extension (e.g., '.pdf')

        Returns:
            Tuple of (file_path, size_mb)
        """
        file_path = self.upload_dir / f"{document_id}{extension}"

        # Write file
        with open(file_path, "wb") as f:
            f.write(content)

        size_mb = len(content) / (1024 * 1024)

        logger.info(f"💾 Saved file: {file_path.name} ({size_mb:.2f} MB)")
        logger.info(f"⏱️  File will auto-delete after {settings.file_ttl}s ({settings.file_ttl // 60} min)")

        return file_path, size_mb

    def get_file_path(self, document_id: str) -> Optional[Path]:
        """
        Get file path if it exists

        Args:
            document_id: Unique document identifier

        Returns:
            Path object or None if not found
        """
        # Check all possible extensions
        for ext in ['.pdf', '.jpg', '.jpeg', '.png', '.tiff']:
            file_path = self.upload_dir / f"{document_id}{ext}"
            if file_path.exists():
                return file_path
        return None

    def delete_file(self, document_id: str) -> bool:
        """
        Delete file for a specific document

        Args:
            document_id: Unique document identifier

        Returns:
            True if deleted, False if not found
        """
        file_path = self.get_file_path(document_id)

        if not file_path:
            logger.warning(f"⚠️  File not found for deletion: {document_id}")
            return False

        try:
            file_path.unlink()
            logger.info(f"🗑️  Deleted file: {file_path.name}")
            return True
        except Exception as e:
            logger.error(f"❌ Failed to delete {file_path}: {e}")
            return False

    def delete_file_if_exists(self, file_path: Path) -> bool:
        """
        Delete specific file if it exists

        Args:
            file_path: Path to file

        Returns:
            True if deleted, False otherwise
        """
        if not file_path or not isinstance(file_path, Path):
            return False

        try:
            if file_path.exists():
                file_path.unlink()
                logger.info(f"🗑️  Deleted file: {file_path.name}")
                return True
            return False
        except Exception as e:
            logger.error(f"❌ Failed to delete {file_path}: {e}")
            return False

    def cleanup_expired_files(self) -> int:
        """
        Clean up files older than TTL

        Returns:
            Number of files deleted
        """
        if not self.upload_dir.exists():
            return 0

        try:
            now = time.time()
            ttl = settings.file_ttl
            deleted_count = 0

            for file_path in self.upload_dir.glob("*"):
                if not file_path.is_file():
                    continue

                # Check file age
                file_age = now - file_path.stat().st_mtime

                if file_age > ttl:
                    try:
                        file_path.unlink()
                        deleted_count += 1
                        logger.info(f"🗑️  Cleaned up expired file: {file_path.name} (age: {file_age:.0f}s)")
                    except Exception as e:
                        logger.error(f"❌ Failed to delete {file_path.name}: {e}")

            if deleted_count > 0:
                logger.info(f"🧹 Cleanup completed: {deleted_count} expired files deleted")

            return deleted_count

        except Exception as e:
            logger.error(f"❌ Cleanup failed: {e}")
            return 0

    def get_file_stats(self) -> dict:
        """
        Get statistics about stored files

        Returns:
            Dictionary with file stats
        """
        if not self.upload_dir.exists():
            return {"total_files": 0, "total_size_mb": 0}

        try:
            files = list(self.upload_dir.glob("*"))
            total_size = sum(f.stat().st_size for f in files if f.is_file())

            return {
                "total_files": len([f for f in files if f.is_file()]),
                "total_size_mb": round(total_size / (1024 * 1024), 2),
                "upload_dir": str(self.upload_dir),
            }
        except Exception as e:
            logger.error(f"❌ Failed to get file stats: {e}")
            return {"error": str(e)}

    def get_file_age(self, document_id: str) -> Optional[float]:
        """
        Get age of file in seconds

        Args:
            document_id: Unique document identifier

        Returns:
            Age in seconds or None if not found
        """
        file_path = self.get_file_path(document_id)

        if not file_path:
            return None

        try:
            return time.time() - file_path.stat().st_mtime
        except Exception as e:
            logger.error(f"❌ Failed to get file age: {e}")
            return None

    def is_file_expired(self, document_id: str) -> bool:
        """
        Check if file has exceeded TTL

        Args:
            document_id: Unique document identifier

        Returns:
            True if expired, False otherwise
        """
        age = self.get_file_age(document_id)

        if age is None:
            return True  # File doesn't exist = expired

        return age > settings.file_ttl


# Global instance
_file_manager: Optional[FileManager] = None


def get_file_manager() -> FileManager:
    """Get or create FileManager singleton"""
    global _file_manager
    if _file_manager is None:
        _file_manager = FileManager()
    return _file_manager
