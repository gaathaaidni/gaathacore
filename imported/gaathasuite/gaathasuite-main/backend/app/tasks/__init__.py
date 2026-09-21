"""
Celery configuration and task definitions for async operations.
Handles background tasks like email sending and report generation.
"""
from celery import Celery
from flask import Flask
from typing import Optional
import os


# Initialize Celery
celery = Celery(__name__)


def init_celery(app: Flask) -> Celery:
    """
    Initialize Celery with Flask app configuration.
    
    Args:
        app: Flask application instance
        
    Returns:
        Configured Celery instance
    """
    # Configure Celery from Flask config
    celery.conf.update(app.config.get('CELERY_CONFIG', {}))
    
    # Use the app's SECRET_KEY if available
    if hasattr(app, 'config') and 'SECRET_KEY' in app.config:
        celery.conf.update(security_key=app.config['SECRET_KEY'])
    
    class ContextTask(celery.Task):
        """Make celery tasks work with Flask app context."""
        def __call__(self, *args, **kwargs):
            with app.app_context():
                return self.run(*args, **kwargs)
    
    celery.Task = ContextTask
    return celery


# Task definitions
@celery.task(bind=True, max_retries=3)
def send_email_task(self, recipient: str, subject: str, body: str) -> dict:
    """
    Async task to send an email.
    
    Args:
        recipient: Email recipient address
        subject: Email subject
        body: Email body
        
    Returns:
        Result dictionary with status
    """
    try:
        from flask_mail import Mail, Message
        from flask import current_app
        
        # This would be implemented with actual email service
        # For now, just log the action
        print(f"Sending email to {recipient}: {subject}")
        
        return {
            'status': 'sent',
            'recipient': recipient,
            'subject': subject,
        }
    except Exception as exc:
        # Retry with exponential backoff
        raise self.retry(exc=exc, countdown=60 * (2 ** self.request.retries))


@celery.task(bind=True, max_retries=2)
def generate_report_task(
    self,
    report_type: str,
    start_date: str,
    end_date: str,
    user_id: int
) -> dict:
    """
    Async task to generate business reports.
    
    Args:
        report_type: Type of report (sales, inventory, payroll, etc.)
        start_date: Report start date (YYYY-MM-DD)
        end_date: Report end date (YYYY-MM-DD)
        user_id: User requesting the report
        
    Returns:
        Result dictionary with report details
    """
    try:
        # Report generation logic would go here
        print(f"Generating {report_type} report from {start_date} to {end_date}")
        
        return {
            'status': 'completed',
            'report_type': report_type,
            'user_id': user_id,
        }
    except Exception as exc:
        raise self.retry(exc=exc, countdown=60)


@celery.task(bind=True)
def send_invoice_email(self, invoice_id: int, recipient_email: str) -> dict:
    """
    Async task to send invoice via email.
    
    Args:
        invoice_id: Invoice ID to send
        recipient_email: Email recipient
        
    Returns:
        Result dictionary
    """
    try:
        from app.models import Invoice
        from extensions import db
        
        invoice = Invoice.query.get(invoice_id)
        if not invoice:
            return {'status': 'error', 'message': 'Invoice not found'}
        
        # Email sending logic
        print(f"Sending invoice {invoice.number} to {recipient_email}")
        
        return {
            'status': 'sent',
            'invoice_id': invoice_id,
            'recipient': recipient_email,
        }
    except Exception as exc:
        raise self.retry(exc=exc, countdown=60)


@celery.task
def sync_data_task(source: str, destination: str) -> dict:
    """
    Async task for data synchronization operations.
    
    Args:
        source: Source system
        destination: Destination system
        
    Returns:
        Sync result
    """
    print(f"Syncing data from {source} to {destination}")
    return {
        'status': 'completed',
        'source': source,
        'destination': destination,
    }


# Celery configuration defaults
DEFAULT_CELERY_CONFIG = {
    'broker_url': os.environ.get('CELERY_BROKER_URL', 'redis://localhost:6379/0'),
    'result_backend': os.environ.get('CELERY_RESULT_BACKEND', 'redis://localhost:6379/0'),
    'accept_content': ['json'],
    'task_serializer': 'json',
    'result_serializer': 'json',
    'timezone': 'UTC',
    'enable_utc': True,
    'task_track_started': True,
    'task_time_limit': 30 * 60,  # Hard time limit 30 minutes
    'task_soft_time_limit': 25 * 60,  # Soft time limit 25 minutes
}
