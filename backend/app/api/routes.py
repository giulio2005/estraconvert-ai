import time
import uuid
from pathlib import Path
from fastapi import APIRouter, UploadFile, File, HTTPException, Form
from fastapi.responses import JSONResponse
from app.models.schemas import (
    DetectColumnsResponse,
    ExtractDataRequest,
    ExtractDataResponse,
    JobResponse,
    JobStatusResponse,
    JobStatus,
)
from app.services.ocr_service import OCRService
from app.services.ai_service import AIService
from app.services.redis_service import get_redis_service
from app.services.file_manager import get_file_manager
from app.services.excel_service import excel_service
from app.config import settings
from app.tasks.document_tasks import detect_columns_task, extract_data_task
from celery_app import celery_app
from celery.result import AsyncResult

router = APIRouter()

# Initialize services
ocr_service = OCRService()
ai_service = AIService()
redis_service = get_redis_service()
file_manager = get_file_manager()

# Fallback in-memory cache (used only if Redis unavailable)
_fallback_cache = {}


def _get_document_metadata(document_id: str) -> dict:
    """Get document metadata from Redis or fallback cache"""
    # Try Redis first
    metadata = redis_service.get_document_metadata(document_id)
    if metadata:
        return metadata

    # Fallback to memory
    if document_id in _fallback_cache:
        return _fallback_cache[document_id]

    raise HTTPException(status_code=404, detail="Document not found or expired")


def _update_document_metadata(document_id: str, updates: dict):
    """Update document metadata in Redis or fallback cache"""
    # Get current metadata
    metadata = _get_document_metadata(document_id)

    # Merge updates
    metadata.update(updates)

    # Save back
    if not redis_service.set_document_metadata(document_id, metadata):
        _fallback_cache[document_id] = metadata


@router.post("/upload")
async def upload_document(file: UploadFile = File(...)):
    """
    Upload a document (PDF or image) for processing.
    Files are stored temporarily and auto-deleted after TTL expires.
    """
    try:
        # Validate file type
        allowed_types = [
            "application/pdf",
            "image/jpeg",
            "image/jpg",
            "image/png",
            "image/tiff",
            "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",  # .xlsx
            "application/vnd.ms-excel",  # .xls
        ]

        if file.content_type not in allowed_types:
            raise HTTPException(
                status_code=400,
                detail=f"Invalid file type. Allowed: PDF, Excel, JPG, PNG, TIFF",
            )

        # Check file size
        content = await file.read()
        size_mb = len(content) / (1024 * 1024)

        if size_mb > settings.max_file_size_mb:
            raise HTTPException(
                status_code=400,
                detail=f"File too large. Max size: {settings.max_file_size_mb}MB",
            )

        # Generate document ID
        document_id = str(uuid.uuid4())

        # Save file with FileManager (includes TTL tracking)
        file_extension = Path(file.filename).suffix
        file_path, _ = file_manager.save_upload(document_id, content, file_extension)

        # Determine file type
        if file.content_type == "application/pdf":
            file_type = "pdf"
        elif file.content_type in ["application/vnd.openxmlformats-officedocument.spreadsheetml.sheet", "application/vnd.ms-excel"]:
            file_type = "excel"
        else:
            file_type = "image"

        # Store metadata in Redis (with TTL) or fallback
        metadata = {
            "file_path": str(file_path),
            "file_type": file_type,
            "file_name": file.filename,
            "size_mb": size_mb,
        }

        # Try Redis first, fallback to memory
        if not redis_service.set_document_metadata(document_id, metadata):
            _fallback_cache[document_id] = metadata

        return {
            "document_id": document_id,
            "file_name": file.filename,
            "file_type": file_type,
            "size_mb": round(size_mb, 2),
        }

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Upload failed: {str(e)}")


