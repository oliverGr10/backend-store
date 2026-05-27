"""Service de fiados — solo deudas manuales.
Para fiados de ventas → SaleService con payment_type='credit'.
"""

import uuid
import logging
from supabase import Client

from app.modules.debts.repository import DebtRepository
from app.modules.debts.schemas import (
    DebtCreate, DebtResponse, DebtItemResponse,
    DebtFilters, DebtSummary,
)
from app.modules.sales.repository import SaleRepository
from app.shared.exceptions import NotFoundError, ValidationError

logger = logging.getLogger("bodega.debts.service")


class DebtService:
    def __init__(self, db: Client):
        self.repo = DebtRepository(db)
        self.sale_repo = SaleRepository(db)

    def _to_response(self, d: dict, items: list[dict] = []) -> DebtResponse:
        return DebtResponse(
            id=d["id"],
            user_id=d["user_id"],
            customer_name=d["customer_name"],
            amount=float(d["amount"]),
            paid=d["paid"],
            paid_at=d.get("paid_at"),
            note=d.get("note"),
            created_at=d["created_at"],
            sale_id=d.get("sale_id"),
            items=[
                DebtItemResponse(
                    product_name=i["product_name"],
                    quantity=i["quantity"],
                    price=float(i["price"]),
                    subtotal=round(float(i["price"]) * i["quantity"], 2),
                )
                for i in items
            ],
        )

    def create_debt(self, data: DebtCreate, user_id: uuid.UUID) -> DebtResponse:
        """Registra deuda manual (sin productos, sin afectar stock)."""
        debt = self.repo.create(user_id, data.customer_name, data.amount, data.note)
        return self._to_response(debt)

    def list_debts(self, user_id: uuid.UUID, filters: DebtFilters) -> tuple[list[DebtResponse], int]:
        debts, total = self.repo.get_all(user_id, filters)
        result = []
        for d in debts:
            items = []
            if d.get("sale_id"):
                items = self.sale_repo.get_items_by_sale(uuid.UUID(d["sale_id"]))
            result.append(self._to_response(d, items))
        return result, total

    def mark_as_paid(self, debt_id: uuid.UUID, user_id: uuid.UUID) -> DebtResponse:
        debt = self.repo.get_by_id(debt_id, user_id)
        if not debt:
            raise NotFoundError("Fiado")
        if debt["paid"]:
            raise ValidationError("Este fiado ya fue marcado como pagado")
        updated = self.repo.mark_as_paid(debt_id)
        items = []
        if updated.get("sale_id"):
            items = self.sale_repo.get_items_by_sale(uuid.UUID(updated["sale_id"]))
        return self._to_response(updated, items)

    def delete_debt(self, debt_id: uuid.UUID, user_id: uuid.UUID) -> dict:
        debt = self.repo.get_by_id(debt_id, user_id)
        if not debt:
            raise NotFoundError("Fiado")
        self.repo.delete(debt_id)
        return {"message": f"Fiado de '{debt['customer_name']}' eliminado"}

    def get_summary(self, user_id: uuid.UUID) -> DebtSummary:
        return DebtSummary(**self.repo.get_summary(user_id))
