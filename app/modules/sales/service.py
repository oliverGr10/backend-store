"""
Service de ventas.

Flujos:
  - payment_type="cash"   → venta normal al contado
  - payment_type="credit" → fiado: registra venta + crea deuda automáticamente
"""

import uuid
import logging
from datetime import date
from supabase import Client

from app.modules.sales.repository import SaleRepository
from app.modules.sales.schemas import (
    SaleCreate, SaleResponse, SaleItemResponse,
    SaleTodaySummary, SaleFilters,
)
from app.modules.products.repository import ProductRepository
from app.modules.debts.repository import DebtRepository
from app.shared.exceptions import NotFoundError, ValidationError

logger = logging.getLogger("bodega.sales.service")


class SaleService:
    def __init__(self, db: Client):
        self.repo = SaleRepository(db)
        self.product_repo = ProductRepository(db)
        self.debt_repo = DebtRepository(db)

    def _build_item_response(self, item: dict) -> SaleItemResponse:
        price = float(item["price"])
        cost = float(item["cost"])
        qty = int(item["quantity"])
        return SaleItemResponse(
            id=item["id"],
            sale_id=item["sale_id"],
            product_id=item.get("product_id"),
            product_name=item["product_name"],
            quantity=qty,
            price=price,
            cost=cost,
            subtotal=round(price * qty, 2),
            profit=round((price - cost) * qty, 2),
        )

    def _build_sale_response(self, sale: dict, items: list[dict]) -> SaleResponse:
        return SaleResponse(
            id=sale["id"],
            user_id=sale["user_id"],
            total=float(sale["total"]),
            profit=float(sale["profit"]),
            payment_type=sale.get("payment_type", "cash"),
            customer_name=sale.get("customer_name"),
            debt_id=sale.get("debt_id"),
            notes=sale.get("notes"),
            created_at=sale["created_at"],
            items=[self._build_item_response(i) for i in items],
        )

    def create_sale(self, data: SaleCreate, user_id: uuid.UUID) -> SaleResponse:
        """
        Registra una venta:
        1. Verifica stock de cada producto
        2. Calcula total y ganancia
        3. Crea la venta y sus items
        4. Descuenta el stock
        5. Si es fiado → crea el registro de deuda automáticamente
        """
        # ── 1. Verificar productos y calcular totales ──────────────────
        items_data = []
        total = 0.0
        profit = 0.0

        for item in data.items:
            product = self.product_repo.get_by_id(item.product_id, user_id)
            if not product:
                raise NotFoundError(f"Producto {item.product_id}")
            if product["stock"] < item.quantity:
                raise ValidationError(
                    f"Stock insuficiente para '{product['name']}'. "
                    f"Disponible: {product['stock']}, solicitado: {item.quantity}"
                )
            price = float(product["price"])
            cost = float(product["cost"])
            subtotal = round(price * item.quantity, 2)

            total += subtotal
            profit += round((price - cost) * item.quantity, 2)

            items_data.append({
                "product_id": str(item.product_id),
                "product_name": product["name"],
                "quantity": item.quantity,
                "price": price,
                "cost": cost,
                "_product": product,
            })

        total = round(total, 2)
        profit = round(profit, 2)

        # ── 2. Crear la venta ──────────────────────────────────────────
        sale = self.repo.create_sale(
            user_id=user_id,
            total=total,
            profit=profit,
            notes=data.notes,
            payment_type=data.payment_type,
            customer_name=data.customer_name,
        )

        # ── 3. Crear los items ─────────────────────────────────────────
        items_payload = [
            {
                "sale_id": sale["id"],
                "product_id": d["product_id"],
                "product_name": d["product_name"],
                "quantity": d["quantity"],
                "price": d["price"],
                "cost": d["cost"],
            }
            for d in items_data
        ]
        created_items = self.repo.create_sale_items(items_payload)

        # ── 4. Descontar stock ─────────────────────────────────────────
        for d in items_data:
            self.product_repo.adjust_stock(d["_product"], -d["quantity"])
            logger.debug(f"Stock -{d['quantity']} → {d['product_name']}")

        # ── 5. Si es fiado → crear deuda automáticamente ──────────────
        if data.payment_type == "credit":
            note = data.notes or f"Venta del {date.today().isoformat()}"
            debt = self.debt_repo.create(
                user_id=user_id,
                customer_name=data.customer_name,
                amount=total,
                note=note,
                sale_id=sale["id"],
            )
            # Vincular el debt_id en la venta
            sale = self.repo.update_debt_id(sale["id"], debt["id"])
            logger.info(f"Fiado creado: {data.customer_name} debe S/ {total}")

        return self._build_sale_response(sale, created_items)

    def get_sale(self, sale_id: uuid.UUID, user_id: uuid.UUID) -> SaleResponse:
        sale = self.repo.get_by_id(sale_id, user_id)
        if not sale:
            raise NotFoundError("Venta")
        items = self.repo.get_items_by_sale(sale_id)
        return self._build_sale_response(sale, items)

    def list_sales(self, user_id: uuid.UUID, filters: SaleFilters) -> tuple[list[SaleResponse], int]:
        sales, total = self.repo.get_all(user_id, filters)
        responses = []
        for sale in sales:
            items = self.repo.get_items_by_sale(uuid.UUID(sale["id"]))
            responses.append(self._build_sale_response(sale, items))
        return responses, total

    def get_today_summary(self, user_id: uuid.UUID) -> SaleTodaySummary:
        today_str = date.today().isoformat()
        sales = self.repo.get_today_sales(user_id, today_str)

        cash = [s for s in sales if s.get("payment_type", "cash") == "cash"]
        credit = [s for s in sales if s.get("payment_type") == "credit"]

        total_items = sum(
            sum(int(i["quantity"]) for i in s.get("sale_items", []))
            for s in sales
        )

        return SaleTodaySummary(
            total_sales=len(sales),
            cash_sales=len(cash),
            credit_sales=len(credit),
            total_revenue=round(sum(float(s["total"]) for s in sales), 2),
            cash_revenue=round(sum(float(s["total"]) for s in cash), 2),
            credit_revenue=round(sum(float(s["total"]) for s in credit), 2),
            total_profit=round(sum(float(s["profit"]) for s in sales), 2),
            total_items_sold=total_items,
        )
