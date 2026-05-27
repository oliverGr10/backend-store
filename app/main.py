"""
BodegaApp — FastAPI Application Entry Point.
Configura la app, middlewares, manejo de errores y registra todos los routers.
"""

import logging
from contextlib import asynccontextmanager
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from fastapi.security import HTTPBearer
from fastapi.exceptions import RequestValidationError
from starlette.exceptions import HTTPException as StarletteHTTPException

from app.config import get_settings

# ── Logging ────────────────────────────────────────────────────────────────
logging.basicConfig(
    level=logging.DEBUG,
    format="%(asctime)s  %(levelname)-8s  %(name)s — %(message)s",
    datefmt="%H:%M:%S",
)
logger = logging.getLogger("bodega")

from app.modules.products.router import router as products_router
from app.modules.sales.router import router as sales_router
from app.modules.debts.router import router as debts_router
from app.modules.auth.router import router as auth_router
from app.modules.ai.router import router as ai_router


# ── Lifespan (startup / shutdown) ──────────────────────────────────────────

@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Eventos de inicio y cierre de la aplicación.
    Las settings se cargan aquí (dentro del lifespan) para garantizar
    que el .env ya fue leído por uvicorn antes de instanciarlas.
    """
    s = get_settings()
    print(f"🚀 {s.app_name} v{s.app_version} arrancando...")
    print(f"   Entorno: {s.environment}")
    print(f"   Docs:    http://localhost:8000/docs")

    yield  # La app corre aquí

    print("🛑 Cerrando BodegaApp...")


# ── Creación de la app ─────────────────────────────────────────────────────

def create_app() -> FastAPI:
    """
    Factory function — crea y configura la app FastAPI.
    Usar factory evita que las settings se lean en tiempo de import.
    """
    s = get_settings()

    application = FastAPI(
        title=s.app_name,
        description=(
            "API para digitalizar bodegas de barrio en Perú.\n\n"
            "## Autenticación\n"
            "1. Haz `POST /auth/login` y copia el `access_token`\n"
            "2. Haz clic en **Authorize 🔒** (arriba a la derecha)\n"
            "3. Escribe `Bearer <tu-token>` y confirma\n"
            "4. Todos los endpoints usarán el token automáticamente"
        ),
        version=s.app_version,
        docs_url="/docs",
        redoc_url="/redoc",
        openapi_url="/openapi.json",
        lifespan=lifespan,
        swagger_ui_parameters={"persistAuthorization": True},
    )

    # ── CORS ────────────────────────────────────────────────────────────────
    application.add_middleware(
        CORSMiddleware,
        allow_origins=s.allowed_origins,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # ── Manejo global de errores ─────────────────────────────────────────────
    # Todos los errores retornan { data: null, error: { code, message } }

    @application.exception_handler(StarletteHTTPException)
    async def http_exception_handler(request: Request, exc: StarletteHTTPException):
        """
        Convierte HTTPExceptions al formato estándar.
        Incluye nuestras excepciones personalizadas (NotFoundError, etc.)
        y las de FastAPI (401 de Bearer, 422 de validación, etc.)
        """
        # Nuestras excepciones ya traen { code, message } en detail
        if isinstance(exc.detail, dict) and "code" in exc.detail:
            error = exc.detail
        else:
            # Mapear códigos HTTP comunes a mensajes en español
            messages = {
                401: ("UNAUTHORIZED", "No autenticado — incluye el token Bearer"),
                403: ("FORBIDDEN", "Sin permisos para esta acción"),
                404: ("NOT_FOUND", "Recurso no encontrado"),
                405: ("METHOD_NOT_ALLOWED", "Método no permitido"),
                409: ("CONFLICT", "Conflicto con datos existentes"),
                422: ("VALIDATION_ERROR", "Datos de entrada inválidos"),
                500: ("INTERNAL_ERROR", "Error interno del servidor"),
            }
            code, message = messages.get(exc.status_code, ("ERROR", str(exc.detail)))
            error = {"code": code, "message": message}

        return JSONResponse(
            status_code=exc.status_code,
            content={"data": None, "error": error},
        )

    @application.exception_handler(RequestValidationError)
    async def validation_exception_handler(request: Request, exc: RequestValidationError):
        """Pydantic validation errors → formato estándar con detalle de campos."""
        errors = exc.errors()
        # Construir mensaje legible: "campo: mensaje"
        messages = []
        for e in errors:
            field = " → ".join(str(loc) for loc in e["loc"] if loc != "body")
            messages.append(f"{field}: {e['msg']}" if field else e["msg"])

        return JSONResponse(
            status_code=422,
            content={
                "data": None,
                "error": {
                    "code": "VALIDATION_ERROR",
                    "message": " | ".join(messages),
                },
            },
        )

    @application.exception_handler(Exception)
    async def generic_exception_handler(request: Request, exc: Exception):
        """Captura cualquier error no manejado."""
        cfg = get_settings()
        detail = str(exc) if cfg.is_development else "Error interno del servidor"
        logger.error(f"Unhandled exception: {exc}", exc_info=True)
        return JSONResponse(
            status_code=500,
            content={"data": None, "error": {"code": "INTERNAL_ERROR", "message": detail}},
        )

    # ── Health check ─────────────────────────────────────────────────────────
    @application.get("/health", tags=["Sistema"], summary="Health check")
    async def health_check():
        """Verifica que la API está corriendo. Útil para Railway / Render."""
        cfg = get_settings()
        return {
            "data": {
                "status": "ok",
                "version": cfg.app_version,
                "environment": cfg.environment,
            },
            "error": None,
        }

    # ── Routers ──────────────────────────────────────────────────────────────
    application.include_router(auth_router, prefix=s.api_prefix)
    application.include_router(products_router, prefix=s.api_prefix)
    application.include_router(sales_router, prefix=s.api_prefix)
    application.include_router(debts_router, prefix=s.api_prefix)
    application.include_router(ai_router, prefix=s.api_prefix)

    return application


app = create_app()
