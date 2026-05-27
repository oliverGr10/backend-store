"""
Conexión a la base de datos PostgreSQL de Supabase.
Usa SQLAlchemy 2.0 async + cliente Supabase para operaciones directas.

IMPORTANTE: el engine y el cliente Supabase se crean de forma lazy
(dentro de funciones) para evitar crashes al importar el módulo
antes de que el .env esté cargado.
"""

from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine, async_sessionmaker
from sqlalchemy.orm import DeclarativeBase
from supabase import create_client, Client
from app.config import get_settings


# ── Base para todos los modelos ORM ────────────────────────────────────────

class Base(DeclarativeBase):
    """Clase base que heredan todos los modelos SQLAlchemy."""
    pass


# ── Engine y sesión lazy ────────────────────────────────────────────────────

_engine = None
_session_factory = None


def _get_engine():
    """Crea el engine SQLAlchemy la primera vez que se necesita."""
    global _engine
    if _engine is None:
        s = get_settings()
        _engine = create_async_engine(
            s.async_database_url,
            echo=s.is_development,
            pool_size=5,
            max_overflow=10,
            pool_pre_ping=True,
            connect_args={"ssl": "require"},   # Supabase exige SSL siempre
        )
    return _engine


def _get_session_factory():
    """Crea el factory de sesiones la primera vez que se necesita."""
    global _session_factory
    if _session_factory is None:
        _session_factory = async_sessionmaker(
            _get_engine(),
            class_=AsyncSession,
            expire_on_commit=False,
        )
    return _session_factory


# ── Dependency injection para FastAPI ──────────────────────────────────────

async def get_db():
    """
    Dependency que provee una sesión de base de datos por request.
    Cierra la sesión automáticamente al terminar.
    """
    factory = _get_session_factory()
    async with factory() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise
        finally:
            await session.close()


# ── Cliente Supabase ────────────────────────────────────────────────────────

def get_supabase_client() -> Client:
    """
    Cliente Supabase para el backend.
    Usa service_role key para bypassear RLS — el backend aplica
    su propio control de acceso (user_id en cada query).
    En producción la seguridad real la garantiza el filtro user_id.
    """
    s = get_settings()
    return create_client(s.supabase_url, s.supabase_service_key)


def get_supabase_admin() -> Client:
    """Cliente Supabase con service_role key (para operaciones admin)."""
    s = get_settings()
    return create_client(s.supabase_url, s.supabase_service_key)
