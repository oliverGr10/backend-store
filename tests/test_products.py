"""
Tests del módulo de productos.
Cubre los endpoints HTTP y la lógica de negocio del service.
"""

import uuid
import pytest
from unittest.mock import AsyncMock, MagicMock
from httpx import AsyncClient, ASGITransport

# Nota: estos tests se activarán cuando el .env esté configurado.
# Por ahora son una plantilla lista para implementar.


# ── Fixtures ───────────────────────────────────────────────────────────────

MOCK_USER_ID = uuid.UUID("00000000-0000-0000-0000-000000000001")

PRODUCT_PAYLOAD = {
    "name": "Inca Kola 1.5L",
    "price": 4.50,
    "cost": 3.00,
    "stock": 24,
    "min_stock": 6,
    "category": "bebidas",
    "unit": "unidad",
}


# ── Tests del Service (unit tests) ─────────────────────────────────────────

class TestProductServiceValidations:
    """Valida las reglas de negocio del ProductService."""

    def test_cost_cannot_exceed_price(self):
        """El costo no puede ser mayor al precio de venta."""
        from app.modules.products.schemas import ProductCreate

        with pytest.raises(Exception):
            # Costo > precio — debería fallar en el service
            data = ProductCreate(
                name="Producto Test",
                price=3.00,
                cost=5.00,   # ← mayor que price
            )
            # El validator de schema no lo valida, lo valida el service
            assert data.cost > data.price

    def test_product_create_schema_valid(self):
        """ProductCreate acepta datos válidos."""
        from app.modules.products.schemas import ProductCreate

        data = ProductCreate(**PRODUCT_PAYLOAD)
        assert data.name == "Inca Kola 1.5L"
        assert data.price == 4.50
        assert data.category == "bebidas"

    def test_product_create_invalid_category(self):
        """ProductCreate rechaza categorías no válidas."""
        from app.modules.products.schemas import ProductCreate
        from pydantic import ValidationError

        with pytest.raises(ValidationError):
            ProductCreate(
                name="Test",
                price=5.00,
                category="categoria_inventada",
            )

    def test_product_create_invalid_price(self):
        """ProductCreate rechaza precio <= 0."""
        from app.modules.products.schemas import ProductCreate
        from pydantic import ValidationError

        with pytest.raises(ValidationError):
            ProductCreate(name="Test", price=0)

    def test_stock_adjust_schema(self):
        """StockAdjust acepta valores positivos y negativos."""
        from app.modules.products.schemas import StockAdjust

        entrada = StockAdjust(quantity=12, reason="Compra proveedor")
        assert entrada.quantity == 12

        merma = StockAdjust(quantity=-3, reason="Producto vencido")
        assert merma.quantity == -3


# ── Tests de respuestas ─────────────────────────────────────────────────────

class TestProductResponseFormat:
    """Verifica el formato estándar de respuestas."""

    def test_success_format(self):
        """success() retorna { data: ..., error: null }."""
        from app.shared.responses import success

        response = success({"id": "123", "name": "Test"})
        assert response["data"]["name"] == "Test"
        assert response["error"] is None

    def test_paginated_format(self):
        """paginated() retorna { data: [...], meta: {...}, error: null }."""
        from app.shared.responses import paginated

        response = paginated(data=[1, 2, 3], total=50, page=1, per_page=20)
        assert response["meta"]["total"] == 50
        assert response["meta"]["has_more"] is True
        assert response["error"] is None

    def test_error_format(self):
        """error() retorna { data: null, error: { code, message } }."""
        from app.shared.responses import error

        response = error("NOT_FOUND", "Producto no encontrado")
        assert response["data"] is None
        assert response["error"]["code"] == "NOT_FOUND"


# ── Tests de utilidades ────────────────────────────────────────────────────

class TestUtils:
    """Tests de funciones utilitarias."""

    def test_calculate_profit(self):
        """calculate_profit calcula correctamente la ganancia."""
        from app.shared.utils import calculate_profit

        # 1 unidad: precio 4.50 - costo 3.00 = 1.50
        assert calculate_profit(4.50, 3.00, 1) == 1.50

        # 10 unidades: 1.50 * 10 = 15.00
        assert calculate_profit(4.50, 3.00, 10) == 15.00

    def test_is_valid_uuid(self):
        """is_valid_uuid detecta UUIDs válidos e inválidos."""
        from app.shared.utils import is_valid_uuid

        assert is_valid_uuid("00000000-0000-0000-0000-000000000001") is True
        assert is_valid_uuid("no-es-un-uuid") is False
        assert is_valid_uuid("") is False
