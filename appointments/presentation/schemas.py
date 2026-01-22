from pydantic import BaseModel
from typing import Optional
from datetime import date, datetime

class CitaCreate(BaseModel):
    id_paciente: int
    numero_cita: int
    fecha: date
    procedimiento: str

    abdomen_alto_cm: Optional[float]
    cintura_cm: Optional[float]
    abdomen_bajo_cm: Optional[float]
    cadera_cm: Optional[float]

    firma: Optional[str]
    estado: Optional[str] = "Programada"

class CitaUpdate(BaseModel):
    numero_cita: Optional[int]
    fecha: Optional[date]
    procedimiento: Optional[str]

    abdomen_alto_cm: Optional[float]
    cintura_cm: Optional[float]
    abdomen_bajo_cm: Optional[float]
    cadera_cm: Optional[float]

    firma: Optional[str]
    estado: Optional[str]

class CitaRead(BaseModel):
    id_cita: int
    id_paciente: int
    numero_cita: int
    fecha: date
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
