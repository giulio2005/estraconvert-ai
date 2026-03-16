"""
Cache Manager - Multi-level intelligent caching system
Provides granular caching for OCR results, detections, and extractions
"""
import hashlib
import json
import logging
from typing import Optional, List, Dict, Any
from app.services.redis_service import get_redis_service

logger = logging.getLogger(__name__)


class CacheLevel:
    """Cache level identifiers"""
    PAGE_OCR = "page_ocr"           # OCR result per page
    COLUMNS = "columns"              # Detected columns
    FULL_EXTRACTION = "extraction"   # Full extraction result
    DOCUMENT_TEXT = "doc_text"       # Already exists in redis_service


class CacheManager:
    """
    Multi-level cache manager for optimized document processing

    Cache Hierarchy:
    L1: Page-level OCR (key: doc:{hash}:page:{N}:ocr)
    L2: Column detection (key: doc:{hash}:columns)
    L3: Full extraction (key: doc:{hash}:extraction)
    L4: Document text (existing in redis_service)
    """

    def __init__(self, ttl: int = 3600):
        """
        Initialize cache manager

        Args:
            ttl: Time-to-live in seconds (default: 1 hour)
        """
        self.redis = get_redis_service()
        self.ttl = ttl

    # ============================================================================
    # HELPER METHODS
    # ============================================================================

    def _compute_content_hash(self, content: str) -> str:
        """
        Compute SHA256 hash of content for cache keys

        Args:
            content: Content to hash

        Returns:
            Hex digest of hash
        """
        return hashlib.sha256(content.encode()).hexdigest()[:16]

    def _build_key(self, doc_id: str, cache_type: str, *parts) -> str:
        """
        Build standardized cache key

        Args:
            doc_id: Document identifier
            cache_type: Type of cache (from CacheLevel)
            *parts: Additional key parts

        Returns:
            Cache key string
        """
        key_parts = [f"cache:{cache_type}:{doc_id}"]
        key_parts.extend(str(p) for p in parts)
        return ":".join(key_parts)

    # ============================================================================
    # L1: PAGE-LEVEL OCR CACHE
    # ============================================================================

    def cache_page_ocr(
        self,
        doc_id: str,
        page_number: int,
        page_hash: str,
        ocr_text: str
    ) -> bool:
        """
        Cache OCR result for a specific page

        Args:
            doc_id: Document identifier
            page_number: Page number (0-indexed)
            page_hash: Hash of page content (for invalidation)
            ocr_text: OCR extracted text

        Returns:
            True if cached successfully
        """
        key = self._build_key(doc_id, CacheLevel.PAGE_OCR, page_number, page_hash)

        try:
            success = self.redis.set_with_ttl(key, ocr_text, self.ttl)
            if success:
                logger.info(f"📄 Cached OCR for page {page_number} (doc: {doc_id[:8]}...)")
            return success
        except Exception as e:
            logger.error(f"❌ Failed to cache page OCR: {e}")
            return False

    def get_page_ocr(
        self,
        doc_id: str,
        page_number: int,
        page_hash: str
    ) -> Optional[str]:
        """
        Retrieve cached OCR result for a page

        Args:
            doc_id: Document identifier
            page_number: Page number (0-indexed)
            page_hash: Hash of page content

        Returns:
            Cached OCR text or None
        """
        key = self._build_key(doc_id, CacheLevel.PAGE_OCR, page_number, page_hash)

        try:
            result = self.redis.get(key)
            if result:
                logger.info(f"✅ Cache hit: Page {page_number} OCR (doc: {doc_id[:8]}...)")
            return result
        except Exception as e:
            logger.error(f"❌ Failed to get page OCR: {e}")
            return None

    def cache_multiple_pages(
        self,
        doc_id: str,
        page_results: List[tuple]
    ) -> int:
        """
        Cache OCR results for multiple pages at once

        Args:
            doc_id: Document identifier
            page_results: List of (page_number, page_hash, ocr_text) tuples

        Returns:
            Number of pages successfully cached
        """
        cached_count = 0

        for page_number, page_hash, ocr_text in page_results:
            if self.cache_page_ocr(doc_id, page_number, page_hash, ocr_text):
                cached_count += 1

        logger.info(f"📦 Cached {cached_count}/{len(page_results)} pages for doc {doc_id[:8]}...")
        return cached_count

    def get_cached_pages(
        self,
        doc_id: str,
        pages_info: List[tuple]
    ) -> tuple:
        """
        Get cached OCR for multiple pages

        Args:
            doc_id: Document identifier
            pages_info: List of (page_number, page_hash) tuples

        Returns:
            Tuple of (cached_results, missing_pages)
            - cached_results: Dict {page_number: ocr_text}
            - missing_pages: List of page_numbers not in cache
        """
        cached_results = {}
        missing_pages = []

        for page_number, page_hash in pages_info:
            ocr_text = self.get_page_ocr(doc_id, page_number, page_hash)

            if ocr_text:
                cached_results[page_number] = ocr_text
            else:
                missing_pages.append(page_number)

        hit_rate = len(cached_results) / len(pages_info) * 100 if pages_info else 0
        logger.info(
            f"📊 Page cache hit rate: {hit_rate:.1f}% "
            f"({len(cached_results)}/{len(pages_info)} pages)"
        )

        return cached_results, missing_pages

    # ============================================================================
    # L2: COLUMN DETECTION CACHE
    # ============================================================================

    def cache_columns(
        self,
        doc_id: str,
        doc_hash: str,
        columns: List[Dict[str, Any]]
    ) -> bool:
        """
        Cache detected columns

        Args:
            doc_id: Document identifier
            doc_hash: Hash of document content
            columns: List of detected column dicts

        Returns:
            True if cached successfully
        """
        key = self._build_key(doc_id, CacheLevel.COLUMNS, doc_hash)

        try:
            columns_json = json.dumps(columns)
            success = self.redis.set_with_ttl(key, columns_json, self.ttl)

            if success:
                logger.info(
                    f"🔍 Cached {len(columns)} columns for doc {doc_id[:8]}..."
                )
            return success
        except Exception as e:
            logger.error(f"❌ Failed to cache columns: {e}")
            return False

    def get_cached_columns(
        self,
        doc_id: str,
        doc_hash: str
    ) -> Optional[List[Dict[str, Any]]]:
        """
        Retrieve cached column detection

        Args:
            doc_id: Document identifier
            doc_hash: Hash of document content

        Returns:
            List of column dicts or None
        """
        key = self._build_key(doc_id, CacheLevel.COLUMNS, doc_hash)

        try:
            result = self.redis.get(key)
            if result:
                columns = json.loads(result)
                logger.info(
                    f"✅ Cache hit: {len(columns)} columns (doc: {doc_id[:8]}...)"
                )
                return columns
            return None
        except Exception as e:
            logger.error(f"❌ Failed to get cached columns: {e}")
            return None

    # ============================================================================
    # L3: FULL EXTRACTION CACHE
    # ============================================================================

    def cache_extraction(
        self,
        doc_id: str,
        doc_hash: str,
        extraction_data: List[List[str]],
        column_names: List[str]
    ) -> bool:
        """
        Cache full extraction result (all columns)

        Args:
            doc_id: Document identifier
            doc_hash: Hash of document content
            extraction_data: Full extracted data (all rows, all columns)
            column_names: Names of columns in order

        Returns:
            True if cached successfully
        """
        key = self._build_key(doc_id, CacheLevel.FULL_EXTRACTION, doc_hash)

        try:
            cache_data = {
                "columns": column_names,
                "data": extraction_data,
                "row_count": len(extraction_data)
            }
            cache_json = json.dumps(cache_data)
            success = self.redis.set_with_ttl(key, cache_json, self.ttl)

            if success:
                logger.info(
                    f"💾 Cached extraction: {len(extraction_data)} rows, "
                    f"{len(column_names)} columns (doc: {doc_id[:8]}...)"
                )
            return success
        except Exception as e:
            logger.error(f"❌ Failed to cache extraction: {e}")
            return False

    def get_cached_extraction(
        self,
        doc_id: str,
        doc_hash: str,
        requested_columns: Optional[List[str]] = None
    ) -> Optional[Dict[str, Any]]:
        """
        Retrieve cached extraction result

        Args:
            doc_id: Document identifier
            doc_hash: Hash of document content
            requested_columns: Optional list of column names to filter
                              (returns all if None)

        Returns:
            Dict with 'columns', 'data', 'row_count' or None
        """
        key = self._build_key(doc_id, CacheLevel.FULL_EXTRACTION, doc_hash)

        try:
            result = self.redis.get(key)
            if not result:
                return None

            cache_data = json.loads(result)

            # If specific columns requested, filter the data
            if requested_columns:
                filtered_data = self._filter_extraction_columns(
                    cache_data,
                    requested_columns
                )
                if filtered_data:
                    logger.info(
                        f"✅ Cache hit: Extraction filtered to "
                        f"{len(requested_columns)} columns (doc: {doc_id[:8]}...)"
                    )
                    return filtered_data
                else:
                    logger.warning(
                        f"⚠️  Cache hit but columns don't match "
                        f"(doc: {doc_id[:8]}...)"
                    )
                    return None

            logger.info(
                f"✅ Cache hit: Full extraction "
                f"({cache_data['row_count']} rows, doc: {doc_id[:8]}...)"
            )
            return cache_data

        except Exception as e:
            logger.error(f"❌ Failed to get cached extraction: {e}")
            return None

    def _filter_extraction_columns(
        self,
        cache_data: Dict[str, Any],
        requested_columns: List[str]
    ) -> Optional[Dict[str, Any]]:
        """
        Filter cached extraction to specific columns

        Args:
            cache_data: Full cached extraction data
            requested_columns: Columns to extract

        Returns:
            Filtered data or None if columns don't match
        """
        cached_columns = cache_data['columns']
        cached_rows = cache_data['data']

        # Check if all requested columns exist in cache
        if not all(col in cached_columns for col in requested_columns):
            return None

        # Find indices of requested columns
        column_indices = [
            cached_columns.index(col) for col in requested_columns
        ]

        # Filter each row to only requested columns
        filtered_rows = [
            [row[idx] for idx in column_indices]
            for row in cached_rows
        ]

        return {
            'columns': requested_columns,
            'data': filtered_rows,
            'row_count': len(filtered_rows)
        }

    # ============================================================================
    # CACHE STATISTICS & MANAGEMENT
    # ============================================================================

    def get_cache_stats(self, doc_id: str) -> Dict[str, Any]:
        """
        Get cache statistics for a document

        Args:
            doc_id: Document identifier

        Returns:
            Dict with cache stats
        """
        # Count keys for this document
        pattern = f"cache:*:{doc_id}:*"
        keys = self.redis.redis_client.keys(pattern) if hasattr(self.redis, 'redis_client') else []

        # Keys are strings (decode_responses=True in Redis), not bytes
        page_ocr_keys = [k for k in keys if ':page_ocr:' in k]
        column_keys = [k for k in keys if ':columns:' in k]
        extraction_keys = [k for k in keys if ':extraction:' in k]

        stats = {
            'total_cached_items': len(keys),
            'page_ocr_cached': len(page_ocr_keys),
            'columns_cached': len(column_keys),
            'extractions_cached': len(extraction_keys),
            'document_id': doc_id
        }

        logger.info(f"📊 Cache stats for {doc_id[:8]}...: {stats}")
        return stats

    def invalidate_document_cache(self, doc_id: str) -> int:
        """
        Invalidate all cache entries for a document

        Args:
            doc_id: Document identifier

        Returns:
            Number of keys deleted
        """
        pattern = f"cache:*:{doc_id}:*"

        try:
            if hasattr(self.redis, 'redis_client'):
                keys = self.redis.redis_client.keys(pattern)
                if keys:
                    deleted = self.redis.redis_client.delete(*keys)
                    logger.info(f"🗑️  Invalidated {deleted} cache entries for doc {doc_id[:8]}...")
                    return deleted
            return 0
        except Exception as e:
            logger.error(f"❌ Failed to invalidate cache: {e}")
            return 0


# Global instance
_cache_manager: CacheManager = None


def get_cache_manager() -> CacheManager:
    """Get or create CacheManager singleton"""
    global _cache_manager
    if _cache_manager is None:
        _cache_manager = CacheManager()
    return _cache_manager
