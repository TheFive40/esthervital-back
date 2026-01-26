from pydantic import BaseModel, EmailStr
from datetime import datetime


class UsuarioCreate(BaseModel):
    nombre: str
    apellido: str
    email: EmailStr
    password: str
    id_rol: int


class UsuarioResponse(BaseModel):
    id_usuario: int
    nombre: str
    apellido: str
    email: EmailStr
    estado: str
    id_rol: int
    primer_login: bool = True
    fecha_creacion: datetime

    class Config:
        from_attributes = True

from pydantic import BaseModel, EmailStr

class UsuarioUpdate(BaseModel):
    nombre: str | None = None
    apellido: str | None = None
    email: EmailStr | None = None
    estado: str | None = None
    id_rol: int | None = None


class CambiarPassword(BaseModel):
    password_actual: str
    password_nueva: str

class CambiarPasswordPrimerLogin(BaseModel):
    password_nueva: str

class RolBase(BaseModel):
    nombre_rol: str
    descripcion: str | None = None

class RolCreate(RolBase):
    pass

class RolResponse(RolBase):
    id_rol: int

    class Config:
        from_attributes = True

class PermisoBase(BaseModel):
    nombre_permiso: str
    modulo: str | None = None
    descripcion: str | None = None

class PermisoCreate(PermisoBase):
    pass

class PermisoResponse(PermisoBase):
    id_permiso: int

    class Config:
        from_attributes = True
