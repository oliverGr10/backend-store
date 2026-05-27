"""
Factory de proveedores IA.
Lee AI_PROVIDER del .env y retorna el proveedor correcto.
Para cambiar de IA: solo cambia AI_PROVIDER y la key en .env.
"""

import logging
from app.config import get_settings
from app.modules.ai.providers.base import AIProvider

logger = logging.getLogger("bodega.ai")


def get_ai_provider() -> AIProvider:
    """
    Instancia el proveedor de IA configurado en .env.

    Proveedores disponibles:
      - gemini     → Google Gemini (requiere GEMINI_API_KEY)
      - anthropic  → Anthropic Claude (requiere ANTHROPIC_API_KEY)

    Ejemplo .env:
      AI_PROVIDER=anthropic
      ANTHROPIC_API_KEY=sk-ant-...
    """
    s = get_settings()
    provider_name = s.ai_provider.lower()

    logger.info(f"🤖 Proveedor IA seleccionado: {provider_name}")

    if provider_name == "gemini":
        from app.modules.ai.providers.gemini import GeminiProvider
        if not s.gemini_api_key:
            raise ValueError("AI_PROVIDER=gemini pero GEMINI_API_KEY no está configurado en .env")
        return GeminiProvider(api_key=s.gemini_api_key)

    elif provider_name == "anthropic":
        from app.modules.ai.providers.anthropic import AnthropicProvider
        if not s.anthropic_api_key:
            raise ValueError("AI_PROVIDER=anthropic pero ANTHROPIC_API_KEY no está configurado en .env")
        return AnthropicProvider(api_key=s.anthropic_api_key)

    else:
        raise ValueError(
            f"AI_PROVIDER='{provider_name}' no reconocido. "
            "Opciones válidas: 'gemini', 'anthropic'"
        )
