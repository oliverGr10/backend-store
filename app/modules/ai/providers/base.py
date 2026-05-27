"""Interfaz abstracta para proveedores de IA."""

from abc import ABC, abstractmethod


class AIProvider(ABC):
    """
    Contrato que debe cumplir cualquier proveedor de IA.
    Para agregar un nuevo proveedor: heredar esta clase e implementar `generate`.
    """

    @abstractmethod
    def generate(self, prompt: str, max_tokens: int = 1024, temperature: float = 0.7) -> str:
        """
        Envía el prompt al modelo y retorna la respuesta en texto.
        Lanza Exception si hay error de API.
        """
        ...

    @property
    @abstractmethod
    def provider_name(self) -> str:
        """Nombre del proveedor para logs."""
        ...
