"""Router de fiados."""

import uuid
from typing import Optional
from fastapi import APIRouter, Depends, Query, status

from app.database import get_supabase_client
from app.modules.debts.service import DebtService
from app.modules.debts.schemas import DebtCreate, DebtFilters
from app.modules.auth.dependencies import get_current_user
from app.shared.responses import success, paginated

router = APIRouter(prefix="/debts", tags=["Fiados"])


def get_service() -> DebtService:
    return DebtService(get_supabase_client())


@router.get("/summary", summary="Resumen de fiados", response_model=dict)
def get_summary(
    service: DebtService = Depends(get_service),
    user_id: uuid.UUID = Depends(get_current_user),
):
    summary = service.get_summary(user_id)
    return success(summary.model_dump())


@router.get("/", summary="Listar fiados", response_model=dict)
def list_debts(
    paid: Optional[bool] = Query(None),
    customer_name: Optional[str] = Query(None),
    page: int = Query(1, ge=1),
    per_page: int = Query(20, ge=1, le=100),
    service: DebtService = Depends(get_service),
    user_id: uuid.UUID = Depends(get_current_user),
):
    filters = DebtFilters(paid=paid, customer_name=customer_name,
                          page=page, per_page=per_page)
    debts, total = service.list_debts(user_id, filters)
    return paginated([d.model_dump() for d in debts], total, page, per_page)


@router.post("/", summary="Registrar fiado manual", response_model=dict, status_code=status.HTTP_201_CREATED)
def create_debt(
    body: DebtCreate,
    service: DebtService = Depends(get_service),
    user_id: uuid.UUID = Depends(get_current_user),
):
    """Para deudas que ya existían. Para fiados de venta → POST /sales con payment_type='credit'."""
    debt = service.create_debt(body, user_id)
    return success(debt.model_dump())


@router.patch("/{debt_id}/pay", summary="Marcar como pagado", response_model=dict)
def mark_as_paid(
    debt_id: uuid.UUID,
    service: DebtService = Depends(get_service),
    user_id: uuid.UUID = Depends(get_current_user),
):
    debt = service.mark_as_paid(debt_id, user_id)
    return success(debt.model_dump())


@router.delete("/{debt_id}", summary="Eliminar fiado", response_model=dict)
def delete_debt(
    debt_id: uuid.UUID,
    service: DebtService = Depends(get_service),
    user_id: uuid.UUID = Depends(get_current_user),
):
    result = service.delete_debt(debt_id, user_id)
    return success(result)
