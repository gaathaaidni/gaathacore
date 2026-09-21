import os
from celery import Celery
from celery.schedules import crontab

# Define the Redis URL for broker and backend.
# We use different DB numbers to separate Celery data from rate-limiting data.
redis_base_url = (
    os.getenv('RATELIMIT_STORAGE_URI')
    or os.getenv('REDIS_URL')
    or 'redis://redis:6379/0'
).rsplit('/', 1)[0]
broker_url = f"{redis_base_url}/1"
result_backend = f"{redis_base_url}/2"

# Create the Celery app instance
celery = Celery(
    'gaatha_tasks',
    broker=broker_url,
    backend=result_backend,
    include=['tasks']  # Points to the tasks.py file to find tasks
)

celery.conf.update(
    task_serializer='json',
    accept_content=['json'],
    result_serializer='json',
    timezone='UTC',
    enable_utc=True,
    broker_connection_retry_on_startup=True, # Add this to address deprecation warning
)

# Configure Periodic Tasks (Celery Beat)
celery.conf.beat_schedule = {
    'daily-sales-report': {
        'task': 'tasks.generate_daily_sales_report',
        'schedule': crontab(hour=2, minute=0), # Runs every night at 2:00 AM UTC
    },
}