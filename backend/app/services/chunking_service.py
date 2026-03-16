"""
Chunking Service - Process large documents in manageable chunks
Enables parallel processing, progress tracking, and memory efficiency
"""
import logging
from typing import List, Tuple, Dict, Any, Callable
from pathlib import Path
from concurrent.futures import ThreadPoolExecutor, as_completed
import time

logger = logging.getLogger(__name__)


class ChunkingService:
    """Service for chunked document processing"""

    # Configuration
    DEFAULT_CHUNK_SIZE = 10  # Pages per chunk
    DEFAULT_OVERLAP = 1      # Pages overlap between chunks (for continuity)
    MAX_PARALLEL_CHUNKS = 4  # Max chunks processed in parallel

    def __init__(
        self,
        chunk_size: int = DEFAULT_CHUNK_SIZE,
        overlap: int = DEFAULT_OVERLAP,
        max_workers: int = MAX_PARALLEL_CHUNKS
    ):
        """
        Initialize chunking service

        Args:
            chunk_size: Number of pages per chunk
            overlap: Pages overlap between chunks
            max_workers: Max parallel chunk processors
        """
        self.chunk_size = chunk_size
        self.overlap = overlap
        self.max_workers = max_workers

    def create_chunks(
        self,
        total_pages: int,
        chunk_size: int = None,
        overlap: int = None
    ) -> List[Tuple[int, int]]:
        """
        Create page ranges for chunked processing

        Args:
            total_pages: Total number of pages
            chunk_size: Pages per chunk (default: self.chunk_size)
            overlap: Pages overlap (default: self.overlap)

        Returns:
            List of (start_page, end_page) tuples

        Example:
            total_pages=25, chunk_size=10, overlap=1
            → [(0, 10), (9, 19), (18, 25)]
        """
        chunk_size = chunk_size or self.chunk_size
        overlap = overlap or self.overlap

        if total_pages <= chunk_size:
            # Small document - no chunking needed
            return [(0, total_pages)]

        chunks = []
        current_start = 0

        while current_start < total_pages:
            current_end = min(current_start + chunk_size, total_pages)
            chunks.append((current_start, current_end))

            # Next chunk starts with overlap
            current_start = current_end - overlap

            # Avoid infinite loop if we're at the end
            if current_start >= total_pages - overlap:
                break

        logger.info(f"📦 Created {len(chunks)} chunks for {total_pages} pages")
        logger.info(f"   Chunk size: {chunk_size}, Overlap: {overlap}")

        return chunks

    def process_chunks_parallel(
        self,
        chunks: List[Tuple[int, int]],
        processor_func: Callable[[int, int, int], str],
        progress_callback: Callable[[int, int, str], None] = None
    ) -> List[str]:
        """
        Process chunks in parallel

        Args:
            chunks: List of (start, end) page ranges
            processor_func: Function to process each chunk
                            Signature: (chunk_idx, start_page, end_page) -> str
            progress_callback: Optional callback for progress updates
                               Signature: (completed_chunks, total_chunks, message) -> None

        Returns:
            List of results (one per chunk, in order)
        """
        total_chunks = len(chunks)
        results = [None] * total_chunks  # Pre-allocate results array
        completed = 0

        logger.info(f"🔄 Processing {total_chunks} chunks in parallel (max {self.max_workers} workers)")

        start_time = time.time()

        with ThreadPoolExecutor(max_workers=self.max_workers) as executor:
            # Submit all chunks
            future_to_chunk = {
                executor.submit(
                    processor_func,
                    idx,
                    start,
                    end
                ): idx
                for idx, (start, end) in enumerate(chunks)
            }

            # Collect results as they complete
            for future in as_completed(future_to_chunk):
                chunk_idx = future_to_chunk[future]
                start, end = chunks[chunk_idx]

                try:
                    result = future.result()
                    results[chunk_idx] = result
                    completed += 1

                    logger.info(
                        f"✅ Chunk {chunk_idx + 1}/{total_chunks} completed "
                        f"(pages {start}-{end})"
                    )

                    if progress_callback:
                        progress_callback(
                            completed,
                            total_chunks,
                            f"Processed pages {start}-{end}"
                        )

                except Exception as e:
                    logger.error(f"❌ Chunk {chunk_idx + 1} failed: {e}")
                    results[chunk_idx] = ""  # Empty result on failure

        elapsed = time.time() - start_time
        logger.info(f"⚡ All chunks processed in {elapsed:.2f}s")

        return results

    def merge_chunk_results(
        self,
        chunk_results: List[str],
        chunks: List[Tuple[int, int]]
    ) -> str:
        """
        Merge results from multiple chunks with overlap handling

        Args:
            chunk_results: List of text results from each chunk
            chunks: Original chunk ranges (for deduplication)

        Returns:
            Merged text
        """
        if len(chunk_results) == 1:
            return chunk_results[0]

        merged_text = ""
        overlap_size = self.overlap

        for idx, result in enumerate(chunk_results):
            if idx == 0:
                # First chunk - use everything
                merged_text += result
            else:
                # Subsequent chunks - skip overlap region
                # Simple heuristic: skip first ~overlap_size pages worth of lines
                lines = result.split('\n')

                # Estimate lines per page (rough: ~50 lines/page)
                lines_to_skip = overlap_size * 50

                # Take remaining lines
                remaining_lines = lines[min(lines_to_skip, len(lines) // 2):]
                merged_text += '\n'.join(remaining_lines)

        logger.info(f"🔗 Merged {len(chunk_results)} chunks into single text")
        return merged_text

    def should_use_chunking(
        self,
        total_pages: int,
        threshold: int = None
    ) -> bool:
        """
        Determine if chunking should be used

        Args:
            total_pages: Total number of pages
            threshold: Minimum pages for chunking (default: chunk_size)

        Returns:
            True if chunking recommended
        """
        threshold = threshold or self.chunk_size
        use_chunking = total_pages > threshold

        if use_chunking:
            logger.info(
                f"📦 Chunking enabled: {total_pages} pages > {threshold} threshold"
            )
        else:
            logger.info(
                f"📄 No chunking: {total_pages} pages ≤ {threshold} threshold"
            )

        return use_chunking

    def estimate_processing_time(
        self,
        total_pages: int,
        time_per_page: float = 3.0
    ) -> Dict[str, float]:
        """
        Estimate processing time with and without chunking

        Args:
            total_pages: Total number of pages
            time_per_page: Average seconds per page

        Returns:
            Dict with estimates
        """
        # Serial processing time
        serial_time = total_pages * time_per_page

        # Parallel processing time with chunking
        if total_pages <= self.chunk_size:
            parallel_time = serial_time
            num_chunks = 1
        else:
            chunks = self.create_chunks(total_pages)
            num_chunks = len(chunks)

            # Time = (total_pages / workers) * time_per_page
            # But accounting for overhead and chunk coordination
            parallel_time = (
                (total_pages / self.max_workers) * time_per_page * 1.2  # 20% overhead
            )

        speedup = serial_time / parallel_time if parallel_time > 0 else 1.0

        estimates = {
            "total_pages": total_pages,
            "num_chunks": num_chunks,
            "serial_time": round(serial_time, 1),
            "parallel_time": round(parallel_time, 1),
            "speedup": round(speedup, 2),
            "time_saved": round(serial_time - parallel_time, 1)
        }

        logger.info(f"⏱️  Processing estimates:")
        logger.info(f"   Serial: {estimates['serial_time']}s")
        logger.info(f"   Parallel: {estimates['parallel_time']}s ({num_chunks} chunks)")
        logger.info(f"   Speedup: {estimates['speedup']}x")

        return estimates


# Global instance
_chunking_service: ChunkingService = None


def get_chunking_service() -> ChunkingService:
    """Get or create ChunkingService singleton"""
    global _chunking_service
    if _chunking_service is None:
        _chunking_service = ChunkingService()
    return _chunking_service
