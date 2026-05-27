"""Router de autenticación."""

from fastapi import APIRouter, Depends
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials

from app.database import get_supabase_client
from app.modules.auth.service import AuthService
from app.modules.auth.schemas import LoginRequest, RegisterRequest
from app.shared.responses import success

router = APIRouter(prefix="/auth", tags=["Autenticación"])
bearer_scheme = HTTPBearer(auto_error=True)


def get_service() -> AuthService:
    return AuthService(get_supabase_client())


@router.post("/register", summary="Registrar bodeguero", response_model=dict, status_code=201)
def register(
    body: RegisterRequest,
    service: AuthService = Depends(get_service),
):
    """Crea una cuenta nueva."""
    result = service.register(body)
    return success(result.model_dump())


@router.post("/login", summary="Iniciar sesión", response_model=dict)
def login(
    body: LoginRequest,
    service: AuthService = Depends(get_service),
):
    """
    Retorna el `access_token`.
    Luego haz clic en **🔒 Authorize** (arriba a la derecha en Swagger)
    y pega el token para autenticar los demás endpoints.
    """
    result = service.login(body)
    return success(result.model_dump())


@router.get("/me", summary="Mi perfil", response_model=dict)
def me(
    credentials: HTTPAuthorizationCredentials = Depends(bearer_scheme),
    service: AuthService = Depends(get_service),
):
    """Retorna los datos del usuario autenticado."""
    result = service.me(credentials.credentials)
    return success(result)


@router.post("/logout", summary="Cerrar sesión", response_model=dict)
def logout(
    credentials: HTTPAuthorizationCredentials = Depends(bearer_scheme),
    service: AuthService = Depends(get_service),
):
    result = service.logout(credentials.credentials)
    return success(result)
