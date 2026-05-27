"""Schemas Pydantic para el módulo de fiados."""

import uuid
from datetime import datetime
from typing import Optional
from pydantic import BaseModel, Field


class DebtCreate(BaseModel):
    """
    Registra una deuda manual (que ya existía antes, no viene de una venta).
    Para fiados de productos vendidos ahora → usar POST /sales con payment_type='credit'.
    """
    customer_name: str = Field(..., min_length=2, max_length=200)
    amount: float = Field(..., gt=0, description="Monto de la deuda")
    note: Optional[str] = Field(None, max_length=500,
                                description='Ej: "debe 20 soles de la semana pasada"')


class DebtItemResponse(BaseModel):
    """Producto registrado en el fiado (cuando viene de una venta)."""
    product_name: str
    quantity: int
    price: float
    subtotal: float


class DebtResponse(BaseModel):
    id: uuid.UUID
    user_id: uuid.UUID
    customer_name: str
    amount: float
    paid: bool
    paid_at: Optional[datetime]
    note: Optional[str]
    created_at: datetime
    sale_id: Optional[uuid.UUID] = None    # si vino de una venta
    items: list[DebtItemResponse] = []     # productos que se llevó


class DebtFilters(BaseModel):
    paid: Optional[bool] = None
    customer_name: Optional[str] = None
    page: int = Field(default=1, ge=1)
    per_page: int = Field(default=20, ge=1, le=100)


class DebtSummary(BaseModel):
    total_debts: int
    total_pending: int
    total_amount_pending: float
    total_amount_paid: float
