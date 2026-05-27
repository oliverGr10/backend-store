"""Repository de ventas — Supabase client."""

import uuid
import logging
from typing import Optional
from supabase import Client

logger = logging.getLogger("bodega.sales.repo")
SALES_TABLE = "sales"
ITEMS_TABLE = "sale_items"


class SaleRepository:
    def __init__(self, db: Client):
        self.db = db

    def create_sale(
        self,
        user_id: uuid.UUID,
        total: float,
        profit: float,
        notes: Optional[str],
        payment_type: str = "cash",
        customer_name: Optional[str] = None,
    ) -> dict:
        payload = {
            "user_id": str(user_id),
            "total": total,
            "profit": profit,
            "notes": notes,
            "payment_type": payment_type,
            "customer_name": customer_name,
        }
        result = self.db.table(SALES_TABLE).insert(payload).execute()
        logger.debug(f"Sale created: {result.data[0]['id']} [{payment_type}]")
        return result.data[0]

    def create_sale_items(self, items: list[dict]) -> list[dict]:
        result = self.db.table(ITEMS_TABLE).insert(items).execute()
        return result.data

    def update_debt_id(self, sale_id: str, debt_id: str) -> dict:
        """Vincula el debt_id a la venta después de crear el fiado."""
        result = (
            self.db.table(SALES_TABLE)
            .update({"debt_id": debt_id})
            .eq("id", sale_id)
            .execute()
        )
        return result.data[0]

    def get_by_id(self, sale_id: uuid.UUID, user_id: uuid.UUID) -> Optional[dict]:
        try:
            result = (
                self.db.table(SALES_TABLE)
                .select("*")
                .eq("id", str(sale_id))
                .eq("user_id", str(user_id))
                .single()
                .execute()
            )
            return result.data
        except Exception:
            return None

    def get_items_by_sale(self, sale_id: uuid.UUID) -> list[dict]:
        result = (
            self.db.table(ITEMS_TABLE)
            .select("*")
            .eq("sale_id", str(sale_id))
            .execute()
        )
        return result.data or []

    def get_all(self, user_id: uuid.UUID, filters) -> tuple[list[dict], int]:
        query = (
            self.db.table(SALES_TABLE)
            .select("*", count="exact")
            .eq("user_id", str(user_id))
            .order("created_at", desc=True)
        )
        if filters.date_from:
            query = query.gte("created_at", filters.date_from)
        if filters.date_to:
            query = query.lte("created_at", filters.date_to + "T23:59:59")
        if filters.payment_type:
            query = query.eq("payment_type", filters.payment_type)
        if filters.min_total:
            query = query.gte("total", filters.min_total)

        offset = (filters.page - 1) * filters.per_page
        query = query.range(offset, offset + filters.per_page - 1)

        result = query.execute()
        return result.data or [], result.count or 0

    def get_today_sales(self, user_id: uuid.UUID, today_str: str) -> list[dict]:
        result = (
            self.db.table(SALES_TABLE)
            .select("*, sale_items(*)")
            .eq("user_id", str(user_id))
            .gte("created_at", today_str + "T00:00:00")
            .lte("created_at", today_str + "T23:59:59")
            .execute()
        )
        return result.data or []