@router.post("/detect-columns", response_model=DetectColumnsResponse)
async def detect_columns(document_id: str = Form(...)):
    """
    Detect columns in the uploaded document using AI.
    Results are cached in Redis with TTL.
    """
    try:
        start_time = time.time()

        # Get document metadata from Redis/fallback
        doc_meta = _get_document_metadata(document_id)
        file_path = Path(doc_meta["file_path"])
        file_type = doc_meta["file_type"]

        # Check if file still exists (not expired)
        if not file_path.exists():
            raise HTTPException(status_code=404, detail="Document file expired or deleted")

        # Fast OCR: extract text from first 3 pages only for column detection
        document_text_preview, num_pages = ocr_service.prepare_for_column_detection(
            file_path, file_type
        )

        # Use AI to detect columns from preview text
        columns = ai_service.detect_columns(document_text_preview)

        processing_time = time.time() - start_time

        # Store detected columns in Redis/fallback
        columns_data = [col.model_dump() for col in columns]
        redis_service.set_columns(document_id, columns_data)

        # Update metadata
        _update_document_metadata(document_id, {
            "columns": columns_data,
            "num_pages": num_pages
        })

        return DetectColumnsResponse(
            document_id=document_id,
            columns=columns,
            processing_time=round(processing_time, 2),
        )

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Column detection failed: {str(e)}"
        )


@router.post("/detect-columns-async", response_model=JobResponse)
async def detect_columns_async(document_id: str = Form(...)):
    """
    Asynchronously detect columns in the uploaded document using AI.
    Returns immediately with a job_id for polling status.
    """
    try:
        # Verify document exists
        doc_meta = _get_document_metadata(document_id)
        file_path = Path(doc_meta["file_path"])

        if not file_path.exists():
            raise HTTPException(status_code=404, detail="Document file expired or deleted")

        # Launch async Celery task
        task = detect_columns_task.delay(document_id)

        return JobResponse(
            job_id=task.id,
            status=JobStatus.PENDING,
            message="Column detection started. Use job_id to check status."
        )

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Failed to start column detection: {str(e)}"
        )


@router.post("/extract-data-async", response_model=JobResponse)
async def extract_data_async(request: ExtractDataRequest):
    """
    Asynchronously extract table data from document.
    Returns immediately with a job_id for polling status.
    """
    try:
        # Verify document exists
        doc_meta = _get_document_metadata(request.document_id)
        file_path = Path(doc_meta["file_path"])

        if not file_path.exists():
            raise HTTPException(status_code=404, detail="Document file expired or deleted")

        # Convert Pydantic models to dicts for Celery serialization
        selected_columns_dict = [col.model_dump() for col in request.selected_columns]
        format_config_dict = request.format_config.model_dump()

        # Launch async Celery task
        task = extract_data_task.delay(
            request.document_id,
            selected_columns_dict,
            format_config_dict
        )

        return JobResponse(
            job_id=task.id,
            status=JobStatus.PENDING,
            message="Data extraction started. Use job_id to check status."
        )

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Failed to start data extraction: {str(e)}"
        )


@router.get("/jobs/{job_id}", response_model=JobStatusResponse)
async def get_job_status(job_id: str):
    """
    Get the status and result of an async job.
    Poll this endpoint to check task progress and retrieve results.
    """
    try:
        task_result = celery_app.AsyncResult(job_id)

        # Map Celery states to our JobStatus enum
        if task_result.state == 'PENDING':
            return JobStatusResponse(
                job_id=job_id,
                status=JobStatus.PENDING,
                progress=0,
                step="Waiting to start..."
            )

        elif task_result.state == 'PROCESSING':
            # Get progress info from task metadata
            info = task_result.info or {}
            return JobStatusResponse(
                job_id=job_id,
                status=JobStatus.PROCESSING,
                progress=info.get('progress', 0),
                step=info.get('step', 'Processing...')
            )

        elif task_result.state == 'SUCCESS':
            # Task completed successfully
            result = task_result.result

            # DEBUG: Log result data size
            if isinstance(result, dict) and 'data' in result:
                print(f"🔍 DEBUG: Returning result with {len(result.get('data', []))} rows")
                if result.get('data'):
                    print(f"   First row: {result['data'][0]}")

            return JobStatusResponse(
                job_id=job_id,
                status=JobStatus.SUCCESS,
                progress=100,
                step="Completed",
                result=result
            )

        elif task_result.state == 'FAILURE':
            # Task failed
            error_info = str(task_result.info) if task_result.info else "Unknown error"
            return JobStatusResponse(
                job_id=job_id,
                status=JobStatus.FAILURE,
                step="Failed",
                error=error_info
            )

        else:
            # Unknown state
            return JobStatusResponse(
                job_id=job_id,
                status=JobStatus.PENDING,
                step=f"Unknown state: {task_result.state}"
            )

    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Failed to get job status: {str(e)}"
        )


