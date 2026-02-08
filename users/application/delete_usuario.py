from sqlalchemy.orm import Session
from fastapi import HTTPException
from users.infrastructure.repositories import UsuarioRepository
from shared.supabase_client import SupabaseClient, SupabaseAdminError
import logging

logger = logging.getLogger(__name__)


class DeleteUsuarioUseCase:

    def __init__(self, repository: UsuarioRepository):
        self.repository = repository
        self.supabase = SupabaseClient()

    def execute(self, db: Session, id_usuario: int) -> None:
        usuario = self.repository.get_by_id(db, id_usuario)

        if not usuario:
            raise HTTPException(
                status_code=404,
                detail="Usuario no encontrado"
            )

        # Verificar si el usuario tiene tratamientos asociados
        from treatments.infrastructure.models import Tratamiento
        tratamientos_count = db.query(Tratamiento).filter(
            Tratamiento.id_usuario == id_usuario
        ).count()

        if tratamientos_count > 0:
            raise HTTPException(
                status_code=409,
                detail=f"No se puede eliminar el usuario porque tiene {tratamientos_count} tratamiento(s) asignado(s). Reasigne o elimine los tratamientos primero."
            )

        # Eliminar de Supabase Auth si el usuario tiene auth_id
        if usuario.auth_id and self.supabase.url and self.supabase.service_role:
            try:
                self.supabase.delete_user(usuario.auth_id)
            except SupabaseAdminError as e:
                logger.error(f"Error deleting Supabase user {usuario.auth_id}: {e}")
                # Continuar con la eliminacion local aunque falle en Supabase
                # para no dejar el sistema en estado inconsistente

        self.repository.delete(db, usuario)
