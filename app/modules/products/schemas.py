import uuid
from datetime import datetime
from typing import Optional
from pydantic import BaseModel, Field, field_validator, computed_field


# ── Categorías y unidades válidas ──────────────────────────────────────────

VALID_CATEGORIES = {
    "general", "bebidas", "abarrotes", "snacks",
    "limpieza", "panaderia", "lacteos", "carnes", "frutas",
}

VALID_UNITS = {"unidad", "kg", "litro", "docena", "paquete", "caja"}


# ── Schemas de REQUEST ─────────────────────────────────────────────────────

class ProductCreate(BaseModel):
    """
    Datos requeridos para crear un producto nuevo.
    Todos los campos con default son opcionales en el body del request.
    """
    name: str = Field(
        ...,
        min_length=2,
        max_length=255,
        examples=["Inca Kola 1.5L"],
    )
    price: float = Field(
        ...,
        gt=0,
        description="Precio de venta (mayor que 0)",
        examples=[4.50],
    )
    cost: float = Field(
        default=0.0,
        ge=0,
        description="Precio de compra (para calcular ganancia)",
        examples=[3.00],
    )
    stock: int = Field(
        default=0,
        ge=0,
        description="Cantidad inicial en inventario",
        examples=[24],
    )
    min_stock: int = Field(
        default=5,
        ge=0,
        description="Alerta de stock bajo cuando llega a este número",
        examples=[6],
    )
    category: str = Field(
        default="general",
        examples=["bebidas"],
    )
    unit: str = Field(
        default="unidad",
        examples=["unidad"],
    )

    @field_validator("category")
    @classmethod
    def validate_category(cls, v: str) -> str:
        v = v.lower().strip()
        if v not in VALID_CATEGORIES:
            raise ValueError(
                f"Categoría '{v}' no válida. Opciones: {sorted(VALID_CATEGORIES)}"
            )
        return v

    @field_validator("unit")
    @classmethod
    def validate_unit(cls, v: str) -> str:
        v = v.lower().strip()
        if v not in VALID_UNITS:
            raise ValueError(
                f"Unidad '{v}' no válida. Opciones: {sorted(VALID_UNITS)}"
            )
        return v

    @field_validator("price", "cost")
    @classmethod
    def round_decimal(cls, v: float) -> float:
        return round(v, 2)


class ProductUpdate(BaseModel):
    """
    Datos para actualizar un producto (todos los campos son opcionales).
    Solo se actualizan los campos que se envíen.
    """
    name: Optional[str] = Field(None, min_length=2, max_length=255)
    price: Optional[float] = Field(None, gt=0)
    cost: Optional[float] = Field(None, ge=0)
    stock: Optional[int] = Field(None, ge=0)
    min_stock: Optional[int] = Field(None, ge=0)
    category: Optional[str] = None
    unit: Optional[str] = None

    @field_validator("category")
    @classmethod
    def validate_category(cls, v: Optional[str]) -> Optional[str]:
        if v is None:
            return v
        v = v.lower().strip()
        if v not in VALID_CATEGORIES:
            raise ValueError(f"Categoría '{v}' no válida.")
        return v

    @field_validator("unit")
    @classmethod
    def validate_unit(cls, v: Optional[str]) -> Optional[str]:
        if v is None:
            return v
        v = v.lower().strip()
        if v not in VALID_UNITS:
            raise ValueError(f"Unidad '{v}' no válida.")
        return v


class StockAdjust(BaseModel):
    """Ajuste directo de stock (entrada de mercadería)."""
    quantity: int = Field(
        ...,
        description="Cantidad a sumar (positivo) o restar (negativo) del stock",
        examples=[12],
    )
    reason: Optional[str] = Field(
        None,
        max_length=255,
        description="Motivo del ajuste: compra, merma, corrección...",
        examples=["Compra proveedor"],
    )


# ── Schemas de RESPONSE ────────────────────────────────────────────────────

class ProductResponse(BaseModel):
    """
    Producto tal como lo retorna la API.
    Incluye campos calculados: is_low_stock y margin.
    """
    id: uuid.UUID
    user_id: uuid.UUID
    name: str
    price: float
    cost: float
    stock: int
    min_stock: int
    category: str
    unit: str
    is_active: bool
    created_at: datetime
    updated_at: datetime

    # Campos calculados
    is_low_stock: bool = Field(
        description="True si el stock está en o por debajo del mínimo"
    )
    margin: float = Field(
        description="Ganancia por unidad: precio - costo"
    )

    model_config = {"from_attributes": True}


class ProductListResponse(BaseModel):
    """Lista de productos con conteo total."""
    items: list[ProductResponse]
    total: int


# ── Filtros de búsqueda ────────────────────────────────────────────────────

class ProductFilters(BaseModel):
    """Parámetros de query para listar productos."""
    category: Optional[str] = None
    low_stock: Optional[bool] = None       # solo los que tienen stock bajo
    is_active: Optional[bool] = True       # por defecto solo activos
    search: Optional[str] = None           # búsqueda por nombre
    page: int = Field(default=1, ge=1)
    per_page: int = Field(default=20, ge=1, le=100)
