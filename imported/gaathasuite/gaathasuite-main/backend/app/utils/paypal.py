import os
import paypalrestsdk
import logging
from app.config import Config

logger = logging.getLogger(__name__)

PAYPAL_CLIENT_ID = os.environ.get("PAYPAL_CLIENT_ID")
PAYPAL_CLIENT_SECRET = os.environ.get("PAYPAL_CLIENT_SECRET")
PAYPAL_MODE = os.environ.get("PAYPAL_MODE", "sandbox")  # "sandbox" or "live"

try:
    paypalrestsdk.configure({
        "mode": PAYPAL_MODE,
        "client_id": PAYPAL_CLIENT_ID,
        "client_secret": PAYPAL_CLIENT_SECRET
    })
    logger.info("PayPal SDK configured successfully for mode: %s", PAYPAL_MODE)
except Exception as e:
    logger.error("Failed to configure PayPal SDK: %s", e, exc_info=True)


def create_paypal_payment(order_id: str, amount: float, currency: str, description: str) -> paypalrestsdk.Payment | None:
    """
    Creates a PayPal payment and returns the payment object.
    """
    try:
        payment = paypalrestsdk.Payment({
            "intent": "sale",
            "payer": {
                "payment_method": "paypal"
            },
            "redirect_urls": {
                "return_url": Config.public_url(f"/payment/execute?order_id={order_id}"),
                "cancel_url": Config.public_url(f"/payment/cancel?order_id={order_id}")
            },
            "transactions": [{
                "item_list": {
                    "items": [{"name": description, "sku": order_id, "price": str(amount), "currency": currency, "quantity": 1}]
                },
                "amount": {"total": str(amount), "currency": currency},
                "description": description
            }]
        })

        if payment.create():
            return payment
        else:
            logger.error("PayPal payment creation failed: %s", payment.error)
            return None
    except Exception as e:
        logger.error("Exception while creating PayPal payment: %s", e, exc_info=True)
        return None