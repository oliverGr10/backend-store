"""
Configuración central de BodegaApp.
Lee variables de entorno con validación via pydantic-settings.
"""

from pydantic_settings import BaseSettings
from pydantic import Field
from functools import lru_cache


class Settings(BaseSettings):
    """Variables de entorno requeridas para correr el backend."""

    # --- Entorno ---
    environment: str = Field(default="development", alias="ENVIRONMENT")
    secret_key: str = Field(..., alias="SECRET_KEY")

    # --- Supabase ---
    supabase_url: str = Field(..., alias="SUPABASE_URL")
    supabase_key: str = Field(..., alias="SUPABASE_KEY")
    supabase_service_key: str = Field(..., alias="SUPABASE_SERVICE_KEY")

    # --- Base de datos (PostgreSQL directo vía SQLAlchemy async) ---
    database_url: str = Field(..., alias="DATABASE_URL")

    # --- IA (proveedor intercambiable) ---
    # AI_PROVIDER=gemini  → usa GEMINI_API_KEY
    # AI_PROVIDER=anthropic → usa ANTHROPIC_API_KEY
    ai_provider: str = Field(default="anthropic", alias="AI_PROVIDER")
    gemini_api_key: str = Field(default="", alias="GEMINI_API_KEY")
    anthropic_api_key: str = Field(default="", alias="ANTHROPIC_API_KEY")

    # --- App ---
    app_name: str = "BodegaApp API"
    app_version: str = "0.1.0"
    api_prefix: str = "/api/v1"
    debug: bool = Field(default=False, alias="DEBUG")

    # --- CORS ---
    allowed_origins: list[str] = ["http://localhost:3000", "http://localhost:8081"]

    model_config = {
        "env_file": ".env",
        "env_file_encoding": "utf-8",
        "populate_by_name": True,
        "extra": "ignore",          # ignora vars de entorno desconocidas
    }

    @property
    def is_development(self) -> bool:
        return self.environment == "development"

    @property
    def async_database_url(self) -> str:
        """Convierte la URL a formato async para asyncpg."""
        url = self.database_url
        if url.startswith("postgresql://"):
            return url.replace("postgresql://", "postgresql+asyncpg://", 1)
        return url


@lru_cache()
def get_settings() -> Settings:
    """
    Retorna la instancia singleton de configuración.
    El @lru_cache garantiza que Settings() se construye una sola vez.
    Se llama explícitamente (no en tiempo de import) para evitar crashes
    cuando el .env aún no está configurado.
    """
    return Settings()


def get_settings_dependency() -> Settings:
    """Alias para usar como Depends() en FastAPI sin el lru_cache directamente."""
    return get_settings()
