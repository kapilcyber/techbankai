"""Celery configuration."""
from src.config.settings import settings

# Celery Configuration from settings
CELERY_BROKER_URL = settings.celery_broker_url
CELERY_RESULT_BACKEND = settings.celery_result_backend

