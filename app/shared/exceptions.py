from fastapi import HTTPException, status


class NotFoundError(HTTPException):
    """El recurso solicitado no existe."""
    def __init__(self, resource: str = "Recurso"):
        super().__init__(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={
                "code": "NOT_FOUND",
                "message": f"{resource} no encontrado",
            },
        )


class ConflictError(HTTPException):
    """El recurso ya existe o hay un conflicto de datos."""
    def __init__(self, message: str = "El recurso ya existe"):
        super().__init__(
            status_code=status.HTTP_409_CONFLICT,
            detail={
                "code": "CONFLICT",
                "message": message,
            },
        )


class ValidationError(HTTPException):
    """Datos de entrada inválidos (lógica de negocio, no de schema)."""
    def __init__(self, message: str):
        super().__init__(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail={
                "code": "VALIDATION_ERROR",
                "message": message,
            },
        )


class UnauthorizedError(HTTPException):
    """El usuario no está autenticado."""
    def __init__(self, message: str = "No autenticado"):
        super().__init__(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail={
                "code": "UNAUTHORIZED",
                "message": message,
            },
            headers={"WWW-Authenticate": "Bearer"},
        )


class ForbiddenError(HTTPException):
    """El usuario no tiene permisos para esta acción."""
    def __init__(self, message: str = "Sin permisos para esta acción"):
        super().__init__(
            status_code=status.HTTP_403_FORBIDDEN,
            detail={
                "code": "FORBIDDEN",
                "message": message,
            },
        )


class InsufficientStockError(HTTPException):
    """No hay suficiente stock para completar la operación."""
    def __init__(self, product_name: str, available: int, requested: int):
        super().__init__(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={
                "code": "INSUFFICIENT_STOCK",
                "message": f"Stock insuficiente para '{product_name}'. "
                           f"Disponible: {available}, solicitado: {requested}",
            },
        )


class DatabaseError(HTTPException):
    """Error inesperado al interactuar con la base de datos."""
    def __init__(self, message: str = "Error interno de base de datos"):
        super().__init__(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={
                "code": "DATABASE_ERROR",
                "message": message,
            },
        )
