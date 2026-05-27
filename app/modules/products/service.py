"""
Service de productos: lógica de negocio de BodegaApp.
Usa ProductRepository (Supabase client) y retorna schemas Pydantic.
"""

import uuid
from supabase import Client

from app.modules.products.repository import ProductRepository
from app.modules.products.schemas import (
    ProductCreate,
    ProductUpdate,
    ProductFilters,
    StockAdjust,
    ProductResponse,
)
from app.shared.exceptions import NotFoundError, ConflictError, ValidationError


class ProductService:
    """Lógica de negocio del módulo de productos."""

    def __init__(self, db: Client):
        self.repo = ProductRepository(db)

    def _to_response(self, data: dict) -> ProductResponse:
        """Convierte un dict de Supabase a un schema de respuesta."""
        price = float(data["price"])
        cost = float(data["cost"])
        stock = int(data["stock"])
        min_stock = int(data["min_stock"])

        return ProductResponse(
            id=data["id"],
            user_id=data["user_id"],
            name=data["name"],
            price=price,
            cost=cost,
            stock=stock,
            min_stock=min_stock,
            category=data["category"],
            unit=data["unit"],
            is_active=data["is_active"],
            created_at=data["created_at"],
            updated_at=data["updated_at"],
            is_low_stock=stock <= min_stock,
            margin=round(price - cost, 2),
        )

    def list_products(
        self,
        user_id: uuid.UUID,
        filters: ProductFilters,
    ) -> tuple[list[ProductResponse], int]:
        products, total = self.repo.get_all(user_id, filters)
        return [self._to_response(p) for p in products], total

    def get_product(
        self,
        product_id: uuid.UUID,
        user_id: uuid.UUID,
    ) -> ProductResponse:
        product = self.repo.get_by_id(product_id, user_id)
        if not product:
            raise NotFoundError("Producto")
        return self._to_response(product)

    def create_product(
        self,
        data: ProductCreate,
        user_id: uuid.UUID,
    ) -> ProductResponse:
        # Nombre único por bodega
        if self.repo.exists_by_name(data.name, user_id):
            raise ConflictError(
                f"Ya existe un producto activo con el nombre '{data.name}'"
            )
        # Costo no puede superar el precio
        if data.cost > data.price:
            raise ValidationError(
                f"El costo ({data.cost}) no puede ser mayor al precio ({data.price})"
            )
        product = self.repo.create(data, user_id)
        return self._to_response(product)

    def update_product(
        self,
        product_id: uuid.UUID,
        data: ProductUpdate,
        user_id: uuid.UUID,
    ) -> ProductResponse:
        product = self.repo.get_by_id(product_id, user_id)
        if not product:
            raise NotFoundError("Producto")

        if data.name and data.name != product["name"]:
            if self.repo.exists_by_name(data.name, user_id, exclude_id=product_id):
                raise ConflictError(
                    f"Ya existe un producto con el nombre '{data.name}'"
                )

        new_price = data.price if data.price is not None else float(product["price"])
        new_cost = data.cost if data.cost is not None else float(product["cost"])
        if new_cost > new_price:
            raise ValidationError(
                f"El costo ({new_cost}) no puede ser mayor al precio ({new_price})"
            )

        updated = self.repo.update(product_id, data)
        return self._to_response(updated)

    def delete_product(
        self,
        product_id: uuid.UUID,
        user_id: uuid.UUID,
    ) -> dict:
        product = self.repo.get_by_id(product_id, user_id)
        if not product:
            raise NotFoundError("Producto")
        self.repo.soft_delete(product_id)
        return {"message": f"Producto '{product['name']}' desactivado correctamente"}

    def adjust_stock(
        self,
        product_id: uuid.UUID,
        data: StockAdjust,
        user_id: uuid.UUID,
    ) -> ProductResponse:
        product = self.repo.get_by_id(product_id, user_id)
        if not product:
            raise NotFoundError("Producto")
        try:
            updated = self.repo.adjust_stock(product, data.quantity)
        except ValueError as e:
            raise ValidationError(str(e))
        return self._to_response(updated)

    def get_low_stock_products(
        self,
        user_id: uuid.UUID,
    ) -> list[ProductResponse]:
        products = self.repo.get_low_stock(user_id)
        return [self._to_response(p) for p in products]
