from pydantic import BaseModel
from typing import Dict

class KPISummary(BaseModel):
    total_sales: float
    paid_invoices_sum: float
    low_stock_count: int
    expense_breakdown: Dict[str, float]
    pending_approvals_count: int