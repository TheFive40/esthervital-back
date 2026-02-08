from sqlalchemy.orm import Session
from fastapi import HTTPException
from passlib.context import CryptContext
from users.infrastructure.repositories import UsuarioRepository
from users.presentation.schemas import CambiarPassword
from shared.supabase_client import SupabaseClient, SupabaseAdminError
import logging

logger = logging.getLogger(__name__)

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


class ChangePasswordUseCase:

    def __init__(self, repository: UsuarioRepository):
        self.repository = repository
        self.supabase = SupabaseClient()

    def execute(
        self,
        db: Session,
        id_usuario: int,
        data: CambiarPassword
    ) -> dict:

        usuario = self.repository.get_by_id(db, id_usuario)

        if not usuario:
            raise HTTPException(
                status_code=404,
                detail="Usuario no encontrado"
            )

        if not pwd_context.verify(data.password_actual, usuario.password):
            raise HTTPException(
                status_code=400,
                detail="Contraseña actual incorrecta"
            )

        # Actualizar contraseña en Supabase Auth si el usuario tiene auth_id
        if usuario.auth_id and self.supabase.url and self.supabase.service_role:
            try:
                self.supabase.update_user_password(usuario.auth_id, data.password_nueva)
            except SupabaseAdminError as e:
                logger.error(f"Error updating Supabase password for user {id_usuario}: {e}")
                raise HTTPException(
                    status_code=502,
                    detail="Error actualizando contraseña en el proveedor de autenticación"
                )

        usuario.password = pwd_context.hash(data.password_nueva)
        usuario.primer_login = False  # Mark first login as completed
        self.repository.update(db, usuario)

        return {
            "message": "Contraseña actualizada correctamente"
        }
