"""Router del módulo de IA."""

import uuid
from fastapi import APIRouter, Depends

from app.database import get_supabase_client
from app.modules.ai.service import AIService
from app.modules.ai.factory import get_ai_provider
from app.modules.ai.schemas import AIRequest
from app.modules.auth.dependencies import get_current_user
from app.shared.responses import success

router = APIRouter(prefix="/ai", tags=["Inteligencia Artificial 🤖"])


def get_service() -> AIService:
    return AIService(
        db=get_supabase_client(),
        ai_provider=get_ai_provider(),
    )


@router.post(
    "/recommendations",
    summary="Análisis y recomendaciones IA",
    response_model=dict,
    description="""
Analiza los datos reales de tu bodega y genera recomendaciones personalizadas.

**Tipos de análisis disponibles:**
- `general` — resumen completo del negocio con 3 recomendaciones
- `top_products` — productos estrella y oportunidades
- `restock` — qué reabastecer urgentemente
- `profit` — análisis de ganancias y márgenes
- `debts` — estrategia para cobrar fiados
- `slow_products` — qué hacer con productos que no rotan

También puedes hacer una **pregunta libre** con el campo `question`.

**Proveedor IA:** configurable en `.env` con `AI_PROVIDER=gemini|anthropic`
""",
)
def get_recommendations(
    body: AIRequest,
    service: AIService = Depends(get_service),
    user_id: uuid.UUID = Depends(get_current_user),
):
    result = service.analyze(body, user_id)
    return success(result.model_dump())
