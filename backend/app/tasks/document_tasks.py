"""
Celery tasks for asynchronous document processing
"""
import logging
import time
from pathlib import Path
from typing import List, Dict, Any
from celery import Task
from celery_app import celery_app
from app.services.redis_service import get_redis_service
from app.services.file_manager import get_file_manager
from app.services.ocr_service import OCRService
from app.services.ai_service import AIService
from app.models.schemas import DetectedColumn, SelectedColumn, FormatConfig

logger = logging.getLogger(__name__)


class CallbackTask(Task):
    """Base task with callbacks for progress tracking"""

    def on_failure(self, exc, task_id, args, kwargs, einfo):
        """Log task failure"""
        logger.error(f"❌ Task {task_id} failed: {exc}")
        logger.error(f"   Args: {args}")
        logger.error(f"   Error info: {einfo}")

    def on_success(self, retval, task_id, args, kwargs):
        """Log task success"""
        logger.info(f"✅ Task {task_id} completed successfully")


@celery_app.task(
    bind=True,
    base=CallbackTask,
    autoretry_for=(Exception,),
    retry_backoff=True,
    retry_backoff_max=600,
    max_retries=3,
    name='tasks.detect_columns'
)
def detect_columns_task(self, document_id: str) -> Dict[str, Any]:
    """
    Async task: Detect columns in uploaded document using AI

    Args:
        document_id: Unique document identifier

    Returns:
        Dict with columns and processing info
    """
    try:
        # Initialize services
        redis_service = get_redis_service()
        file_manager = get_file_manager()
        ocr_service = OCRService()
        ai_service = AIService()

        # Update: Starting
        self.update_state(
            state='PROCESSING',
            meta={'progress': 0, 'step': 'Retrieving document...'}
        )

        # Get document metadata from Redis
        doc_meta = redis_service.get_document_metadata(document_id)
        if not doc_meta:
            raise ValueError(f"Document {document_id} not found in cache")

        file_path = Path(doc_meta["file_path"])
        file_type = doc_meta["file_type"]

        # Verify file exists
        if not file_path.exists():
            raise FileNotFoundError(f"Document file {file_path} not found or expired")

        # Update: OCR extraction
        self.update_state(
            state='PROCESSING',
            meta={'progress': 20, 'step': 'Extracting text from first 3 pages...'}
        )

        # Fast OCR: extract text from first 3 pages only (FASE 4: with caching)
        start_time = time.time()
        document_text_preview, num_pages = ocr_service.prepare_for_column_detection(
            file_path, file_type, document_id=document_id
        )

        # Update: AI analysis
        self.update_state(
            state='PROCESSING',
            meta={'progress': 60, 'step': 'Analyzing columns with AI...'}
        )

        # Use AI to detect columns (FASE 4: with caching)
        columns = ai_service.detect_columns(document_text_preview, document_id=document_id)

        # Update: Caching results
        self.update_state(
            state='PROCESSING',
            meta={'progress': 90, 'step': 'Caching results...'}
        )

        processing_time = time.time() - start_time

        # Store detected columns in Redis
        columns_data = [col.model_dump() for col in columns]
        redis_service.set_columns(document_id, columns_data)

        # Update metadata
        current_meta = redis_service.get_document_metadata(document_id)
        if current_meta:
            current_meta.update({
                "columns": columns_data,
                "num_pages": num_pages
            })
            redis_service.set_document_metadata(document_id, current_meta)

        logger.info(f"✅ Detected {len(columns)} columns for document {document_id}")

        return {
            'status': 'completed',
            'document_id': document_id,
            'columns': columns_data,
            'num_pages': num_pages,
            'processing_time': round(processing_time, 2)
        }

    except Exception as e:
        logger.error(f"❌ Column detection failed for {document_id}: {str(e)}")
        # Do not manually set FAILURE state, let raise handle it
        raise


