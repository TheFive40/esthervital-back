from fastapi import HTTPException
from sqlalchemy.orm import Session
from users.infrastructure.repositories import UsuarioRepository
from users.presentation.schemas import UsuarioUpdate

class UpdateUsuarioUseCase:

    def __init__(self, repo: UsuarioRepository):
        self.repo = repo

    def execute(self, db: Session, user_id: int, data: UsuarioUpdate):
        usuario = self.repo.get_by_id(db, user_id)

        if not usuario:
            raise HTTPException(status_code=404, detail="Usuario no encontrado")

        for field, value in data.dict(exclude_unset=True).items():
            setattr(usuario, field, value)

        return self.repo.update(db, usuario)
