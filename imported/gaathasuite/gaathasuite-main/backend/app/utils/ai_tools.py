import os
import httpx
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, or_, func, extract
from app.models.books import Invoice
from app.models.asset import Asset
from app.models.crm import Customer, Lead
from app.models.inventory import Item, StockTransaction
from app.models.purchase_order import PurchaseOrder # Needed for dashboard summary
from decimal import Decimal
from typing import Optional

# Groq configuration
GROQ_API_KEY = os.getenv("GROQ_API_TOKEN") or os.getenv("GROQ_API_KEY", "")
GROQ_URL = os.getenv("GROQ_URL", "https://api.groq.com/openai/v1/chat/completions")
GROQ_MODEL = os.getenv("GROQ_MODEL", "llama-3.1-70b-versatile")


def get_vani_system_prompt() -> str:
    """Return the default system prompt for the Vani AI assistant."""
    return (
        "You are Vani, Gaatha Suite's enterprise intelligence assistant. "
        "Help users with concise, accurate operational guidance across CRM, "
        "inventory, finance, HR, approvals, and reporting. When the user asks "
        "for an action, identify the safest next step and any data needed. "
        "Do not invent business records; explain assumptions clearly."
    )

# Define the tool schema for Groq
CREATE_DRAFT_INVOICE_TOOL = {
    "type": "function",
    "function": {
        "name": "create_draft_invoice",
        "description": "Creates a new draft invoice for a customer.",
        "parameters": {
            "type": "object",
            "properties": {
                "customer_name": {
                    "type": "string",
                    "description": "The name of the customer for whom the invoice is being created."
                },
                "total_amount": {
                    "type": "number",
                    "description": "The total amount of the invoice."
                },
                "reference": {
                    "type": "string",
                    "description": "An optional reference number or description for the invoice."
                }
            },
            "required": ["customer_name", "total_amount"]
        }
    }
}

CREATE_CUSTOMER_TOOL = {
    "type": "function",
    "function": {
        "name": "create_customer",
        "description": "Creates a new customer record.",
        "parameters": {
            "type": "object",
            "properties": {
                "name": {"type": "string", "description": "The full name of the customer."},
                "email": {"type": "string", "description": "The customer's email address."},
                "phone": {"type": "string", "description": "The customer's phone number."},
                "lead_source": {"type": "string", "description": "Where the lead came from."}
            },
            "required": ["name"]
        }
    }
}

UPDATE_CUSTOMER_TOOL = {
    "type": "function",
    "function": {
        "name": "update_customer",
        "description": "Updates an existing customer's details.",
        "parameters": {
            "type": "object",
            "properties": {
                "current_name": {"type": "string", "description": "The current name of the customer to identify them."},
                "new_name": {"type": "string", "description": "The new name for the customer."},
                "email": {"type": "string", "description": "The new email address."},
                "phone": {"type": "string", "description": "The new phone number."}
            },
            "required": ["current_name"]
        }
    }
}

CREATE_LEAD_TOOL = {
    "type": "function",
    "function": {
        "name": "create_lead",
        "description": "Creates a new lead in the CRM.",
        "parameters": {
            "type": "object",
            "properties": {
                "name": {"type": "string", "description": "The name of the lead contact."},
                "email": {"type": "string", "description": "Email address of the lead."},
                "phone": {"type": "string", "description": "Phone number of the lead."},
                "source": {"type": "string", "description": "The source of the lead (e.g. Web, Referral)."}
            },
            "required": ["name"]
        }
    }
}

GET_INVENTORY_TOOL = {
    "type": "function",
    "function": {
        "name": "get_inventory",
        "description": "Looks up items in the inventory by name or SKU to check stock levels.",
        "parameters": {
            "type": "object",
            "properties": {
                "search_query": {
                    "type": "string",
                    "description": "The name or SKU of the item to look up."
                }
            },
            "required": ["search_query"]
        }
    }
}

ADJUST_STOCK_TOOL = {
    "type": "function",
    "function": {
        "name": "adjust_stock",
        "description": "Adjusts the stock level for a specific item (addition or removal).",
        "parameters": {
            "type": "object",
            "properties": {
                "item_identifier": {"type": "string", "description": "The name or SKU of the item."},
                "quantity": {"type": "integer", "description": "The quantity to add (positive) or remove (negative)."},
                "reason": {"type": "string", "description": "The reason for the adjustment (e.g., Damage, Correction)."},
                "warehouse_id": {"type": "integer", "description": "The ID of the warehouse. Defaults to 1 if unknown."}
            },
            "required": ["item_identifier", "quantity"]
        }
    }
}

