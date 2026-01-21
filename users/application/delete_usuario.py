from sqlalchemy.orm import Session
from fastapi import HTTPException
from users.infrastructure.repositories import UsuarioRepository


class DeleteUsuarioUseCase:

    def __init__(self, repository: UsuarioRepository):
        self.repository = repository

    def execute(self, db: Session, id_usuario: int) -> None:
        usuario = self.repository.get_by_id(db, id_usuario)

        if not usuario:
            raise HTTPException(
                status_code=404,
                detail="Usuario no encontrado"
            )

        self.repository.delete(db, usuario)
