"""Schemas Pydantic para el módulo de ventas."""

import uuid
from datetime import datetime
from typing import Optional, Literal
from pydantic import BaseModel, Field, model_validator


# ── REQUEST ────────────────────────────────────────────────────────────────

class SaleItemCreate(BaseModel):
    """Un producto dentro de una venta."""
    product_id: uuid.UUID
    quantity: int = Field(..., gt=0, description="Cantidad vendida")


class SaleCreate(BaseModel):
    """
    Body para registrar una venta.

    payment_type:
      - "cash"   → pago al contado (default)
      - "credit" → fiado: requiere customer_name, crea deuda automáticamente
    """
    items: list[SaleItemCreate] = Field(..., min_length=1)
    payment_type: Literal["cash", "credit"] = Field(
        default="cash",
        description="'cash' = pago ahora | 'credit' = fiado (paga después)",
    )
    customer_name: Optional[str] = Field(
        None,
        min_length=2,
        max_length=200,
        description="Requerido si payment_type = 'credit'",
    )
    notes: Optional[str] = Field(None, max_length=500)

    @model_validator(mode="after")
    def customer_required_for_credit(self):
        if self.payment_type == "credit" and not self.customer_name:
            raise ValueError(
                "customer_name es requerido cuando payment_type es 'credit'"
            )
        return self

    @model_validator(mode="after")
    def no_duplicate_products(self):
        ids = [str(i.product_id) for i in self.items]
        if len(ids) != len(set(ids)):
            raise ValueError("No puedes repetir el mismo producto en una venta")
        return self


# ── RESPONSE ───────────────────────────────────────────────────────────────

class SaleItemResponse(BaseModel):
    id: uuid.UUID
    sale_id: uuid.UUID
    product_id: Optional[uuid.UUID]
    product_name: str
    quantity: int
    price: float
    cost: float
    subtotal: float     # price * quantity
    profit: float       # (price - cost) * quantity


class SaleResponse(BaseModel):
    id: uuid.UUID
    user_id: uuid.UUID
    total: float
    profit: float
    payment_type: str           # "cash" | "credit"
    customer_name: Optional[str] = None   # solo si es fiado
    debt_id: Optional[uuid.UUID] = None   # ID del fiado creado (si aplica)
    notes: Optional[str]
    created_at: datetime
    items: list[SaleItemResponse] = []


class SaleTodaySummary(BaseModel):
    """Resumen de ventas del día."""
    total_sales: int
    cash_sales: int             # ventas al contado
    credit_sales: int           # ventas fiadas
    total_revenue: float        # ingresos totales
    cash_revenue: float         # ingresos cobrados
    credit_revenue: float       # pendiente de cobro (fiados)
    total_profit: float
    total_items_sold: int


# ── FILTROS ────────────────────────────────────────────────────────────────

class SaleFilters(BaseModel):
    date_from: Optional[str] = None
    date_to: Optional[str] = None
    payment_type: Optional[Literal["cash", "credit"]] = None
    min_total: Optional[float] = None
    page: int = Field(default=1, ge=1)
    per_page: int = Field(default=20, ge=1, le=100)
