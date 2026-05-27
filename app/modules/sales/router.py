"""Router de ventas."""

import uuid
from typing import Optional
from fastapi import APIRouter, Depends, Query, status

from app.database import get_supabase_client
from app.modules.sales.service import SaleService
from app.modules.sales.schemas import SaleCreate, SaleFilters
from app.modules.auth.dependencies import get_current_user
from app.shared.responses import success, paginated

router = APIRouter(prefix="/sales", tags=["Ventas"])


def get_service() -> SaleService:
    return SaleService(get_supabase_client())


@router.post("/", summary="Registrar venta", response_model=dict, status_code=status.HTTP_201_CREATED)
def create_sale(
    body: SaleCreate,
    service: SaleService = Depends(get_service),
    user_id: uuid.UUID = Depends(get_current_user),
):
    sale = service.create_sale(body, user_id)
    return success(sale.model_dump())


@router.get("/today", summary="Resumen del día", response_model=dict)
def get_today_summary(
    service: SaleService = Depends(get_service),
    user_id: uuid.UUID = Depends(get_current_user),
):
    summary = service.get_today_summary(user_id)
    return success(summary.model_dump())


@router.get("/", summary="Historial de ventas", response_model=dict)
def list_sales(
    date_from: Optional[str] = Query(None),
    date_to: Optional[str] = Query(None),
    payment_type: Optional[str] = Query(None),
    min_total: Optional[float] = Query(None),
    page: int = Query(1, ge=1),
    per_page: int = Query(20, ge=1, le=100),
    service: SaleService = Depends(get_service),
    user_id: uuid.UUID = Depends(get_current_user),
):
    filters = SaleFilters(date_from=date_from, date_to=date_to,
                          payment_type=payment_type, min_total=min_total,
                          page=page, per_page=per_page)
    sales, total = service.list_sales(user_id, filters)
    return paginated([s.model_dump() for s in sales], total, page, per_page)


@router.get("/{sale_id}", summary="Detalle de venta", response_model=dict)
def get_sale(
    sale_id: uuid.UUID,
    service: SaleService = Depends(get_service),
    user_id: uuid.UUID = Depends(get_current_user),
):
    sale = service.get_sale(sale_id, user_id)
    return success(sale.model_dump())
