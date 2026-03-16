"""
Celery application for async task processing
Handles document processing tasks (OCR, AI extraction) in background
"""
import logging
from celery import Celery
from app.config import settings

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Create Celery app
celery_app = Celery(
    'estraconvert',
    broker=settings.celery_broker,
    backend=settings.celery_backend,
    include=['app.tasks.document_tasks']
)

# Celery configuration
celery_app.conf.update(
    # Serialization
    task_serializer='json',
    result_serializer='json',
    accept_content=['json'],

    # Timezone
    timezone='Europe/Rome',
    enable_utc=True,

    # Task tracking
    task_track_started=True,
    task_send_sent_event=True,

    # Timeouts
    task_time_limit=settings.celery_task_time_limit,
    task_soft_time_limit=settings.celery_task_time_limit - 30,

    # Results
    result_expires=settings.celery_result_expires,
    result_persistent=False,

    # Worker settings
    worker_prefetch_multiplier=1,
    worker_max_tasks_per_child=100,

    # Retry policy
    task_acks_late=True,
    task_reject_on_worker_lost=True,
)

logger.info(f"🔄 Celery app configured")
logger.info(f"   Broker: {settings.celery_broker}")
logger.info(f"   Backend: {settings.celery_backend}")
logger.info(f"   Task time limit: {settings.celery_task_time_limit}s")
logger.info(f"   Result expires: {settings.celery_result_expires}s")

if __name__ == '__main__':
    celery_app.start()
