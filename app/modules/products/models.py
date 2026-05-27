import uuid
from datetime import datetime
from sqlalchemy import String, Numeric, Integer, Boolean, Text, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy.dialects.postgresql import UUID as PG_UUID, TIMESTAMP
from app.database import Base


class Product(Base):
    """Tabla de productos del inventario de la bodega."""

    __tablename__ = "products"

    # --- Clave primaria ---
    id: Mapped[uuid.UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
    )

    # --- Relación con el usuario (bodeguero) ---
    user_id: Mapped[uuid.UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("auth.users.id"),
        nullable=False,
        index=True,
    )

    # --- Datos del producto ---
    name: Mapped[str] = mapped_column(String(255), nullable=False)

    price: Mapped[float] = mapped_column(
        Numeric(10, 2),
        nullable=False,
        comment="Precio de venta al cliente",
    )

    cost: Mapped[float] = mapped_column(
        Numeric(10, 2),
        default=0.0,
        comment="Precio de compra (para calcular ganancia)",
    )

    stock: Mapped[int] = mapped_column(
        Integer,
        default=0,
        comment="Cantidad disponible en bodega",
    )

    min_stock: Mapped[int] = mapped_column(
        Integer,
        default=5,
        comment="Alerta cuando el stock baja de este número",
    )

    category: Mapped[str] = mapped_column(
        String(100),
        default="general",
        comment="Categoría: bebidas, abarrotes, snacks, limpieza...",
    )

    unit: Mapped[str] = mapped_column(
        String(50),
        default="unidad",
        comment="Unidad de medida: unidad, kg, litro, docena",
    )

    is_active: Mapped[bool] = mapped_column(
        Boolean,
        default=True,
        comment="Soft delete — false = producto eliminado",
    )

    # --- Timestamps ---
    created_at: Mapped[datetime] = mapped_column(
        TIMESTAMP(timezone=True),
        nullable=False,
        default=datetime.utcnow,
    )

    updated_at: Mapped[datetime] = mapped_column(
        TIMESTAMP(timezone=True),
        nullable=False,
        default=datetime.utcnow,
        onupdate=datetime.utcnow,
    )

    def __repr__(self) -> str:
        return f"<Product id={self.id} name={self.name!r} stock={self.stock}>"

    @property
    def is_low_stock(self) -> bool:
        """True si el stock está por debajo del mínimo configurado."""
        return self.stock <= self.min_stock

    @property
    def margin(self) -> float:
        """Ganancia por unidad vendida."""
        return round(float(self.price) - float(self.cost), 2)
