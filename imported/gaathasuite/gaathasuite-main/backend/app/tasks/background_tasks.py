import csv
import io
import logging
import os
import time
from datetime import datetime, timedelta
from decimal import Decimal
from sqlalchemy import select, func
from app.config import Config
from app.tasks import celery_app
from app.dependencies import get_db
from app.models.inventory import Item
from app.models.base import BackgroundTask, ScheduledReport, User
from app.models.notifications import Notification
from app.models.preferences import NotificationPreference
from app.models.books import Invoice
from app.models.crm import Customer
from app.utils.email import send_email
from app.utils.signing import generate_token

logger = logging.getLogger(__name__)

@celery_app.task(name="tasks.send_weekly_digest")
async def send_weekly_digest():
    task_record = None
    """
    Iterates through all organizations to aggregate 7-day stats 
    and sends a digest email to administrators.
    """
    async with get_db() as db:
        # Create a task record
        task_record = BackgroundTask(
            org_id=1, # Placeholder: In a real scenario, this would iterate through all orgs
            task_name="Weekly Digest Report",
            celery_task_id=send_weekly_digest.request.id,
            status="STARTED",
            started_at=datetime.utcnow()
        )
        db.add(task_record)
        await db.commit()

        # Logic to fetch all active Orgs would go here
        # For now, we simulate a loop or target specific orgs
        today = datetime.utcnow()
        last_week = today - timedelta(days=7)

        # Example: Aggregate Sales for the week
        sales_query = select(func.sum(Invoice.total_amount)).where(
            Invoice.created_at >= last_week,
            Invoice.status == "paid"
        )
        result = await db.execute(sales_query)
        total_sales = result.scalar() or 0.0

        # Example: Find Low Stock items
        low_stock_query = select(Item).where(Item.current_stock <= Item.min_stock_level)
        items_res = await db.execute(low_stock_query)
        low_stock_items = items_res.scalars().all()

        # Email sending logic using app.services.email
        result_info = f"Sales: ${total_sales:.2f}, Low Stock Alerts: {len(low_stock_items)}"
        logger.info(f"Weekly Digest Generated: {result_info}")

        # Send to Org Admins (simplified for placeholder org_id=1)
        admin_query = select(User).where(User.organization_id == 1, User.role == 'admin')
        admins = (await db.execute(admin_query)).scalars().all()
        
        for admin in admins:
            pref_res = await db.execute(select(NotificationPreference).where(NotificationPreference.user_id == admin.id))
            pref = pref_res.scalar_one_or_none()
            
            if not pref or pref.email_enabled:
                send_email(
                    to_email=admin.email,
                    subject="Gaatha Suite: Weekly Business Digest",
                    body=f"Hello {admin.username},\n\nHere is your weekly summary:\n{result_info}\n\nRegards,\nGaatha Suite Team"
                )

        task_record.status = "SUCCESS"
        task_record.completed_at = datetime.utcnow()
        task_record.result_info = result_info
        await db.commit()

@celery_app.task(name="tasks.process_bulk_import")
async def process_bulk_import(content: str, resource_type: str, org_id: int, user_id: int):
    """
    Processes CSV content in the background to create Items or Customers.
    """
    task_record = None
    f = io.StringIO(content)
    reader = csv.DictReader(f)
    
    async with get_db() as db:
        task_record = BackgroundTask(
            org_id=org_id,
            user_id=user_id,
            task_name=f"Bulk Import: {resource_type}",
            celery_task_id=process_bulk_import.request.id,
            status="STARTED",
            started_at=datetime.utcnow()
        )
        db.add(task_record)
        await db.commit()

        count = 0
        for row in reader:
            try:
                if resource_type == "items":
                    new_obj = Item(
                        org_id=org_id,
                        sku=row['sku'],
                        name=row['name'],
                        unit_price=Decimal(row.get('unit_price', 0)),
                        cost_price=Decimal(row.get('cost_price', 0)),
                        current_stock=int(row.get('initial_stock', 0))
                    )
                elif resource_type == "customers":
                    new_obj = Customer(
                        org_id=org_id,
                        name=row['name'],
                        email=row.get('email'),
                        phone=row.get('phone')
                    )
                
                db.add(new_obj)
                count += 1
                
                # Flush in chunks to avoid memory issues with massive CSVs
                if count % 100 == 0:
                    await db.flush()
                    
            except Exception as e:
                logger.error(f"Failed to import row {row}: {str(e)}")
                continue
        
        await db.commit()
        result_info = f"Successfully imported {count} {resource_type}."
        logger.info(f"Bulk Import Complete: {result_info}")
        
        task_record.status = "SUCCESS"
        task_record.completed_at = datetime.utcnow()
        task_record.result_info = result_info
        await db.commit()

