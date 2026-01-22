from sqlalchemy.orm import Session
from users.infrastructure.models import Usuario, Rol, Permiso


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
    
    def get_by_email(self, email: str):
        return self.db.query(Usuario).filter(Usuario.email == email).first()
    
    def get_all(self):
        return self.db.query(Usuario).all()

    def update(self, db: Session, usuario: Usuario):
        db.commit()
        db.refresh(usuario)
        return usuario

    def delete(self, db: Session, usuario: Usuario):
        db.delete(usuario)
        db.commit()

class RolRepository: 
    def __init__(self, db: Session):
        self.db = db

    def get_all(self):
        return self.db.query(Rol).all()
    
    def create(self, rol_data):
        nuevo_rol = Rol(**rol_data.dict())
        self.db.add(nuevo_rol)
        self.db.commit()
        self.db.refresh(nuevo_rol)
        return nuevo_rol
    
    def delete(self, id_rol: int):
        rol = self.db.query(Rol).filter(Rol.id_rol == id_rol).first()
        if rol:
            self.db.delete(rol)
            self.db.commit()
            return True
        return False
    
class PermisoRepository:
    def __init__(self, db: Session):
        self.db = db

    def get_all(self):
        return self.db.query(Permiso).all()
    
    def create(self, permiso_data):
        nuevo_permiso = Permiso(**permiso_data.dict())
        self.db.add(nuevo_permiso)
        self.db.commit()
        self.db.refresh(nuevo_permiso)
        return nuevo_permiso
    def delete(self, id_permiso: int):  
        permiso = self.db.query(Permiso).filter(Permiso.id_permiso == id_permiso).first()
        if permiso:
            self.db.delete(permiso)
            self.db.commit()
            return True
        return False
    
    