"""Repository de fiados — Supabase client."""

import uuid
import logging
from typing import Optional
from supabase import Client

logger = logging.getLogger("bodega.debts.repo")
TABLE = "debts"


class DebtRepository:
    def __init__(self, db: Client):
        self.db = db

    def create(self, user_id: uuid.UUID, customer_name: str,
               amount: float, note: Optional[str],
               sale_id: Optional[str] = None) -> dict:
        payload = {
            "user_id": str(user_id),
            "customer_name": customer_name.strip(),
            "amount": amount,
            "note": note,
            "paid": False,
        }
        if sale_id:
            payload["sale_id"] = sale_id
        result = self.db.table(TABLE).insert(payload).execute()
        return result.data[0]

    def get_by_id(self, debt_id: uuid.UUID, user_id: uuid.UUID) -> Optional[dict]:
        try:
            result = (
                self.db.table(TABLE)
                .select("*")
                .eq("id", str(debt_id))
                .eq("user_id", str(user_id))
                .single()
                .execute()
            )
            return result.data
        except Exception:
            return None

    def get_all(self, user_id: uuid.UUID, filters) -> tuple[list[dict], int]:
        query = (
            self.db.table(TABLE)
            .select("*", count="exact")
            .eq("user_id", str(user_id))
            .order("created_at", desc=True)
        )
        if filters.paid is not None:
            query = query.eq("paid", filters.paid)
        if filters.customer_name:
            query = query.ilike("customer_name", f"%{filters.customer_name}%")

        offset = (filters.page - 1) * filters.per_page
        query = query.range(offset, offset + filters.per_page - 1)

        result = query.execute()
        return result.data or [], result.count or 0

    def mark_as_paid(self, debt_id: uuid.UUID) -> dict:
        from datetime import datetime, timezone
        result = (
            self.db.table(TABLE)
            .update({"paid": True, "paid_at": datetime.now(timezone.utc).isoformat()})
            .eq("id", str(debt_id))
            .execute()
        )
        return result.data[0]

    def delete(self, debt_id: uuid.UUID) -> None:
        self.db.table(TABLE).delete().eq("id", str(debt_id)).execute()

    def get_summary(self, user_id: uuid.UUID) -> dict:
        result = (
            self.db.table(TABLE)
            .select("amount, paid")
            .eq("user_id", str(user_id))
            .execute()
        )
        debts = result.data or []
        pending = [d for d in debts if not d["paid"]]
        paid = [d for d in debts if d["paid"]]
        return {
            "total_debts": len(debts),
            "total_pending": len(pending),
            "total_amount_pending": round(sum(float(d["amount"]) for d in pending), 2),
            "total_amount_paid": round(sum(float(d["amount"]) for d in paid), 2),
        }