@router.post("/extract-data", response_model=ExtractDataResponse)
async def extract_data(request: ExtractDataRequest):
    """
    Extract table data from document based on selected columns and format config.
    Extracted text is cached in Redis. File is auto-deleted after successful extraction.
    """
    try:
        start_time = time.time()

        # Get document metadata from Redis/fallback
        doc_meta = _get_document_metadata(request.document_id)
        file_path = Path(doc_meta["file_path"])
        file_type = doc_meta["file_type"]

        # Check if file still exists
        if not file_path.exists():
            raise HTTPException(status_code=404, detail="Document file expired or deleted")

        # Try to get cached extracted text from Redis
        document_text = redis_service.get_document_text(request.document_id)

        if not document_text:
            # Extract full document text (all pages in parallel)
            document_text, _ = ocr_service.prepare_for_data_extraction(file_path, file_type)
            # Cache in Redis for potential reuse
            redis_service.set_document_text(request.document_id, document_text)

        # Extract data using AI
        data = ai_service.extract_table_data(
            document_text, request.selected_columns, request.format_config
        )

        processing_time = time.time() - start_time

        # SUCCESS: Data extracted! Now we can safely delete the file
        # The extracted data is being returned to user, no need to keep original file
        file_manager.delete_file_if_exists(file_path)

        return ExtractDataResponse(
            document_id=request.document_id,
            data=data,
            rows_extracted=len(data),
            processing_time=round(processing_time, 2),
        )

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Data extraction failed: {str(e)}")


@router.get("/health")
async def health_check():
    """Health check endpoint with Redis and storage status"""
    redis_status = "connected" if redis_service.is_available() else "unavailable (using fallback)"
    file_stats = file_manager.get_file_stats()

    return {
        "status": "healthy",
        "service": "EstraConvert API",
        "redis": redis_status,
        "storage": file_stats,
    }


