from pydantic import BaseModel, EmailStr
from typing import Optional
from datetime import date, datetime

class PacienteCreate(BaseModel):
    nombre: str
    apellido: str
    fecha_nacimiento: date
    edad: Optional[int] = None
    peso_kg: Optional[float] = None

    telefono: Optional[str] = None
    email: Optional[EmailStr] = None
    direccion: Optional[str] = None
    ocupacion: Optional[str] = None

    numero_hijos: Optional[int] = None
    tipo_parto: Optional[str] = None

    tipo_identificacion: str
    numero_identificacion: str
    estado: Optional[str] = "Activo"

class PacienteUpdate(BaseModel):
    nombre: Optional[str]
    apellido: Optional[str]
    fecha_nacimiento: Optional[date]
    edad: Optional[int]
    peso_kg: Optional[float]

    telefono: Optional[str]
    email: Optional[EmailStr]
    direccion: Optional[str]
    ocupacion: Optional[str]

    numero_hijos: Optional[int]
    tipo_parto: Optional[str]

    tipo_identificacion: Optional[str]
    numero_identificacion: Optional[str]
    estado: Optional[str]

class PacienteRead(BaseModel):
    id_paciente: int
    nombre: str
    apellido: str
    fecha_nacimiento: date
    edad: Optional[int]
    peso_kg: Optional[float]

    telefono: Optional[str]
    email: Optional[EmailStr]
    direccion: Optional[str]
    ocupacion: Optional[str]

    numero_hijos: Optional[int]
    tipo_parto: Optional[str]

    tipo_identificacion: str
    numero_identificacion: str
    estado: str
    fecha_registro: datetime

    class Config:
        from_attributes = True