GET_DASHBOARD_SUMMARY_TOOL = {
    "type": "function",
    "function": {
        "name": "get_dashboard_summary",
        "description": "Retrieves the current month's dashboard summary including sales, cash flow, inventory valuation, and low stock alerts.",
        "parameters": {
            "type": "object",
            "properties": {
                # No specific parameters needed for current month's summary
            },
            "required": []
        }
    }
}

ANALYZE_EXPENSES_TOOL = {
    "type": "function",
    "function": {
        "name": "analyze_expenses",
        "description": "Analyzes expense trends by category for the current year.",
        "parameters": {
            "type": "object",
            "properties": {},
            "required": []
        }
    }
}

ANALYZE_VENDORS_TOOL = {
    "type": "function",
    "function": {
        "name": "analyze_vendors",
        "description": "Analyzes vendor performance based on total spend and order volume.",
        "parameters": {
            "type": "object",
            "properties": {
                "limit": {
                    "type": "integer",
                    "description": "Number of top vendors to return (default 5)."
                }
            },
            "required": []
        }
    }
}

GET_ACTIVITY_LOGS_TOOL = {
    "type": "function",
    "function": {
        "name": "get_activity_logs",
        "description": "Fetches recent activity logs for the organization, optionally filtered by user.",
        "parameters": {
            "type": "object",
            "properties": {
                "user_id": {
                    "type": "integer",
                    "description": "Optional user ID to filter logs by a specific user."
                },
                "limit": {
                    "type": "integer",
                    "description": "Maximum number of recent logs to return. Defaults to 10."
                }
            },
            "required": []
        }
    }
}

CREATE_ASSET_TOOL = {
    "type": "function",
    "function": {
        "name": "create_asset",
        "description": "Adds a new asset to the system with acquisition details and useful life.",
        "parameters": {
            "type": "object",
            "properties": {
                "name": {"type": "string", "description": "Name of the asset."},
                "cost": {"type": "number", "description": "Purchase cost of the asset."},
                "useful_life_years": {"type": "integer", "description": "Useful life of the asset in years."},
                "acquisition_date": {"type": "string", "description": "Acquisition date in YYYY-MM-DD format."},
                "salvage_value": {"type": "number", "description": "Estimated salvage value at end of life."}
            },
            "required": ["name", "cost", "useful_life_years", "acquisition_date"]
        }
    }
}

DEPRECIATE_ASSET_TOOL = {
    "type": "function",
    "function": {
        "name": "depreciate_asset",
        "description": "Depreciates an existing asset for a given date and records the entry.",
        "parameters": {
            "type": "object",
            "properties": {
                "asset_name": {"type": "string", "description": "Name of the asset to depreciate."},
                "depreciation_date": {"type": "string", "description": "Date of depreciation in YYYY-MM-DD format."}
            },
            "required": ["asset_name", "depreciation_date"]
        }
    }
}

NORA_TOOLSET = [
    CREATE_DRAFT_INVOICE_TOOL,
    CREATE_CUSTOMER_TOOL,
    UPDATE_CUSTOMER_TOOL,
    GET_INVENTORY_TOOL,
    ADJUST_STOCK_TOOL,
    GET_DASHBOARD_SUMMARY_TOOL,
    CREATE_LEAD_TOOL,
    ANALYZE_EXPENSES_TOOL,
    ANALYZE_VENDORS_TOOL,
    GET_ACTIVITY_LOGS_TOOL,
    CREATE_ASSET_TOOL,
    DEPRECIATE_ASSET_TOOL,
]


def build_groq_payload(
    message: str,
    context: str = "",
    messages_history: list = None,
    tools: list = None,
    temperature: float = 0.7,
    max_tokens: int = 500,
):
    payload = {
        "model": GROQ_MODEL,
        "messages": [
            {
                "role": "system",
                "content": f"You are Nora, the expert AI assistant for Gaatha Suite. Answer based on live data if provided. {context}"
            },
            *(messages_history if messages_history else [{"role": "user", "content": message}])
        ],
        "temperature": temperature,
        "max_tokens": max_tokens,
        "tools": tools if tools is not None else NORA_TOOLSET,
        "tool_choice": "auto"
    }
    return payload


async def call_groq(
    message: str,
    context: str = "",
    messages_history: list = None,
    tools: list = None,
    temperature: float = 0.7,
    max_tokens: int = 500,
):
    if not GROQ_API_KEY:
        return {"error": "Groq API key not configured."}

    headers = {
        "Authorization": f"Bearer {GROQ_API_KEY}",
        "Content-Type": "application/json"
    }
    payload = build_groq_payload(
        message=message,
        context=context,
        messages_history=messages_history,
        tools=tools,
        temperature=temperature,
        max_tokens=max_tokens,
    )

    async with httpx.AsyncClient() as client:
        response = await client.post(GROQ_URL, headers=headers, json=payload, timeout=10.0)
        if response.status_code != 200:
            raise RuntimeError(f"Groq API error: {response.status_code} {response.text}")
        data = response.json()
        return data["choices"][0]["message"]


