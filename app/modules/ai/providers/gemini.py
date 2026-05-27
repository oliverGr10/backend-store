"""Proveedor de IA: Google Gemini."""

import logging
from google import genai
from google.genai import types

from app.modules.ai.providers.base import AIProvider

logger = logging.getLogger("bodega.ai.gemini")

GEMINI_MODEL = "gemini-2.0-flash"


class GeminiProvider(AIProvider):
    """Implementación con Google Gemini (nuevo SDK google-genai)."""

    def __init__(self, api_key: str):
        masked = f"{api_key[:6]}...{api_key[-6:]}" if len(api_key) > 12 else "***"
        logger.info(f"🔑 Gemini client inicializado con key: {masked}")
        self.client = genai.Client(api_key=api_key)

    @property
    def provider_name(self) -> str:
        return f"Google Gemini ({GEMINI_MODEL})"

    def generate(self, prompt: str, max_tokens: int = 1024, temperature: float = 0.7) -> str:
        logger.info(f"📡 Llamando a Gemini ({len(prompt)} chars)...")
        response = self.client.models.generate_content(
            model=GEMINI_MODEL,
            contents=prompt,
            config=types.GenerateContentConfig(
                temperature=temperature,
                max_output_tokens=max_tokens,
            ),
        )
        text = response.text
        logger.info(f"✅ Gemini respondió: {len(text)} chars")
        return text
