"""
Repository de productos usando el cliente Supabase (PostgREST sobre HTTPS).
Evita conexión directa a PostgreSQL — funciona en cualquier red IPv4.
"""

import uuid
import logging
from typing import Optional
from supabase import Client

from app.modules.products.schemas import ProductCreate, ProductUpdate, ProductFilters

logger = logging.getLogger("bodega.repository")
TABLE = "products"


class ProductRepository:
    def __init__(self, db: Client):
        self.db = db

    def get_by_id(self, product_id: uuid.UUID, user_id: uuid.UUID) -> Optional[dict]:
        logger.debug(f"get_by_id: product={product_id} user={user_id}")
        try:
            result = (
                self.db.table(TABLE)
                .select("*")
                .eq("id", str(product_id))
                .eq("user_id", str(user_id))
                .eq("is_active", True)
                .single()
                .execute()
            )
            logger.debug(f"get_by_id result: {result.data}")
            return result.data
        except Exception as e:
            logger.error(f"get_by_id error: {e}")
            return None

    def get_all(self, user_id: uuid.UUID, filters: ProductFilters) -> tuple[list[dict], int]:
        logger.debug(f"get_all: user={user_id} filters={filters}")
        query = (
            self.db.table(TABLE)
            .select("*", count="exact")
            .eq("user_id", str(user_id))
        )
        if filters.is_active is not None:
            query = query.eq("is_active", filters.is_active)
        if filters.category:
            query = query.eq("category", filters.category.lower())
        if filters.search:
            query = query.ilike("name", f"%{filters.search}%")

        offset = (filters.page - 1) * filters.per_page
        query = query.order("name").range(offset, offset + filters.per_page - 1)

        result = query.execute()
        products = result.data or []
        total = result.count or 0

        if filters.low_stock:
            products = [p for p in products if p["stock"] <= p["min_stock"]]
            total = len(products)

        return products, total

    def create(self, data: ProductCreate, user_id: uuid.UUID) -> dict:
        payload = {
            "user_id": str(user_id),
            "name": data.name.strip(),
            "price": data.price,
            "cost": data.cost,
            "stock": data.stock,
            "min_stock": data.min_stock,
            "category": data.category,
            "unit": data.unit,
            "is_active": True,
        }
        logger.debug(f"INSERT products payload: {payload}")
        result = self.db.table(TABLE).insert(payload).execute()
        logger.debug(f"INSERT result: {result}")
        return result.data[0]

    def update(self, product_id: uuid.UUID, data: ProductUpdate) -> dict:
        update_data = data.model_dump(exclude_unset=True, exclude_none=True)
        logger.debug(f"UPDATE product {product_id}: {update_data}")
        result = (
            self.db.table(TABLE)
            .update(update_data)
            .eq("id", str(product_id))
            .execute()
        )
        return result.data[0]

    def soft_delete(self, product_id: uuid.UUID) -> dict:
        logger.debug(f"SOFT DELETE product {product_id}")
        result = (
            self.db.table(TABLE)
            .update({"is_active": False})
            .eq("id", str(product_id))
            .execute()
        )
        return result.data[0]

    def adjust_stock(self, product: dict, quantity_delta: int) -> dict:
        new_stock = product["stock"] + quantity_delta
        if new_stock < 0:
            raise ValueError(
                f"Stock insuficiente. Disponible: {product['stock']}, "
                f"ajuste solicitado: {quantity_delta}"
            )
        logger.debug(f"STOCK product {product['id']}: {product['stock']} → {new_stock}")
        result = (
            self.db.table(TABLE)
            .update({"stock": new_stock})
            .eq("id", product["id"])
            .execute()
        )
        return result.data[0]

    def get_low_stock(self, user_id: uuid.UUID) -> list[dict]:
        result = (
            self.db.table(TABLE)
            .select("*")
            .eq("user_id", str(user_id))
            .eq("is_active", True)
            .execute()
        )
        products = result.data or []
        low = [p for p in products if p["stock"] <= p["min_stock"]]
        return sorted(low, key=lambda p: p["stock"])

    def exists_by_name(
        self,
        name: str,
        user_id: uuid.UUID,
        exclude_id: Optional[uuid.UUID] = None,
    ) -> bool:
        logger.debug(f"exists_by_name: '{name}' user={user_id}")
        query = (
            self.db.table(TABLE)
            .select("id")
            .eq("user_id", str(user_id))
            .eq("is_active", True)
            .ilike("name", name.strip())
        )
        if exclude_id:
            query = query.neq("id", str(exclude_id))
        result = query.execute()
        logger.debug(f"exists_by_name result: {result.data}")
        return len(result.data or []) > 0
