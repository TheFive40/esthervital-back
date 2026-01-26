from sqlalchemy.orm import Session
from fastapi import HTTPException
from passlib.context import CryptContext
from users.infrastructure.repositories import UsuarioRepository
from users.presentation.schemas import CambiarPassword


pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


class ChangePasswordUseCase:

    def __init__(self, repository: UsuarioRepository):
        self.repository = repository

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

        usuario.password = pwd_context.hash(data.password_nueva)
        usuario.primer_login = False  # Mark first login as completed
        self.repository.update(db, usuario)

        return {
            "message": "Contraseña actualizada correctamente"
        }