@celery_app.task(
    bind=True,
    base=CallbackTask,
    autoretry_for=(Exception,),
    retry_backoff=True,
    retry_backoff_max=600,
    max_retries=3,
    name='tasks.extract_data'
)
def extract_data_task(
    self,
    document_id: str,
    selected_columns: List[Dict],
    format_config: Dict
) -> Dict[str, Any]:
    """
    Async task: Extract table data from document based on config

    Args:
        document_id: Unique document identifier
        selected_columns: Columns to extract
        format_config: Output format configuration

    Returns:
        Dict with extracted data and info
    """
    try:
        # Initialize services
        redis_service = get_redis_service()
        file_manager = get_file_manager()
        ocr_service = OCRService()
        ai_service = AIService()

        # Update: Starting
        self.update_state(
            state='PROCESSING',
            meta={'progress': 0, 'step': 'Retrieving document...'}
        )

        # Get document metadata from Redis
        doc_meta = redis_service.get_document_metadata(document_id)
        if not doc_meta:
            raise ValueError(f"Document {document_id} not found in cache")

        file_path = Path(doc_meta["file_path"])
        file_type = doc_meta["file_type"]

        # Verify file exists
        if not file_path.exists():
            raise FileNotFoundError(f"Document file {file_path} not found or expired")

        # Update: Checking cache
        self.update_state(
            state='PROCESSING',
            meta={'progress': 10, 'step': 'Checking cached OCR results...'}
        )

        # Try to get cached extracted text from Redis
        document_text = redis_service.get_document_text(document_id)

        if not document_text:
            # Update: OCR extraction
            self.update_state(
                state='PROCESSING',
                meta={'progress': 20, 'step': 'Extracting text from all pages (this may take a while)...'}
            )

            # Extract full document text (all pages in parallel) - FASE 4: with caching
            start_time = time.time()

            # Progress callback for chunked processing (FASE 3)
            def progress_update(completed: int, total: int, message: str):
                progress = 20 + int((completed / total) * 40)  # 20-60% range
                self.update_state(
                    state='PROCESSING',
                    meta={'progress': progress, 'step': message}
                )

            document_text, _ = ocr_service.prepare_for_data_extraction(
                file_path, file_type,
                document_id=document_id,  # FASE 4: Enable caching
                progress_callback=progress_update  # FASE 3: Progress updates
            )

            # Cache in Redis for potential reuse
            redis_service.set_document_text(document_id, document_text)

            logger.info(f"📝 OCR completed in {time.time() - start_time:.2f}s for document {document_id}")

        # Update: AI extraction
        self.update_state(
            state='PROCESSING',
            meta={'progress': 60, 'step': 'Extracting data with AI...'}
        )

        # Convert dicts back to Pydantic models
        columns_models = [SelectedColumn(**col) for col in selected_columns]
        format_model = FormatConfig(**format_config)

        # Extract data using AI - FAST mode (no validation) - FASE 4: with caching
        extraction_start = time.time()
        data, _ = ai_service.extract_table_data(
            document_text, columns_models, format_model,
            document_id=document_id,  # FASE 4: Enable caching
            enable_validation=False  # Skip validation for speed
        )

        logger.info(f"🤖 AI extraction completed in {time.time() - extraction_start:.2f}s")

        # Update: Cleanup
        self.update_state(
            state='PROCESSING',
            meta={'progress': 90, 'step': 'Cleaning up and finalizing...'}
        )

        # SUCCESS: Delete file after extraction (security)
        file_manager.delete_file_if_exists(file_path)
        logger.info(f"🗑️  Auto-deleted file for document {document_id}")

        total_time = time.time() - (extraction_start if 'start_time' not in locals() else start_time)

        # Launch async quality validation in background (non-blocking)
        quality_task_id = None
        try:
            quality_task = calculate_quality_task.delay(document_id, data, selected_columns)
            quality_task_id = quality_task.id
            logger.info(f"📊 Quality validation launched in background: {quality_task_id}")
        except Exception as e:
            logger.warning(f"⚠️  Could not launch background quality check: {e}")

        return {
            'status': 'completed',
            'document_id': document_id,
            'data': data,
            'rows_extracted': len(data),
            'processing_time': round(total_time, 2),
            'quality_task_id': quality_task_id  # ID for background quality check
        }

    except Exception as e:
        logger.error(f"❌ Data extraction failed for {document_id}: {str(e)}")
        # Do not manually set FAILURE state, let raise handle it
        raise


@celery_app.task(
    bind=True,
    base=CallbackTask,
    name='tasks.calculate_quality'
)
def calculate_quality_task(
    self,
    document_id: str,
    data: List[List[str]],
    selected_columns: List[Dict]
) -> Dict[str, Any]:
    """
    Async task: Calculate quality metrics and validation in background
    This runs after data extraction to not block the user

    Args:
        document_id: Unique document identifier
        data: Extracted data rows
        selected_columns: Column configuration

    Returns:
        Dict with quality report
    """
    try:
        logger.info(f"📊 Starting quality validation for document {document_id}")

        # Initialize services
        ai_service = AIService()

        # Prepare column data
        selected_columns_dict = [
            {
                'output_name': col.get('output_name'),
                'order': col.get('order'),
                'type': col.get('type')
            }
            for col in selected_columns
        ]

        # Run validation (Step 1: Validate data schemas)
        validated_data, validation_issues = ai_service.data_validator.validate_data(
            data,
            selected_columns_dict
        )

        # Run quality checks (Step 2: Quality checks and corrections)
        corrected_data, quality_metrics = ai_service.quality_checker.check_quality(
            validated_data,
            selected_columns_dict
        )

        # Calculate field confidence (Step 3: Field-level confidence)
        field_confidence = ai_service.quality_checker.analyze_field_confidence(
            corrected_data,
            selected_columns_dict
        )

        # Build quality report
        quality_report = {
            "validation": ai_service.data_validator.get_validation_summary(),
            "quality_metrics": quality_metrics.to_dict(),
            "field_confidence": field_confidence,
            "has_critical_errors": ai_service.data_validator.has_critical_errors()
        }

        logger.info(f"✅ Quality validation completed for {document_id}")
        logger.info(f"   Quality Score: {quality_metrics.quality_score:.1f}/100")
        logger.info(f"   Completeness: {quality_metrics.completeness_score:.1f}%")
        logger.info(f"   Confidence: {quality_metrics.confidence_score:.1f}%")

        return {
            'status': 'completed',
            'document_id': document_id,
            'quality_report': quality_report
        }

    except Exception as e:
        logger.error(f"❌ Quality validation failed for {document_id}: {str(e)}")
        raise
