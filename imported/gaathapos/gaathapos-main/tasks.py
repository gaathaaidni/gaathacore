from celery_app import celery
from app import create_app
import time
from datetime import datetime, timedelta
from sqlalchemy import func

@celery.task(bind=True)
def send_async_email(self, recipient, subject, body):
    """
    Background task to send an email.
    Creates a temporary Flask app context to access config and extensions.
    """
    app = create_app()
    with app.app_context():
        try:
            from extensions import mail
            from flask_mail import Message
            
            sender = app.config.get('MAIL_DEFAULT_SENDER', 'noreply@nexorapos.com')
            msg = Message(subject, sender=sender, recipients=[recipient])
            msg.body = body
            
            mail.send(msg)
            print("Email sent successfully!")
            return {'status': 'Success', 'recipient': recipient}
        except Exception as e:
            # Retry in 60 seconds if email sending fails (up to 3 times)
            self.retry(exc=e, countdown=60, max_retries=3)
            print(f"Failed to send email: {e}")
            return {'status': 'Failed', 'error': str(e)}

@celery.task(bind=True)
def generate_daily_sales_report(self):
    """
    Periodic background task to generate a sales report 
    for the previous day and email it to admins.
    """
    app = create_app()
    with app.app_context():
        try:
            # Calculate yesterday's date
            from extensions import db
            from models import Order, OrderItem, MenuItem, Restaurant, User
            
            # For a multi-tenant app, we must generate a report for each restaurant.
            restaurants = Restaurant.query.all()
            if not restaurants:
                print("No restaurants found to generate reports for.")
                return

            for restaurant in restaurants:
                # Calculate exactly midnight for today and yesterday to get a clean 24hr window
                today = datetime.utcnow().replace(hour=0, minute=0, second=0, microsecond=0)
                yesterday_start = today - timedelta(days=1)
                date_str = yesterday_start.strftime('%Y-%m-%d')
                
                # Calculate Total Orders (completed statuses) for the current restaurant in the loop
                total_orders = Order.query.filter(
                    Order.restaurant_id == restaurant.id, # Filter by restaurant
                    Order.created_at >= yesterday_start,
                    Order.created_at < today,
                    Order.status.in_(['ready', 'served'])
                ).count()

                # Calculate Total Revenue per restaurant
                revenue = db.session.query(func.sum(OrderItem.quantity * MenuItem.price)) \
                    .join(MenuItem, OrderItem.menu_item_id == MenuItem.id) \
                    .join(Order, OrderItem.order_id == Order.id) \
                    .filter(Order.restaurant_id == restaurant.id) \
                    .filter(Order.created_at >= yesterday_start, Order.created_at < today) \
                    .filter(Order.status.in_(['ready', 'served'])) \
                    .scalar()

                total_revenue = float(revenue or 0.0)

                # Find admins for this restaurant to email the report
                admins = User.query.filter_by(restaurant_id=restaurant.id, role='restaurant_admin').all()
                admin_emails = [admin.email for admin in admins if admin.email]

                if not admin_emails:
                    print(f"No admin emails found for restaurant {restaurant.name}")
                    continue

                report_body = f"Hello Admin,\n\nHere is the sales report for {restaurant.name} for {date_str}.\n\nTotal Orders: {total_orders}\nTotal Revenue: ${total_revenue:,.2f}\n"
                # Trigger an email for each restaurant's admin(s)
                # Ensure the first argument to the email task is a list of strings
                send_async_email.delay(admin_emails, f"Daily Sales Report - {restaurant.name} - {date_str}", report_body)
        except Exception as e:
            print(f"Failed to generate report: {e}")

@celery.task(bind=True)
def deduct_inventory_for_order(self, order_id, restaurant_id=None):
    """Legacy inventory deduction task is intentionally inert.

    The active inventory path is the Product-based service. This task remains as a
    compatibility stub so it cannot mutate stock or process data from another restaurant.
    """
    app = create_app()
    with app.app_context():
        try:
            from models import Order
            if restaurant_id is None:
                raise ValueError("Legacy inventory deduction requires an explicit restaurant_id")
            order = Order.query.filter_by(id=order_id, restaurant_id=restaurant_id).first()
            if not order:
                print(f"Legacy inventory deduction skipped: order {order_id} not found for restaurant {restaurant_id}.")
                return {"status": "skipped", "order_id": order_id, "restaurant_id": restaurant_id, "reason": "order_not_found"}
            print(
                f"Legacy inventory deduction disabled for order {order_id} restaurant {restaurant_id}: "
                "Product-based stock reconciliation is the only active path."
            )
            return {"status": "disabled", "order_id": order_id, "restaurant_id": restaurant_id}
        except Exception as exc:
            print(f"Legacy inventory deduction failed safely for order {order_id}: {exc}")
            return {"status": "failed", "order_id": order_id, "restaurant_id": restaurant_id, "error": str(exc)}