"""
Formato estándar de respuestas para toda la API.
Estructura: { data: T | null, error: ErrorDetail | null, meta: dict | null }
"""

from typing import Any, Generic, TypeVar, Optional
from pydantic import BaseModel

T = TypeVar("T")


class ErrorDetail(BaseModel):
    """Detalle de un error de API."""
    code: str
    message: str


class Meta(BaseModel):
    """Metadatos de paginación u otros."""
    total: Optional[int] = None
    page: Optional[int] = None
    per_page: Optional[int] = None
    has_more: Optional[bool] = None


class ApiResponse(BaseModel, Generic[T]):
    """
    Respuesta estándar de la API.

    Éxito:  { "data": {...}, "error": null }
    Error:  { "data": null,  "error": { "code": "...", "message": "..." } }
    Lista:  { "data": [...], "error": null, "meta": { "total": N } }
    """
    data: Optional[T] = None
    error: Optional[ErrorDetail] = None
    meta: Optional[Meta] = None


def success(data: Any, meta: Optional[dict] = None) -> dict:
    """
    Construye una respuesta exitosa.

    Ejemplo:
        return success(product)
        return success(products, meta={"total": 42})
    """
    response: dict[str, Any] = {"data": data, "error": None}
    if meta:
        response["meta"] = meta
    return response


def error(code: str, message: str) -> dict:
    """
    Construye una respuesta de error estándar.

    Ejemplo:
        return error("NOT_FOUND", "Producto no encontrado")
    """
    return {
        "data": None,
        "error": {"code": code, "message": message},
    }


def paginated(data: list, total: int, page: int, per_page: int) -> dict:
    """
    Construye una respuesta paginada.

    Ejemplo:
        return paginated(products, total=100, page=1, per_page=20)
    """
    return {
        "data": data,
        "error": None,
        "meta": {
            "total": total,
            "page": page,
            "per_page": per_page,
            "has_more": (page * per_page) < total,
        },
    }
