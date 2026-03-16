from datetime import datetime
from typing import Iterable

from database.db import db
from database.models import Bill, BillItem


def create_bill(business_id: int, table_no: str, items: Iterable[dict], gst_rate: float = 0.0):
    bill = Bill(business_id=business_id, table_no=table_no, status="PENDING")
    db.session.add(bill)
    db.session.flush()

    subtotal = 0.0
    for item in items:
        name = item.get("product_name")
        quantity = int(item.get("quantity", 1))
        price = float(item.get("price", 0.0))
        if not name or quantity <= 0 or price < 0:
            continue
        subtotal += price * quantity
        db.session.add(
            BillItem(
                bill_id=bill.id,
                product_name=name,
                price=price,
                quantity=quantity,
            )
        )

    total = subtotal + (subtotal * gst_rate) / 100 if gst_rate else subtotal
    bill.total = total
    db.session.commit()
    return bill


def complete_bill(bill: Bill):
    bill.status = "COMPLETED"
    bill.completed_at = datetime.utcnow()
    db.session.commit()
    return bill


def update_bill(bill: Bill, items: list[dict], gst_rate: float = 0.0):
    """Replace bill items and recalculate total."""
    for existing in list(bill.items):
        db.session.delete(existing)
    db.session.flush()

    subtotal = 0.0
    for item in items:
        name = item.get("product_name")
        quantity = int(item.get("quantity", 1))
        price = float(item.get("price", 0.0))
        if not name or quantity <= 0 or price < 0:
            continue
        subtotal += price * quantity
        db.session.add(
            BillItem(
                bill_id=bill.id,
                product_name=name,
                price=price,
                quantity=quantity,
            )
        )

    total = subtotal + (subtotal * gst_rate) / 100 if gst_rate else subtotal
    bill.total = total
    db.session.commit()
    return bill

