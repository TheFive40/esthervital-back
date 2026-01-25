from pydantic import BaseModel
from typing import Optional
from datetime import date, datetime

class CitaCreate(BaseModel):
    id_paciente: int
    numero_cita: int
    fecha: date
    hora: Optional[str] = "09:00"
    procedimiento: str

    abdomen_alto_cm: Optional[float] = None
    cintura_cm: Optional[float] = None
    abdomen_bajo_cm: Optional[float] = None
    cadera_cm: Optional[float] = None

    firma: Optional[str] = None
    estado: Optional[str] = "Programada"

class CitaUpdate(BaseModel):
    numero_cita: Optional[int] = None
    fecha: Optional[date] = None
    hora: Optional[str] = None
    procedimiento: Optional[str] = None

    abdomen_alto_cm: Optional[float] = None
    cintura_cm: Optional[float] = None
    abdomen_bajo_cm: Optional[float] = None
    cadera_cm: Optional[float] = None

    firma: Optional[str] = None
    estado: Optional[str]

class CitaRead(BaseModel):
    id_cita: int
    id_paciente: int
    numero_cita: int
    fecha: date
    hora: Optional[str]
    procedimiento: str

    abdomen_alto_cm: Optional[float]
    cintura_cm: Optional[float]
    abdomen_bajo_cm: Optional[float]
    cadera_cm: Optional[float]

    firma: Optional[str]
    estado: str
    fecha_registro: datetime

    class Config:
        from_attributes = True
