from celery import Celery

from backend.app.core.config import settings

celery_app = Celery(
    "databridge",
    broker=settings.CELERY_BROKER_URL,
    backend=settings.CELERY_RESULT_BACKEND,
)

celery_app.conf.update(
    task_serializer="json",
    accept_content=["json"],
    result_serializer="json",
    timezone="UTC",
    enable_utc=True,
    task_track_started=True,
    task_acks_late=True,
    worker_prefetch_multiplier=1,
    worker_max_tasks_per_child=100,
    task_soft_time_limit=3600,
    task_time_limit=7200,
    task_routes={
        "backend.app.tasks.scanning.*": {"queue": "scanning"},
        "backend.app.tasks.transfer_tasks.*": {"queue": "transfer"},
        "backend.app.tasks.notification_tasks.*": {"queue": "notifications"},
    },
)

celery_app.autodiscover_tasks(["backend.app.tasks"])
