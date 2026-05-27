"""Router de productos."""

import uuid
import logging
import traceback
from typing import Optional
from fastapi import APIRouter, Depends, Query, status

from app.database import get_supabase_client
from app.modules.products.service import ProductService
from app.modules.products.schemas import (
    ProductCreate, ProductUpdate, ProductFilters, StockAdjust,
)
from app.modules.auth.dependencies import get_current_user
from app.shared.responses import success, paginated

logger = logging.getLogger("bodega.products")
router = APIRouter(prefix="/products", tags=["Productos"])


def get_service() -> ProductService:
    return ProductService(get_supabase_client())


@router.get("/", summary="Listar productos", response_model=dict)
def list_products(
    category: Optional[str] = Query(None),
    low_stock: Optional[bool] = Query(None),
    search: Optional[str] = Query(None),
    page: int = Query(1, ge=1),
    per_page: int = Query(20, ge=1, le=100),
    service: ProductService = Depends(get_service),
    user_id: uuid.UUID = Depends(get_current_user),
):
    filters = ProductFilters(category=category, low_stock=low_stock,
                             search=search, page=page, per_page=per_page)
    products, total = service.list_products(user_id, filters)
    return paginated([p.model_dump() for p in products], total, page, per_page)


@router.post("/", summary="Crear producto", response_model=dict, status_code=status.HTTP_201_CREATED)
def create_product(
    body: ProductCreate,
    service: ProductService = Depends(get_service),
    user_id: uuid.UUID = Depends(get_current_user),
):
    logger.info(f"➕ Creando producto: {body.name}")
    try:
        product = service.create_product(body, user_id)
        return success(product.model_dump())
    except Exception as e:
        logger.error(f"❌ {e}\n{traceback.format_exc()}")
        raise


@router.get("/low-stock", summary="Stock bajo", response_model=dict)
def get_low_stock_products(
    service: ProductService = Depends(get_service),
    user_id: uuid.UUID = Depends(get_current_user),
):
    products = service.get_low_stock_products(user_id)
    return success([p.model_dump() for p in products])


@router.get("/{product_id}", summary="Detalle de producto", response_model=dict)
def get_product(
    product_id: uuid.UUID,
    service: ProductService = Depends(get_service),
    user_id: uuid.UUID = Depends(get_current_user),
):
    product = service.get_product(product_id, user_id)
    return success(product.model_dump())


@router.put("/{product_id}", summary="Actualizar producto", response_model=dict)
def update_product(
    product_id: uuid.UUID,
    body: ProductUpdate,
    service: ProductService = Depends(get_service),
    user_id: uuid.UUID = Depends(get_current_user),
):
    product = service.update_product(product_id, body, user_id)
    return success(product.model_dump())


@router.delete("/{product_id}", summary="Desactivar producto", response_model=dict)
def delete_product(
    product_id: uuid.UUID,
    service: ProductService = Depends(get_service),
    user_id: uuid.UUID = Depends(get_current_user),
):
    result = service.delete_product(product_id, user_id)
    return success(result)


@router.patch("/{product_id}/stock", summary="Ajustar stock", response_model=dict)
def adjust_stock(
    product_id: uuid.UUID,
    body: StockAdjust,
    service: ProductService = Depends(get_service),
    user_id: uuid.UUID = Depends(get_current_user),
):
    product = service.adjust_stock(product_id, body, user_id)
    return success(product.model_dump())