def call_groq_sync(
    message: str,
    context: str = "",
    messages_history: list = None,
    tools: list = None,
    temperature: float = 0.7,
    max_tokens: int = 500,
):
    if not GROQ_API_KEY:
        return {"error": "Groq API key not configured."}

    headers = {
        "Authorization": f"Bearer {GROQ_API_KEY}",
        "Content-Type": "application/json"
    }
    payload = build_groq_payload(
        message=message,
        context=context,
        messages_history=messages_history,
        tools=tools,
        temperature=temperature,
        max_tokens=max_tokens,
    )

    with httpx.Client(timeout=10.0) as client:
        response = client.post(GROQ_URL, headers=headers, json=payload)
        if response.status_code != 200:
            raise RuntimeError(f"Groq API error: {response.status_code} {response.text}")
        data = response.json()
        return data["choices"][0]["message"]


async def _create_draft_invoice_in_db(
    db: AsyncSession, 
    org_id: int, 
    customer_name: str, 
    total_amount: Decimal, 
    reference: Optional[str] = None
) -> dict:
    """
    Internal function to create a draft invoice in the database.
    """
    # Find customer by name (simplified, in real app might need more robust lookup)
    customer_result = await db.execute(select(Customer).where(Customer.name == customer_name, Customer.org_id == org_id))
    customer = customer_result.scalar_one_or_none()

    if not customer:
        return {"error": f"Customer '{customer_name}' not found. Please create the customer first."}

    new_invoice = Invoice(org_id=org_id, customer_id=customer.id, total_amount=total_amount, reference=reference, status="draft")
    db.add(new_invoice)
    await db.commit()
    await db.refresh(new_invoice)
    return {"success": f"Draft invoice {new_invoice.id} created for {customer.name} with amount {new_invoice.total_amount}."}

async def _create_customer_in_db(
    db: AsyncSession,
    org_id: int,
    name: str,
    email: Optional[str] = None,
    phone: Optional[str] = None,
    lead_source: Optional[str] = None
) -> dict:
    new_customer = Customer(org_id=org_id, name=name, email=email, phone=phone, lead_source=lead_source)
    db.add(new_customer)
    await db.commit()
    await db.refresh(new_customer)
    return {"success": f"Customer '{name}' created with ID {new_customer.id}."}

async def _update_customer_in_db(
    db: AsyncSession,
    org_id: int,
    current_name: str,
    new_name: Optional[str] = None,
    email: Optional[str] = None,
    phone: Optional[str] = None
) -> dict:
    result = await db.execute(select(Customer).where(Customer.name == current_name, Customer.org_id == org_id))
    customer = result.scalar_one_or_none()
    if not customer:
        return {"error": f"Customer '{current_name}' not found."}
    if new_name: customer.name = new_name
    if email: customer.email = email
    if phone: customer.phone = phone
    await db.commit()
    return {"success": f"Customer '{current_name}' updated successfully."}

async def _create_lead_in_db(db: AsyncSession, org_id: int, name: str, email: str = None, phone: str = None, source: str = "AI Chat") -> dict:
    """
    Helper to persist a new lead generated by Nora AI.
    """
    new_lead = Lead(
        organization_id=org_id,
        name=name,
        contact_email=email,
        source=source,
        status="new"
    )
    db.add(new_lead)
    await db.commit()
    await db.refresh(new_lead)
    return {"success": f"Lead '{name}' has been successfully created."}

async def _get_inventory_from_db(db: AsyncSession, org_id: int, search_query: str) -> dict:
    query = select(Item).where(
        Item.org_id == org_id,
        or_(Item.name.ilike(f"%{search_query}%"), Item.sku.ilike(f"%{search_query}%"))
    )
    result = await db.execute(query)
    items = result.scalars().all()
    if not items:
        return {"error": f"No items found matching '{search_query}'."}
    
    return {"items": [{"name": i.name, "sku": i.sku, "stock": i.current_stock, "price": str(i.unit_price)} for i in items]}

