from celery import Celery
from ..core.config import get_settings

celery_app = Celery(
    "scholarship_finder",
    broker=get_settings().redis_url,
    backend=get_settings().redis_url,
    include=["app.workers.tasks"],
)
celery_app.conf.update(task_acks_late=True, task_track_started=True, worker_prefetch_multiplier=1)
