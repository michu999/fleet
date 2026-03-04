"""
Celery application configuration.
"""

from celery import Celery

from app.core.config import settings

celery_app = Celery(
    "fleet",
    broker=settings.REDIS_URL,
    backend=settings.REDIS_URL,
    include=[

    ],
)

celery_app.conf.update(
    task_serializer="json",
    accept_content=["json"],
    result_serializer="json",
    timezone="UTC",
    enable_utc=True,
    task_track_started=True,
    task_time_limit=30 * 60,  # 30 minut
    worker_prefetch_multiplier=1,
)
