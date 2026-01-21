"""
Celery Configuration for HPE
Used for background tasks like backup, email notifications, etc.
"""
import os
from celery import Celery
from celery.schedules import crontab

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings.production')

app = Celery('hpe')
app.config_from_object('django.conf:settings', namespace='CELERY')
app.autodiscover_tasks()

# Celery Beat Schedule for automated tasks
app.conf.beat_schedule = {
    # Daily backup at 2:00 AM
    'daily-backup': {
        'task': 'apps.core.tasks.daily_backup',
        'schedule': crontab(hour=2, minute=0),
    },
    # Safety stock check every hour
    'check-safety-stock': {
        'task': 'apps.inventory.tasks.check_safety_stock_levels',
        'schedule': crontab(minute=0),  # Every hour
    },
    # Document approval reminder at 9:00 AM
    'approval-reminder': {
        'task': 'apps.documents.tasks.send_pending_approval_reminders',
        'schedule': crontab(hour=9, minute=0),
    },
}

app.conf.timezone = 'Asia/Seoul'
