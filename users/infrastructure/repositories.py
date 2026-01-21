from sqlalchemy.orm import Session
from users.infrastructure.models import Usuario


class UsuarioRepository:

    def __init__(self, db: Session):
        self.db = db

    def create(self, usuario: Usuario):
        self.db.add(usuario)
        self.db.commit()
        self.db.refresh(usuario)
        return usuario

    def get_by_id(self, db: Session, user_id: int):
        return db.query(Usuario).filter(Usuario.id_usuario == user_id).first()

    def update(self, db: Session, usuario: Usuario):
        db.commit()
        db.refresh(usuario)
        return usuario

    def delete(self, db: Session, usuario: Usuario):
        db.delete(usuario)
        db.commit()