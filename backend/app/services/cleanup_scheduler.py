"""
Background scheduler for automatic file cleanup
Runs periodic cleanup of expired files
"""
import logging
from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.interval import IntervalTrigger
from app.services.file_manager import get_file_manager
from app.config import settings

logger = logging.getLogger(__name__)


class CleanupScheduler:
    """Manages background cleanup tasks"""

    def __init__(self):
        """Initialize scheduler"""
        self.scheduler = BackgroundScheduler()
        self.file_manager = get_file_manager()
        self._setup_jobs()

    def _setup_jobs(self):
        """Setup scheduled cleanup jobs"""
        # Run cleanup every 10 minutes
        self.scheduler.add_job(
            func=self._cleanup_expired_files,
            trigger=IntervalTrigger(minutes=10),
            id='cleanup_expired_files',
            name='Cleanup expired files',
            replace_existing=True,
        )

        logger.info("📅 Cleanup scheduler configured (runs every 10 minutes)")

    def _cleanup_expired_files(self):
        """Execute file cleanup task"""
        try:
            logger.info("🧹 Running scheduled file cleanup...")
            deleted = self.file_manager.cleanup_expired_files()

            if deleted > 0:
                logger.info(f"✅ Cleanup completed: {deleted} files deleted")
            else:
                logger.debug("✅ Cleanup completed: no expired files found")

            # Log storage stats
            stats = self.file_manager.get_file_stats()
            logger.info(f"📊 Storage: {stats.get('total_files', 0)} files, {stats.get('total_size_mb', 0)} MB")

        except Exception as e:
            logger.error(f"❌ Cleanup task failed: {e}")

    def start(self):
        """Start the scheduler"""
        if not self.scheduler.running:
            self.scheduler.start()
            logger.info("✅ Cleanup scheduler started")

            # Run initial cleanup
            self._cleanup_expired_files()

    def stop(self):
        """Stop the scheduler"""
        if self.scheduler.running:
            self.scheduler.shutdown(wait=False)
            logger.info("🛑 Cleanup scheduler stopped")

    def get_status(self) -> dict:
        """Get scheduler status"""
        jobs = self.scheduler.get_jobs()
        return {
            "running": self.scheduler.running,
            "jobs": [
                {
                    "id": job.id,
                    "name": job.name,
                    "next_run": str(job.next_run_time) if hasattr(job, 'next_run_time') and job.next_run_time else "N/A",
                }
                for job in jobs
            ],
        }


# Global instance
_cleanup_scheduler = None


def get_cleanup_scheduler() -> CleanupScheduler:
    """Get or create CleanupScheduler singleton"""
    global _cleanup_scheduler
    if _cleanup_scheduler is None:
        _cleanup_scheduler = CleanupScheduler()
    return _cleanup_scheduler
