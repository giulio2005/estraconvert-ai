"""
Redis service for caching document metadata and OCR results
Provides automatic TTL and JSON serialization
"""
import json
import logging
from typing import Optional, Dict, Any
from redis import Redis, ConnectionError as RedisConnectionError
from app.config import settings

logger = logging.getLogger(__name__)


class RedisService:
    """Redis cache service with automatic TTL and JSON handling"""

    def __init__(self):
        """Initialize Redis connection"""
        self.redis: Optional[Redis] = None
        self._connect()

    def _connect(self):
        """Establish Redis connection with retry"""
        try:
            self.redis = Redis(
                host=settings.redis_host,
                port=settings.redis_port,
                db=settings.redis_db,
                password=settings.redis_password if settings.redis_password else None,
                decode_responses=True,  # Auto decode bytes to strings
                socket_connect_timeout=5,
                socket_timeout=5,
            )
            # Test connection
            self.redis.ping()
            logger.info(f"✅ Redis connected: {settings.redis_host}:{settings.redis_port}")
        except RedisConnectionError as e:
            logger.error(f"❌ Redis connection failed: {e}")
            logger.warning("⚠️  Running without Redis cache (fallback to memory)")
            self.redis = None
        except Exception as e:
            logger.error(f"❌ Redis initialization error: {e}")
            self.redis = None

    def is_available(self) -> bool:
        """Check if Redis is available"""
        if not self.redis:
            return False
        try:
            return self.redis.ping()
        except:
            return False

    def set_document_metadata(self, document_id: str, metadata: Dict[str, Any]) -> bool:
        """
        Store document metadata with automatic TTL

        Args:
            document_id: Unique document identifier
            metadata: Document metadata dictionary

        Returns:
            True if stored successfully, False otherwise
        """
        if not self.is_available():
            return False

        try:
            key = f"doc:{document_id}:meta"
            value = json.dumps(metadata)
            self.redis.setex(key, settings.cache_ttl, value)
            logger.info(f"📦 Cached metadata for document {document_id} (TTL: {settings.cache_ttl}s)")
            return True
        except Exception as e:
            logger.error(f"❌ Failed to cache metadata for {document_id}: {e}")
            return False

    def get_document_metadata(self, document_id: str) -> Optional[Dict[str, Any]]:
        """
        Retrieve document metadata from cache

        Args:
            document_id: Unique document identifier

        Returns:
            Metadata dictionary or None if not found
        """
        if not self.is_available():
            return None

        try:
            key = f"doc:{document_id}:meta"
            value = self.redis.get(key)
            if value:
                return json.loads(value)
            return None
        except Exception as e:
            logger.error(f"❌ Failed to retrieve metadata for {document_id}: {e}")
            return None

    def set_document_text(self, document_id: str, text: str) -> bool:
        """
        Store extracted document text with automatic TTL

        Args:
            document_id: Unique document identifier
            text: Extracted text content

        Returns:
            True if stored successfully, False otherwise
        """
        if not self.is_available():
            return False

        try:
            key = f"doc:{document_id}:text"
            self.redis.setex(key, settings.cache_ttl, text)
            logger.info(f"📝 Cached text for document {document_id} ({len(text)} chars, TTL: {settings.cache_ttl}s)")
            return True
        except Exception as e:
            logger.error(f"❌ Failed to cache text for {document_id}: {e}")
            return False

    def get_document_text(self, document_id: str) -> Optional[str]:
        """
        Retrieve extracted document text from cache

        Args:
            document_id: Unique document identifier

        Returns:
            Extracted text or None if not found
        """
        if not self.is_available():
            return None

        try:
            key = f"doc:{document_id}:text"
            return self.redis.get(key)
        except Exception as e:
            logger.error(f"❌ Failed to retrieve text for {document_id}: {e}")
            return None

    def set_columns(self, document_id: str, columns: list) -> bool:
        """
        Store detected columns with automatic TTL

        Args:
            document_id: Unique document identifier
            columns: List of detected columns

        Returns:
            True if stored successfully, False otherwise
        """
        if not self.is_available():
            return False

        try:
            key = f"doc:{document_id}:columns"
            value = json.dumps(columns)
            self.redis.setex(key, settings.cache_ttl, value)
            logger.info(f"🔍 Cached {len(columns)} columns for document {document_id}")
            return True
        except Exception as e:
            logger.error(f"❌ Failed to cache columns for {document_id}: {e}")
            return False

    def get_columns(self, document_id: str) -> Optional[list]:
        """
        Retrieve detected columns from cache

        Args:
            document_id: Unique document identifier

        Returns:
            List of columns or None if not found
        """
        if not self.is_available():
            return None

        try:
            key = f"doc:{document_id}:columns"
            value = self.redis.get(key)
            if value:
                return json.loads(value)
            return None
        except Exception as e:
            logger.error(f"❌ Failed to retrieve columns for {document_id}: {e}")
            return None

    def delete_document_data(self, document_id: str) -> int:
        """
        Delete all cached data for a document

        Args:
            document_id: Unique document identifier

        Returns:
            Number of keys deleted
        """
        if not self.is_available():
            return 0

        try:
            keys = [
                f"doc:{document_id}:meta",
                f"doc:{document_id}:text",
                f"doc:{document_id}:columns",
            ]
            deleted = self.redis.delete(*keys)
            logger.info(f"🗑️  Deleted {deleted} cache entries for document {document_id}")
            return deleted
        except Exception as e:
            logger.error(f"❌ Failed to delete data for {document_id}: {e}")
            return 0

    def get_ttl(self, document_id: str) -> Optional[int]:
        """
        Get remaining TTL for document metadata

        Args:
            document_id: Unique document identifier

        Returns:
            Remaining seconds or None if key doesn't exist
        """
        if not self.is_available():
            return None

        try:
            key = f"doc:{document_id}:meta"
            ttl = self.redis.ttl(key)
            return ttl if ttl > 0 else None
        except Exception as e:
            logger.error(f"❌ Failed to get TTL for {document_id}: {e}")
            return None

    def extend_ttl(self, document_id: str, additional_seconds: int = None) -> bool:
        """
        Extend TTL for all document data

        Args:
            document_id: Unique document identifier
            additional_seconds: Seconds to add (default: reset to cache_ttl)

        Returns:
            True if extended successfully
        """
        if not self.is_available():
            return False

        try:
            ttl = additional_seconds or settings.cache_ttl
            keys = [
                f"doc:{document_id}:meta",
                f"doc:{document_id}:text",
                f"doc:{document_id}:columns",
            ]
            for key in keys:
                if self.redis.exists(key):
                    self.redis.expire(key, ttl)
            logger.info(f"⏱️  Extended TTL for document {document_id} to {ttl}s")
            return True
        except Exception as e:
            logger.error(f"❌ Failed to extend TTL for {document_id}: {e}")
            return False

    def clear_all(self) -> bool:
        """Clear all document cache (use with caution!)"""
        if not self.is_available():
            return False

        try:
            keys = self.redis.keys("doc:*")
            if keys:
                deleted = self.redis.delete(*keys)
                logger.warning(f"🗑️  Cleared {deleted} cache entries")
            return True
        except Exception as e:
            logger.error(f"❌ Failed to clear cache: {e}")
            return False

    # =========================================================================
    # FASE 4: Generic cache helpers for CacheManager
    # =========================================================================

    def set_with_ttl(self, key: str, value: str, ttl: int) -> bool:
        """
        Generic method to set a key with TTL (FASE 4)

        Args:
            key: Cache key
            value: Value to store
            ttl: Time to live in seconds

        Returns:
            True if successful
        """
        if not self.is_available():
            return False

        try:
            self.redis.setex(key, ttl, value)
            return True
        except Exception as e:
            logger.error(f"❌ Failed to set key {key}: {e}")
            return False

    def get(self, key: str) -> Optional[str]:
        """
        Generic method to get a value (FASE 4)

        Args:
            key: Cache key

        Returns:
            Value or None
        """
        if not self.is_available():
            return None

        try:
            return self.redis.get(key)
        except Exception as e:
            logger.error(f"❌ Failed to get key {key}: {e}")
            return None

    @property
    def redis_client(self):
        """Expose Redis client for advanced operations (FASE 4)"""
        return self.redis


# Global instance
_redis_service: Optional[RedisService] = None


def get_redis_service() -> RedisService:
    """Get or create Redis service singleton"""
    global _redis_service
    if _redis_service is None:
        _redis_service = RedisService()
    return _redis_service
