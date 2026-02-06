from pydantic import BaseModel, EmailStr
from typing import Optional, List, Generic, TypeVar
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
    nombre: Optional[str] = None
    apellido: Optional[str] = None
    fecha_nacimiento: Optional[date] = None
    edad: Optional[int] = None
    peso_kg: Optional[float] = None

    telefono: Optional[str] = None
    email: Optional[EmailStr] = None
    direccion: Optional[str] = None
    ocupacion: Optional[str] = None

    numero_hijos: Optional[int] = None
    tipo_parto: Optional[str] = None

    tipo_identificacion: Optional[str] = None
    numero_identificacion: Optional[str] = None
    estado: Optional[str] = None

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


class PaginatedPacientesResponse(BaseModel):
    """Response model for paginated patients list"""
    data: List[PacienteRead]
    total: int
    page: int
    limit: int
    total_pages: int

    class Config:
        from_attributes = True
