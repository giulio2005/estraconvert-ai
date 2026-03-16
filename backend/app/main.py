from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.api.routes import router
from app.config import settings
from app.services.cleanup_scheduler import get_cleanup_scheduler
from app.services.redis_service import get_redis_service
from app.services.file_manager import get_file_manager
import logging

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)

logger = logging.getLogger(__name__)

# Create FastAPI app
app = FastAPI(
    title="EstraConvert API",
    description="AI-powered secure document to CSV conversion API with automatic cleanup",
    version="1.1.0",
)

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins_list,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routes
app.include_router(router, prefix="/api", tags=["conversion"])


@app.on_event("startup")
async def startup_event():
    logger.info("🚀 EstraConvert API starting up...")
    logger.info(f"📁 Upload directory: {settings.upload_dir}")
    logger.info(f"🌐 CORS origins: {settings.cors_origins_list}")

    # Initialize Redis
    redis_service = get_redis_service()
    if redis_service.is_available():
        logger.info(f"✅ Redis cache enabled (TTL: {settings.cache_ttl}s)")
    else:
        logger.warning("⚠️  Redis unavailable - using in-memory fallback")

    # Initialize file manager
    file_manager = get_file_manager()
    logger.info(f"📂 File TTL: {settings.file_ttl}s ({settings.file_ttl // 60} minutes)")

    # Start cleanup scheduler
    scheduler = get_cleanup_scheduler()
    scheduler.start()
    logger.info("🧹 Automatic cleanup scheduler started (runs every 10 minutes)")

    # Initial cleanup on startup
    file_stats = file_manager.get_file_stats()
    logger.info(f"📊 Current storage: {file_stats.get('total_files', 0)} files, {file_stats.get('total_size_mb', 0)} MB")


@app.on_event("shutdown")
async def shutdown_event():
    logger.info("👋 EstraConvert API shutting down...")

    # Stop cleanup scheduler
    try:
        scheduler = get_cleanup_scheduler()
        scheduler.stop()
        logger.info("🛑 Cleanup scheduler stopped")
    except Exception as e:
        logger.error(f"Error stopping scheduler: {e}")


@app.get("/")
async def root():
    return {
        "service": "EstraConvert API",
        "version": "1.1.0",
        "status": "running",
        "features": [
            "Automatic file cleanup",
            "Redis caching with TTL",
            "Secure temporary storage",
            "Post-extraction file deletion"
        ],
        "docs": "/docs",
    }


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(
        "app.main:app",
        host=settings.host,
        port=settings.port,
        reload=settings.reload,
    )
