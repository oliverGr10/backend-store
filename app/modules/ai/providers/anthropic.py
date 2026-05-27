"""Proveedor de IA: Anthropic Claude."""

import logging
import anthropic

from app.modules.ai.providers.base import AIProvider

logger = logging.getLogger("bodega.ai.anthropic")

CLAUDE_MODEL = "claude-haiku-4-5-20251001"   # rápido y económico para producción


class AnthropicProvider(AIProvider):
    """Implementación con Anthropic Claude."""

    def __init__(self, api_key: str):
        masked = f"{api_key[:10]}...{api_key[-6:]}" if len(api_key) > 16 else "***"
        logger.info(f"🔑 Anthropic client inicializado con key: {masked}")
        self.client = anthropic.Anthropic(api_key=api_key)

    @property
    def provider_name(self) -> str:
        return f"Anthropic Claude ({CLAUDE_MODEL})"

    def generate(self, prompt: str, max_tokens: int = 1024, temperature: float = 0.7) -> str:
        logger.info(f"📡 Llamando a Claude ({len(prompt)} chars)...")
        message = self.client.messages.create(
            model=CLAUDE_MODEL,
            max_tokens=max_tokens,
            temperature=temperature,
            messages=[{"role": "user", "content": prompt}],
        )
        text = message.content[0].text
        logger.info(f"✅ Claude respondió: {len(text)} chars")
        return text
