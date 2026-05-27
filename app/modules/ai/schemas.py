"""Schemas del módulo de IA."""

from typing import Optional, Literal
from pydantic import BaseModel, Field


class AIRequest(BaseModel):
    """
    Solicitud de análisis al asistente IA.
    type define qué tipo de análisis hacer.
    """
    type: Literal[
        "general",          # resumen completo del negocio
        "top_products",     # productos más vendidos
        "restock",          # qué necesita reabastecer
        "profit",           # análisis de ganancias
        "debts",            # situación de fiados
        "slow_products",    # productos que no se venden
    ] = Field(default="general")

    question: Optional[str] = Field(
        None,
        max_length=500,
        description="Pregunta libre al asistente. Ej: '¿Qué día vendo más?'",
    )
    days: int = Field(
        default=30,
        ge=1,
        le=90,
        description="Días hacia atrás a analizar (default: últimos 30 días)",
    )


class AIResponse(BaseModel):
    """Respuesta del asistente IA."""
    analysis: str           # respuesta en texto natural (español)
    type: str
    days_analyzed: int
    data_summary: dict      # resumen numérico de los datos usados
