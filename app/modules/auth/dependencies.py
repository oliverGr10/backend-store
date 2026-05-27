"""
Dependency de autenticación para FastAPI.
Usa HTTPBearer para que Swagger muestre el candado 🔒 en cada endpoint.
"""

import uuid
import logging
from fastapi import Depends
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials

from app.database import get_supabase_client
from app.shared.exceptions import UnauthorizedError

logger = logging.getLogger("bodega.auth.deps")

# Este scheme hace que Swagger muestre el botón Authorize 🔒
bearer_scheme = HTTPBearer(auto_error=True)


def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(bearer_scheme),
) -> uuid.UUID:
    """
    Valida el JWT de Supabase y retorna el user_id.

    En Swagger: clic en 🔒 Authorize → escribe el token (sin 'Bearer').
    En código:  Authorization: Bearer <token>
    """
    token = credentials.credentials
    if not token:
        raise UnauthorizedError("Token vacío")

    try:
        db = get_supabase_client()
        response = db.auth.get_user(token)
        user = response.user
        if not user:
            raise UnauthorizedError()
        logger.debug(f"✅ Usuario autenticado: {user.email}")
        return uuid.UUID(str(user.id))
    except UnauthorizedError:
        raise
    except Exception as e:
        logger.error(f"Token error: {e}")
        raise UnauthorizedError("Token inválido o expirado")