async def _adjust_stock_in_db(
    db: AsyncSession, org_id: int, item_identifier: str, quantity: int, reason: str = "AI Adjustment", warehouse_id: int = 1
) -> dict:
    query = select(Item).where(
        Item.org_id == org_id,
        or_(Item.name == item_identifier, Item.sku == item_identifier)
    )
    result = await db.execute(query)
    item = result.scalar_one_or_none()
    
    if not item:
        return {"error": f"Item '{item_identifier}' not found."}
    
    item.current_stock += quantity
    
    txn = StockTransaction(
        org_id=org_id,
        item_id=item.id,
        warehouse_id=warehouse_id,
        quantity=quantity,
        transaction_type="ADJUSTMENT",
        created_at=func.now()
    )
    db.add(txn)
    await db.commit()
    
    return {"success": f"Stock for '{item.name}' updated. New balance: {item.current_stock}."}

async def _get_dashboard_summary_from_db(db: AsyncSession, org_id: int) -> dict:
    """
    Fetches the current month's dashboard summary data.
    This mirrors the logic in app/routers/dashboard.py get_dashboard_summary.
    """
    from sqlalchemy import func, extract
    from datetime import datetime

    now = datetime.utcnow()
    current_month = now.month
    current_year = now.year

    # 1. Sales Calculation (Invoiced this month)
    sales_query = select(func.sum(Invoice.total_amount)).where(
        Invoice.org_id == org_id,
        extract('month', Invoice.created_at) == current_month,
        extract('year', Invoice.created_at) == current_year
    )
    sales_result = await db.execute(sales_query)
    total_sales = sales_result.scalar() or 0.0

    # 2. Cash Calculation (Paid invoices this month)
    cash_query = select(func.sum(Invoice.total_amount)).where(
        Invoice.org_id == org_id,
        Invoice.status == "paid",
        extract('month', Invoice.created_at) == current_month,
        extract('year', Invoice.created_at) == current_year
    )
    cash_result = await db.execute(cash_query)
    total_cash = cash_result.scalar() or 0.0

    # 3. Low Stock Alerts
    low_stock_query = select(func.count(Item.id)).where(
        Item.org_id == org_id,
        Item.current_stock <= Item.min_stock_level
    )
    low_stock_result = await db.execute(low_stock_query)
    low_stock_count = low_stock_result.scalar() or 0

    return {
        "period": f"{now.strftime('%B %Y')}",
        "sales": float(total_sales),
        "cash_flow": float(total_cash),
        "inventory_alerts": {
            "low_stock_count": low_stock_count
        }
    }

async def _get_expense_analysis_from_db(db: AsyncSession, org_id: int) -> dict:
    """
    Aggregates expenses by category for the organization.
    Note: Uses a generic Expense model assumption based on platform architecture.
    """
    # This assumes an Expense model exists with category and amount
    # Since Expense model isn't in context, we use a dynamic execution approach or 
    # assume standard fields: amount, category, org_id.
    from sqlalchemy import text
    query = text("""
        SELECT category, SUM(amount) as total 
        FROM expenses 
        WHERE org_id = :org_id AND extract(year from created_at) = extract(year from now())
        GROUP BY category 
        ORDER BY total DESC
    """)
    result = await db.execute(query, {"org_id": org_id})
    rows = result.fetchall()
    return {"expense_breakdown": [{"category": r[0], "total": float(r[1])} for r in rows]}

async def _get_vendor_analysis_from_db(db: AsyncSession, org_id: int, limit: int = 5) -> dict:
    """
    Analyzes top vendors by spend volume.
    """
    # Joins Vendors with PurchaseOrders or Expenses to find total spend
    from sqlalchemy import text
    query = text("""
        SELECT v.name, COUNT(po.id) as order_count, SUM(po.total_amount) as total_spend
        FROM vendors v
        JOIN purchase_orders po ON v.id = po.vendor_id
        WHERE v.org_id = :org_id
        GROUP BY v.name
        ORDER BY total_spend DESC
        LIMIT :limit
    """)
    result = await db.execute(query, {"org_id": org_id, "limit": limit})
    rows = result.fetchall()
    return {"top_vendors": [{"vendor": r[0], "orders": r[1], "spend": float(r[2])} for r in rows]}

async def _get_activity_logs_from_db(db: AsyncSession, org_id: int, user_id: Optional[int] = None, limit: int = 10) -> dict:
    """
    Fetches the most recent activity logs.
    """
    from sqlalchemy import text
    query_str = "SELECT user_id, action, path, created_at FROM activity_logs WHERE org_id = :org_id"
    params = {"org_id": org_id, "limit": limit}
    
    if user_id:
        query_str += " AND user_id = :user_id"
        params["user_id"] = user_id
        
    query_str += " ORDER BY created_at DESC LIMIT :limit"
    
    result = await db.execute(text(query_str), params)
    rows = result.fetchall()
    
    return {"logs": [{"user_id": r[0], "action": r[1], "path": r[2], "timestamp": str(r[3])} for r in rows]}