@router.post("/cleanup")
async def manual_cleanup():
    """Manually trigger file cleanup (admin endpoint)"""
    try:
        deleted = file_manager.cleanup_expired_files()
        file_stats = file_manager.get_file_stats()

        return {
            "message": "Cleanup completed",
            "files_deleted": deleted,
            "remaining_files": file_stats.get("total_files", 0),
            "storage_mb": file_stats.get("total_size_mb", 0),
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Cleanup failed: {str(e)}")


@router.delete("/document/{document_id}")
async def delete_document(document_id: str):
    """
    Manually delete a document and all its cached data.
    Useful if user wants to immediately remove their data.
    """
    try:
        # Delete file
        file_deleted = file_manager.delete_file(document_id)

        # Delete Redis cache
        cache_deleted = redis_service.delete_document_data(document_id)

        # Delete from fallback cache
        if document_id in _fallback_cache:
            del _fallback_cache[document_id]

        return {
            "message": "Document deleted",
            "document_id": document_id,
            "file_deleted": file_deleted,
            "cache_entries_deleted": cache_deleted,
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Deletion failed: {str(e)}")


@router.get("/ai-provider")
async def get_ai_provider():
    """Get current AI provider configuration"""
    return {
        "provider": settings.ai_provider,
        "available_providers": ["gemini", "openrouter"]
    }


@router.post("/ai-provider")
async def set_ai_provider(provider: str = Form(...)):
    """Set AI provider (requires restart)"""
    if provider not in ["gemini", "openrouter"]:
        raise HTTPException(status_code=400, detail="Invalid provider. Must be 'gemini' or 'openrouter'")

    # Note: This requires updating .env file and restarting the server
    return {
        "message": f"To use {provider}, update AI_PROVIDER={provider} in .env file and restart the server",
        "current_provider": settings.ai_provider
    }


# ==================== EXCEL ENDPOINTS ====================

@router.post("/detect-columns-excel", response_model=DetectColumnsResponse)
async def detect_columns_excel(document_id: str = Form(...), sheet_name: str = Form(None)):
    """
    Detect columns in Excel file with AI-powered header and type detection
    Returns column info with AI-classified types (currency/number/date/text)
    """
    try:
        # Get document metadata
        doc_meta = _get_document_metadata(document_id)
        file_path = Path(doc_meta["file_path"])
        file_type = doc_meta.get("file_type")

        # Verify it's an Excel file
        if file_type != "excel":
            raise HTTPException(status_code=400, detail="Document is not an Excel file")

        # Check if file exists
        if not file_path.exists():
            raise HTTPException(status_code=404, detail="Excel file expired or deleted")

        # Detect columns using Excel service with AI-powered type detection
        result = excel_service.detect_columns(file_path, sheet_name)

        # Convert to API response format
        # AI has already classified columns as currency/number/date/text
        from app.models.schemas import DetectedColumn
        detected_columns = [
            DetectedColumn(
                id=str(idx),
                name=col["name"],
                type=col["type"],  # AI-detected type (currency/number/date/text)
                confidence=1.0  # Excel columns with AI detection
            )
            for idx, col in enumerate(result["columns"])
        ]

        return DetectColumnsResponse(
            document_id=document_id,
            columns=detected_columns,
            processing_time=0.1  # Excel is instant
        )

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Excel column detection failed: {str(e)}")


@router.get("/excel-sheets/{document_id}")
async def get_excel_sheets(document_id: str):
    """Get all sheet names from an Excel file"""
    try:
        # Get document metadata
        doc_meta = _get_document_metadata(document_id)
        file_path = Path(doc_meta["file_path"])
        file_type = doc_meta.get("file_type")

        # Verify it's an Excel file
        if file_type != "excel":
            raise HTTPException(status_code=400, detail="Document is not an Excel file")

        # Check if file exists
        if not file_path.exists():
            raise HTTPException(status_code=404, detail="Excel file expired or deleted")

        # Get sheet names
        sheet_names = excel_service.get_sheet_names(file_path)

        return {
            "document_id": document_id,
            "sheets": sheet_names,
            "sheet_count": len(sheet_names)
        }

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get Excel sheets: {str(e)}")


@router.post("/extract-data-excel")
async def extract_data_excel(request: ExtractDataRequest):
    """
    Extract data from Excel file and convert to CSV (fast, no AI needed)
    """
    try:
        # Get document metadata
        doc_meta = _get_document_metadata(request.document_id)
        file_path = Path(doc_meta["file_path"])
        file_type = doc_meta.get("file_type")

        # Verify it's an Excel file
        if file_type != "excel":
            raise HTTPException(status_code=400, detail="Document is not an Excel file")

        # Check if file exists
        if not file_path.exists():
            raise HTTPException(status_code=404, detail="Excel file expired or deleted")

        # Extract selected columns
        selected_col_names = [col.name for col in request.selected_columns] if request.selected_columns else None

        # Convert to CSV
        csv_path = excel_service.convert_to_csv(
            file_path=file_path,
            selected_columns=selected_col_names,
            sheet_name=None  # Use first sheet or add to request
        )

        # Read CSV data as List[List[str]] (matches ExtractDataResponse schema)
        import csv
        csv_data = []
        with open(csv_path, 'r', encoding='utf-8') as f:
            reader = csv.reader(f)
            csv_data = list(reader)

        # Get CSV as base64 for download
        import base64
        with open(csv_path, 'rb') as f:
            csv_base64 = base64.b64encode(f.read()).decode('utf-8')

        # NOTE: Excel files are NOT deleted after extraction to allow re-conversion with different settings
        # They will be auto-deleted after TTL expires (default: 1 hour)
        # PDF files are still deleted immediately after extraction for security

        return ExtractDataResponse(
            document_id=request.document_id,
            data=csv_data,
            rows_extracted=len(csv_data) - 1 if len(csv_data) > 0 else 0,  # Exclude header row
            processing_time=0.2  # Excel is very fast
        )

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Excel extraction failed: {str(e)}")
