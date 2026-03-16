import io
import base64
import hashlib
from pathlib import Path
from PIL import Image
from pdf2image import convert_from_path, convert_from_bytes
from typing import List, Union, Tuple, Callable, Optional
from app.config import settings
from pypdf import PdfReader
from app.services.ai_provider import get_ai_provider
from app.services.chunking_service import get_chunking_service
from app.services.cache_manager import get_cache_manager


class OCRService:
    """Service for OCR and document image processing with chunked support"""

    def __init__(self):
        self.ai_provider = get_ai_provider()
        self.chunking_service = get_chunking_service()
        self.cache_manager = get_cache_manager()

    def _compute_page_hash(self, image: Image.Image) -> str:
        """Compute hash of page image for cache key"""
        buffered = io.BytesIO()
        image.save(buffered, format="PNG")
        return hashlib.md5(buffered.getvalue()).hexdigest()[:16]

    def extract_text_from_pdf(self, pdf_path: Union[str, Path], max_pages: int = None) -> Tuple[str, bool]:
        """
        Try to extract text directly from PDF.
        Returns: (extracted_text, is_text_based)
        """
        try:
            reader = PdfReader(pdf_path)
            total_pages = len(reader.pages)
            pages_to_process = min(max_pages, total_pages) if max_pages else total_pages

            extracted_text = []
            total_chars = 0

            for i in range(pages_to_process):
                try:
                    page = reader.pages[i]
                    page_text = page.extract_text()
                    total_chars += len(page_text.strip())
                    extracted_text.append(f"--- PAGE {i + 1} ---\n{page_text}")
                except Exception as page_error:
                    # Skip pages that fail extraction (encrypted, corrupted, etc.)
                    print(f"⚠️  Warning: Failed to extract page {i+1}: {str(page_error)[:100]}")
                    extracted_text.append(f"--- PAGE {i + 1} ---\n[Extraction failed]")

            # INCREASED THRESHOLD: Consider text-based if we got significant text
            # Strategy: Only use OCR if extraction completely fails or gets minimal text
            # Typical bank statement has 500-2000 chars per page
            # Use 50 chars/page as minimum threshold (very conservative)
            is_text_based = total_chars > (pages_to_process * 50)

            # If we got some text, log it for debugging
            if total_chars > 0:
                print(f"📄 PyPDF2 extracted {total_chars} chars from {pages_to_process} pages (avg {total_chars/pages_to_process:.0f} chars/page)")
                print(f"✅ Decision: {'TEXT-BASED (direct extraction)' if is_text_based else 'IMAGE-BASED (will use OCR)'}")

            return "\n\n".join(extracted_text), is_text_based

        except Exception as e:
            # If extraction completely fails (file corrupted, unsupported format, etc.)
            print(f"❌ PyPDF2 extraction failed completely: {str(e)[:100]}")
            print(f"→ Will use OCR Vision instead")
            return "", False

    def pdf_to_images(self, pdf_path: Union[str, Path]) -> List[Image.Image]:
        """Convert PDF to list of PIL Images"""
        try:
            images = convert_from_path(pdf_path, dpi=300)
            return images
        except Exception as e:
            raise Exception(f"Error converting PDF to images: {str(e)}")

    def pdf_bytes_to_images(self, pdf_bytes: bytes) -> List[Image.Image]:
        """Convert PDF bytes to list of PIL Images"""
        try:
            images = convert_from_bytes(pdf_bytes, dpi=300)
            return images
        except Exception as e:
            raise Exception(f"Error converting PDF bytes to images: {str(e)}")

    def image_to_base64(self, image: Image.Image) -> str:
        """Convert PIL Image to base64 string"""
        buffered = io.BytesIO()
        image.save(buffered, format="PNG")
        img_str = base64.b64encode(buffered.getvalue()).decode()
        return img_str

    def extract_text_from_images(
        self,
        pil_images: List[Image.Image],
        max_pages: int = None,
        document_id: Optional[str] = None
    ) -> str:
        """
        Extract text from images using Gemini Vision OCR
        Fast and accurate text extraction with parallel processing
        FASE 4: Now with page-level caching

        Args:
            pil_images: List of PIL images to process
            max_pages: Maximum number of pages to process (None = all pages)
            document_id: Document ID for caching (optional)
        """
        try:
            import concurrent.futures

            # Limit pages if specified
            images_to_process = pil_images[:max_pages] if max_pages else pil_images

            # FASE 4: Check cache if document_id provided
            if document_id:
                # Build pages_info for cache lookup
                pages_info = [
                    (idx, self._compute_page_hash(img))
                    for idx, img in enumerate(images_to_process)
                ]

                # Check cache
                cached_results, missing_pages = self.cache_manager.get_cached_pages(
                    document_id,
                    pages_info
                )

                if cached_results:
                    print(f"✅ Cache hit: {len(cached_results)}/{len(images_to_process)} pages cached")
            else:
                cached_results = {}
                missing_pages = list(range(len(images_to_process)))

            # Process only missing pages
            prompt = """Extract ALL text from this document page exactly as it appears.
Preserve layout and table structure. Return raw text only."""

            def process_page(idx_img_tuple):
                idx, img = idx_img_tuple
                text = self.ai_provider.generate_with_image(prompt, img, temperature=0, max_tokens=4000)

                # Cache result if document_id provided
                if document_id:
                    page_hash = self._compute_page_hash(img)
                    self.cache_manager.cache_page_ocr(document_id, idx, page_hash, text)

                return idx, text

            # Only process pages not in cache
            pages_to_process = [
                (idx, images_to_process[idx])
                for idx in missing_pages
            ]

            if pages_to_process:
                print(f"🔄 Processing {len(pages_to_process)} uncached pages with OCR...")
                # Process pages in parallel using ThreadPoolExecutor
                with concurrent.futures.ThreadPoolExecutor(max_workers=4) as executor:
                    new_results = list(executor.map(process_page, pages_to_process))

                # Merge new results with cached results
                all_results = {idx: text for idx, text in new_results}
                all_results.update(cached_results)
            else:
                all_results = cached_results

            # Sort by page number and combine
            sorted_results = sorted(all_results.items(), key=lambda x: x[0])
            full_text = [f"--- PAGE {idx + 1} ---\n{text}" for idx, text in sorted_results]

            return "\n\n".join(full_text)

        except Exception as e:
            raise Exception(f"Error extracting text: {str(e)}")

    def prepare_for_column_detection(
        self,
        file_path: Path,
        file_type: str,
        document_id: Optional[str] = None
    ) -> Tuple[str, int]:
        """
        Fast preparation for column detection - only processes first 3 pages.
        Smart strategy: tries direct text extraction first, falls back to OCR if needed.
        FASE 4: Now with page-level caching support.

        Args:
            file_path: Path to document
            file_type: Type of file (pdf, image)
            document_id: Document ID for caching (optional)

        Returns:
            (extracted_text, total_pages)
        """
        if file_type == "pdf":
            # Try direct text extraction first (FAST)
            text, is_text_based = self.extract_text_from_pdf(file_path, max_pages=3)

            if is_text_based:
                # PDF has selectable text - use it directly!
                print(f"✓ PDF is text-based, direct extraction used (fast)")
                reader = PdfReader(file_path)
                return text, len(reader.pages)
            else:
                # PDF is scanned/image-based - use OCR (SLOW)
                print(f"✗ PDF is image-based, using OCR fallback (slow)")
                pil_images = self.pdf_to_images(file_path)
                total_pages = len(pil_images)
                text = self.extract_text_from_images(pil_images, max_pages=3, document_id=document_id)
                return text, total_pages
        else:
            # Image file - always use OCR
            pil_images = [Image.open(file_path)]
            text = self.extract_text_from_images(pil_images, document_id=document_id)
            return text, 1

    def prepare_for_data_extraction(
        self,
        file_path: Path,
        file_type: str,
        document_id: Optional[str] = None,
        progress_callback: Optional[Callable[[int, int, str], None]] = None
    ) -> Tuple[str, int]:
        """
        Full document preparation for data extraction - processes all pages.
        Smart strategy: tries direct text extraction first, falls back to OCR if needed.
        FASE 3: Now supports chunked processing for large documents.
        FASE 4: Now with page-level caching support.

        Args:
            file_path: Path to document
            file_type: Type of file (pdf, image, excel)
            document_id: Document ID for caching (optional)
            progress_callback: Optional callback (completed, total, message)

        Returns:
            (extracted_text, number of pages)
        """
        if file_type == "pdf":
            # Try direct text extraction first (FAST)
            text, is_text_based = self.extract_text_from_pdf(file_path)

            if is_text_based:
                # PDF has selectable text - use it directly!
                print(f"✓ Full PDF is text-based, direct extraction used (instant)")
                reader = PdfReader(file_path)
                return text, len(reader.pages)
            else:
                # PDF is scanned/image-based - use chunked OCR for efficiency
                reader = PdfReader(file_path)
                total_pages = len(reader.pages)

                # FASE 3: Use chunking for large documents
                if self.chunking_service.should_use_chunking(total_pages):
                    print(f"✓ Using chunked OCR for {total_pages} pages (faster!)")
                    text = self._extract_text_chunked(
                        file_path,
                        total_pages,
                        document_id,
                        progress_callback
                    )
                    return text, total_pages
                else:
                    # Small document - process normally
                    print(f"✗ Full PDF is image-based, using parallel OCR (slower)")
                    pil_images = self.pdf_to_images(file_path)
                    text = self.extract_text_from_images(pil_images, document_id=document_id)
                    return text, len(pil_images)
        else:
            # Image file - always use OCR
            pil_images = [Image.open(file_path)]
            text = self.extract_text_from_images(pil_images, document_id=document_id)
            return text, 1

    def _extract_text_chunked(
        self,
        pdf_path: Path,
        total_pages: int,
        document_id: Optional[str] = None,
        progress_callback: Optional[Callable[[int, int, str], None]] = None
    ) -> str:
        """
        Extract text from PDF using chunked processing (FASE 3)
        FASE 4: Now with page-level caching support

        Args:
            pdf_path: Path to PDF
            total_pages: Total number of pages
            document_id: Document ID for caching (optional)
            progress_callback: Progress updates

        Returns:
            Extracted text from all pages
        """
        # Create chunks
        chunks = self.chunking_service.create_chunks(total_pages)

        # Define processor function for each chunk
        def process_chunk(chunk_idx: int, start_page: int, end_page: int) -> str:
            """Process single chunk of pages"""
            try:
                print(f"🔄 Processing chunk {chunk_idx + 1}: pages {start_page + 1}-{end_page}")

                # Convert only this chunk's pages to images
                images = convert_from_path(
                    pdf_path,
                    dpi=300,
                    first_page=start_page + 1,  # pdf2image is 1-indexed
                    last_page=end_page
                )

                # OCR this chunk's images with caching
                chunk_text = self.extract_text_from_images(images, document_id=document_id)

                return chunk_text

            except Exception as e:
                print(f"❌ Chunk {chunk_idx + 1} failed: {e}")
                return ""

        # Process chunks in parallel
        chunk_results = self.chunking_service.process_chunks_parallel(
            chunks,
            process_chunk,
            progress_callback
        )

        # Merge results
        merged_text = self.chunking_service.merge_chunk_results(
            chunk_results,
            chunks
        )

        return merged_text
