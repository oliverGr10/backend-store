"""
Utilidades compartidas entre módulos.
"""

from datetime import datetime, timezone, date
from uuid import UUID
import re


def utcnow() -> datetime:
    """Retorna la fecha/hora actual en UTC (timezone-aware)."""
    return datetime.now(timezone.utc)


def today_range() -> tuple[datetime, datetime]:
    """
    Retorna el rango de inicio y fin del día de hoy en UTC.
    Útil para filtrar ventas del día.
    """
    today = date.today()
    start = datetime.combine(today, datetime.min.time()).replace(tzinfo=timezone.utc)
    end = datetime.combine(today, datetime.max.time()).replace(tzinfo=timezone.utc)
    return start, end


def is_valid_uuid(value: str) -> bool:
    """Verifica si un string es un UUID válido."""
    try:
        UUID(str(value))
        return True
    except ValueError:
        return False


def slugify(text: str) -> str:
    """Convierte un texto en slug (minúsculas, sin espacios, sin acentos)."""
    # Básico: solo ASCII
    text = text.lower().strip()
    text = re.sub(r"[^\w\s-]", "", text)
    text = re.sub(r"[\s_-]+", "-", text)
    text = re.sub(r"^-+|-+$", "", text)
    return text


def round_price(value: float, decimals: int = 2) -> float:
    """Redondea un precio a N decimales (por defecto 2)."""
    return round(value, decimals)


def calculate_profit(price: float, cost: float, quantity: int = 1) -> float:
    """Calcula la ganancia neta de un item vendido."""
    return round_price((price - cost) * quantity)
