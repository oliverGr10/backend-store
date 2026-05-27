"""Service de autenticación — delega en Supabase Auth."""

import logging
from supabase import Client

from app.modules.auth.schemas import LoginRequest, LoginResponse, RegisterRequest, AuthUserResponse
from app.shared.exceptions import UnauthorizedError, ConflictError, ValidationError

logger = logging.getLogger("bodega.auth")


class AuthService:
    def __init__(self, db: Client):
        self.db = db

    def register(self, data: RegisterRequest) -> AuthUserResponse:
        """Crea un nuevo usuario bodeguero en Supabase Auth."""
        try:
            response = self.db.auth.sign_up({
                "email": data.email,
                "password": data.password,
            })
            user = response.user
            session = response.session

            if not user:
                raise ValidationError("No se pudo crear el usuario")

            logger.info(f"Usuario registrado: {user.email}")

            # Supabase puede requerir confirmación de email
            # Si no hay session, el email necesita confirmarse
            access_token = session.access_token if session else ""

            return AuthUserResponse(
                user_id=str(user.id),
                email=user.email,
                access_token=access_token,
            )
        except (ValidationError, ConflictError):
            raise
        except Exception as e:
            error_msg = str(e).lower()
            logger.error(f"Register error: {e}")
            if "already registered" in error_msg or "already been registered" in error_msg:
                raise ConflictError("Este email ya está registrado")
            raise ValidationError(f"Error al registrar: {str(e)}")

    def login(self, data: LoginRequest) -> LoginResponse:
        """Autentica con email y contraseña. Retorna JWT."""
        try:
            response = self.db.auth.sign_in_with_password({
                "email": data.email,
                "password": data.password,
            })
            session = response.session
            user = response.user

            if not session or not user:
                raise UnauthorizedError("Credenciales incorrectas")

            logger.info(f"Login exitoso: {user.email}")
            return LoginResponse(
                access_token=session.access_token,
                user_id=str(user.id),
                email=user.email,
            )
        except UnauthorizedError:
            raise
        except Exception as e:
            logger.error(f"Login error: {e}")
            raise UnauthorizedError("Email o contraseña incorrectos")

    def logout(self, access_token: str) -> dict:
        """Invalida el token en Supabase."""
        try:
            self.db.auth.sign_out()
            logger.info("Logout exitoso")
        except Exception as e:
            logger.warning(f"Logout warning (ignorado): {e}")
        return {"message": "Sesión cerrada correctamente"}

    def me(self, access_token: str) -> dict:
        """Retorna los datos del usuario autenticado."""
        try:
            response = self.db.auth.get_user(access_token)
            user = response.user
            if not user:
                raise UnauthorizedError()
            return {
                "user_id": str(user.id),
                "email": user.email,
                "created_at": str(user.created_at),
            }
        except UnauthorizedError:
            raise
        except Exception as e:
            logger.error(f"me() error: {e}")
            raise UnauthorizedError("Token inválido o expirado")
