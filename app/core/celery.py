from __future__ import absolute_import, unicode_literals
import os
from celery import Celery
from celery.schedules import crontab
from django.conf import settings

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'core.settings')

app = Celery('core')

app.config_from_object('django.conf:settings', namespace='CELERY')

app.autodiscover_tasks()

app.conf.beat_schedule = {
    'activate-scheduled-subscriptions-every-hour': {
        'task': 'subscriptions.tasks.activate_scheduled_subscriptions',
        'schedule': crontab(minute=0),  # every hour at minute 0
    },
}
