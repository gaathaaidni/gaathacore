from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.models.purchase_order import PurchaseOrder
from app.models.inventory import Item, StockTransaction, GoodsReceivedNote
from fastapi import HTTPException

class ProcurementService:
    @staticmethod
    async def process_grn(db: AsyncSession, po_id: int, org_id: int, user_id: int, notes: str = None):
        """
        Converts a Purchase Order into stock additions via a GRN.
        """
        # 1. Fetch PO with line items
        result = await db.execute(
            select(PurchaseOrder).where(PurchaseOrder.id == po_id, PurchaseOrder.org_id == org_id)
        )
        po = result.scalar_one_or_none()

        if not po or po.status != "ordered":
            raise HTTPException(status_code=400, detail="PO must be in 'ordered' status to receive goods")

        # 2. Create GRN record
        grn = GoodsReceivedNote(
            org_id=org_id,
            purchase_order_id=po_id,
            received_by_id=user_id,
            notes=notes
        )
        db.add(grn)

        # 3. Update Item stocks and create transactions
        for line in po.lines:
            item_result = await db.execute(select(Item).where(Item.id == line.item_id))
            item = item_result.scalar_one_or_none()
            
            if item:
                item.current_stock += line.quantity
                txn = StockTransaction(
                    org_id=org_id, item_id=item.id, warehouse_id=1, quantity=line.quantity, transaction_type="PURCHASE"
                )
                db.add(txn)

        po.status = "received"
        await db.commit()
        return {"status": "success", "grn_id": grn.id}