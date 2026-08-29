import os
from celery import Celery
from celery.schedules import crontab
from app.core.config import settings

# Initialize Celery app instance
celery_app = Celery(
    "dwrms_worker",
    broker=settings.CELERY_BROKER_URL,
    backend=settings.CELERY_RESULT_BACKEND,
    include=["app.worker"],
)

# Celery Configuration
celery_app.conf.update(
    task_serializer="json",
    accept_content=["json"],
    result_serializer="json",
    timezone="Africa/Harare",  # Central Africa Time (CAT)
    enable_utc=True,
    task_track_started=True,
    task_time_limit=300,  # 5 minutes hard limit per task
    worker_prefetch_multiplier=1,
    worker_max_tasks_per_child=1000,
)

# Celery Beat Scheduled Tasks
celery_app.conf.beat_schedule = {
    "escalate-overdue-approvals-every-5min": {
        "task": "app.worker.check_and_escalate_overdue_approvals",
        "schedule": 300.0,  # Every 5 minutes
    },
    "purge-temp-storage-daily": {
        "task": "app.worker.purge_temp_storage",
        "schedule": crontab(hour=3, minute=0),  # Daily at 03:00 CAT
    },
    "worker-health-heartbeat-hourly": {
        "task": "app.worker.heartbeat_task",
        "schedule": 3600.0,  # Every hour
    },
}