@celery_app.task(name="tasks.export_data")
async def export_data(resource_type: str, org_id: int, user_id: int, columns: list = None, filters: dict = None):
    """
    Exports data for a given resource type to a CSV file.
    Supports custom column selection and basic filtering.
    """
    task_record = None
    async with get_db() as db:
        task_record = BackgroundTask(
            org_id=org_id,
            user_id=user_id,
            task_name=f"Data Export: {resource_type}",
            celery_task_id=export_data.request.id,
            status="STARTED",
            started_at=datetime.utcnow()
        )
        db.add(task_record)
        await db.commit()

        try:
            data = []
            headers = []
            
            # Base Query
            if resource_type == "items":
                query = select(Item).where(Item.org_id == org_id)
                available_headers = ["id", "sku", "name", "description", "unit_price", "cost_price", "current_stock", "min_stock_level"]
                result = await db.execute(query)
                items = result.scalars().all()
                headers = columns if columns else available_headers
                data = [[getattr(item, h) for h in headers] for item in items]
                
            elif resource_type == "invoices":
                query = select(Invoice).where(Invoice.org_id == org_id)
                available_headers = ["id", "customer_id", "status", "total_amount", "created_at", "reference"]
                result = await db.execute(query)
                invoices = result.scalars().all()
                headers = columns if columns else available_headers
                data = [[getattr(invoice, h) for h in headers] for invoice in invoices]
                
            elif resource_type == "customers":
                query = select(Customer).where(Customer.org_id == org_id)
                available_headers = ["id", "name", "email", "phone", "lead_source", "created_at"]
                result = await db.execute(query)
                customers = result.scalars().all()
                headers = columns if columns else available_headers
                data = [[getattr(customer, h) for h in headers] for customer in customers]
            else:
                raise ValueError(f"Unsupported export resource type: {resource_type}")

            if not data:
                raise ValueError(f"No data found for {resource_type} to export.")

            file_path = f"/tmp/export_{resource_type}_{org_id}_{datetime.now().strftime('%Y%m%d%H%M%S')}.csv"
            with open(file_path, 'w', newline='') as csvfile:
                writer = csv.writer(csvfile)
                writer.writerow(headers)
                writer.writerows(data)
            
            task_record.status = "SUCCESS"
            task_record.completed_at = datetime.utcnow()
            task_record.result_info = file_path
            
            # Check User Preferences
            pref_res = await db.execute(select(NotificationPreference).where(NotificationPreference.user_id == user_id))
            pref = pref_res.scalar_one_or_none()
            
            if not pref or pref.in_app_enabled:
                # Generate secure signed link
                signed_token = generate_token({"path": file_path, "user_id": user_id, "org_id": org_id})
                notification = Notification(
                    org_id=org_id,
                    user_id=user_id,
                    title="Export Ready",
                    message=f"Your custom {resource_type} report is ready for download.",
                    link=f"/api/v1/download?token={signed_token}"
                )
                db.add(notification)

            if not pref or pref.email_enabled:
                user_res = await db.execute(select(User).where(User.id == user_id))
                user = user_res.scalar_one_or_none()
                if user:
                    signed_token = generate_token({"path": file_path, "user_id": user_id, "org_id": org_id})
                    download_url = Config.public_url(f"/api/v1/download?token={signed_token}")
                    send_email(
                        to_email=user.email,
                        subject=f"Gaatha Suite: Your {resource_type} export is ready",
                        body=f"Hello,\n\nYour requested export is ready. You can download it here: {download_url}\n\nNote: This link will expire in 1 hour."
                    )
            
            await db.commit()
        except Exception as e:
            task_record.status = "FAILURE"
            task_record.completed_at = datetime.utcnow()
            task_record.result_info = f"Export failed: {str(e)}"
            await db.commit()
            logger.error(f"Data Export Failed for {resource_type} (Org: {org_id}): {str(e)}")

@celery_app.task(name="tasks.run_scheduled_reports")
async def run_scheduled_reports():
    """
    Periodic task (run via Celery Beat) that checks for due scheduled reports.
    """
    now = datetime.utcnow()
    async with get_db() as db:
        query = select(ScheduledReport).where(
            ScheduledReport.is_active == True,
            ScheduledReport.next_run_at <= now
        )
        result = await db.execute(query)
        reports = result.scalars().all()

        for report in reports:
            if report.report_type == "EXPORT":
                export_data.delay(report.resource_type, report.org_id, report.user_id)
            elif report.report_type == "DIGEST":
                # Logic for custom digest could be triggered here
                pass
            
            # Update next run time
            report.last_run_at = now
            interval = timedelta(days=1) if report.frequency == "DAILY" else timedelta(days=7)
            report.next_run_at = now + interval
            
        await db.commit()

@celery_app.task(name="tasks.send_password_reset_email")
async def send_password_reset_email(user_id: int, email: str):
    """
    Generates a secure token and sends a password reset email.
    """
    token = generate_token({"user_id": user_id, "action": "password_reset"})
    reset_url = Config.public_url(f"/auth/reset-password?token={token}")
    
    send_email(
        to_email=email,
        subject="Gaatha Suite: Password Reset Request",
        body=f"Hello,\n\nYou requested a password reset. Click the link below to set a new password:\n{reset_url}\n\nThis link expires in 1 hour."
    )
    logger.info(f"Password reset email sent to {email}")

@celery_app.task(name="tasks.cleanup_old_exports")
def cleanup_old_exports():
    """
    Maintenance task to delete export files older than 24 hours from /tmp.
    """
    now = time.time()
    cutoff = now - (24 * 3600)
    for filename in os.listdir("/tmp"):
        if filename.startswith("export_"):
            file_path = os.path.join("/tmp", filename)
            if os.path.isfile(file_path):
                if os.path.getmtime(file_path) < cutoff:
                    os.remove(file_path)
                    logger.info(f"Cleanup: Deleted old export file {file_path}")