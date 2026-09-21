from celery.schedules import crontab

CELERY_BEAT_SCHEDULE = {
    "weekly-business-digest": {
        "task": "tasks.send_weekly_digest",
        "schedule": crontab(hour=8, minute=0, day_of_week=1), # Mondays at 8 AM
    },
    "daily-file-cleanup": {
        "task": "tasks.cleanup_old_exports",
        "schedule": crontab(hour=0, minute=0), # Daily at Midnight
    },
    "periodic-scheduled-reports": {
        "task": "tasks.run_scheduled_reports",
        "schedule": crontab(minute=0), # Every hour
    },
}

# This should be imported and applied to the celery_app instance:
# celery_app.conf.beat_schedule = CELERY_BEAT_SCHEDULE