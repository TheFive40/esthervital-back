from pydantic import BaseModel
from datetime import date
from typing import Optional

class TratamientoBase(BaseModel):
    id_paciente: int
    nombre_tratamiento: str
    tipo_tratamiento: str
    descripcion: Optional[str] = None
    estado: str
    fecha_inicio: date
    fecha_fin: Optional[date] = None


class TratamientoCreate(TratamientoBase):
    pass


class TratamientoUpdate(BaseModel):
    nombre_tratamiento: Optional[str]
    tipo_tratamiento: Optional[str]
    descripcion: Optional[str]
    estado: Optional[str]
    fecha_inicio: Optional[date]
    fecha_fin: Optional[date]


class TratamientoResponse(TratamientoBase):
    id_tratamiento: int

    class Config:
        from_attributes = True
