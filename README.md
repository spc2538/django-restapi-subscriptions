# Stack

- Django
- Firebase Authentication
- Stripe
- Celery Beat
- Redis
- PostgreSQL

## Commands

```bash
virtualenv venv -p python
source venv/bin/activate
pip install django
pip freeze > requirements.txt
mkdir -p app
django-admin startproject core app
cd app
python manage.py migrate
python manage.py runserver
```


```bash
PATHG=app
sudo chown -R $USER:$USER $PATHG
sudo chmod -R 775 $PATHG
sudo find $PATHG -type d -exec chmod 0775 "{}" \;
sudo find $PATHG -type f -exec chmod 0664 "{}" \;
```

## Celery tasks Integration

- Install

```bash
pip install celery[redis] django-celery-beat
```

- Add `django-celery-beat` to `INSTALLED_APPS`:

```python
INSTALLED_APPS = [
    'django_celery_beat',
]
```

- Run migrations

```bash
python manage.py migrate
```

- `core/celery.py` manager file

```python
# core/celery.py
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
        'schedule': crontab(minute=0),  # cada hora a minuto 0
    },
}
```

- Import Celery app to `core/__init__.py`

```python
# core/__init__.py
from .celery import app as celery_app

__all__ = ('celery_app',)
```

- Add Celery settings to `settings.py`

```python
# Celery
CELERY_BROKER_URL = 'redis://127.0.0.1:6379/0'
CELERY_RESULT_BACKEND = 'redis://127.0.0.1:6379/0'
CELERY_ACCEPT_CONTENT = ['json']
CELERY_TASK_SERIALIZER = 'json'
CELERY_RESULT_SERIALIZER = 'json'
CELERY_TIMEZONE = 'UTC'

CELERY_TASK_DEFAULT_QUEUE = 'default'
```

- Celery worker and beat start commands

```bash
celery -A core worker --loglevel=info
celery -A core beat --loglevel=info
```

- Realizar pruebas manualmente con una tarea en especifico

```bash
python manage.py shell
>>> from subscriptions.tasks import activate_scheduled_subscriptions
>>> activate_scheduled_subscriptions.delay()
# Llamar directamente
>>> activate_scheduled_subscriptions()
```


