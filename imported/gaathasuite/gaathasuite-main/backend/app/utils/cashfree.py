import os
from app.config import Config
from cashfree_pg.api_client import APIClient
from cashfree_pg.configuration import Configuration
from cashfree_pg.exceptions import (
    ApiException,
    AuthenticationException,
    InvalidRequestException,
    RateLimitException,
)
from cashfree_pg.models.create_order_request import CreateOrderRequest
from cashfree_pg.models.customer_details import CustomerDetails

# Initialize Cashfree client from environment variables
CASHFREE_CLIENT_ID = os.environ.get("CASHFREE_CLIENT_ID")
CASHFREE_CLIENT_SECRET = os.environ.get("CASHFREE_CLIENT_SECRET")
CASHFREE_ENV = os.environ.get("CASHFREE_ENV", "sandbox")  # or "production"

try:
    # Use Configuration and APIClient for initialization, which is correct for v2.x, v3.x, etc.
    config = Configuration(
        client_id=CASHFREE_CLIENT_ID,
        client_secret=CASHFREE_CLIENT_SECRET,
        environment=CASHFREE_ENV
    )
    api_client = APIClient(config)
except Exception as e:
    print(f"Failed to initialize Cashfree client: {e}")
    api_client = None

async def create_payment_order(
    order_id: str,
    amount: float,
    currency: str,
    customer_name: str,
    customer_email: str,
    customer_phone: str,
) -> dict:
    """
    Creates a payment order with Cashfree and returns the payment session ID.
    """
    if not api_client:
        raise Exception("Cashfree client is not initialized.")

    create_order_request = CreateOrderRequest(
        order_id=order_id,
        order_amount=amount,
        order_currency=currency,
        customer_details=CustomerDetails(customer_id=customer_email, customer_email=customer_email, customer_phone=customer_phone, customer_name=customer_name),
        order_meta={"return_url": Config.public_url(f"/superadmin/payment/status?order_id={{order_id}}")},
    )

    api_response = api_client.order.create_order(x_api_version="2022-09-01", create_order_request=create_order_request)
    return api_response.data.to_dict()