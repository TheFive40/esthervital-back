from pydantic import BaseModel
from typing import Optional, List
from datetime import datetime

class HistorialCreate(BaseModel):
    id_paciente: int
    motivo_consulta: Optional[str]
    diagnostico: Optional[str]
    tratamiento: Optional[str]
    sesiones_planificadas: Optional[int]

class HistorialUpdate(BaseModel):
    motivo_consulta: Optional[str]
    diagnostico: Optional[str]
    tratamiento: Optional[str]
    sesiones_planificadas: Optional[int]

class HistorialRead(BaseModel):
    id_historial: int
    id_paciente: int
    motivo_consulta: Optional[str]
    diagnostico: Optional[str]
    tratamiento: Optional[str]
    sesiones_planificadas: Optional[int]
    fecha_ingreso: datetime

    class Config:
        from_attributes = True

class DocumentoCreate(BaseModel):
    id_historial: int
    tipo_documento: str
    url_archivo: str
    descripcion: Optional[str]

class DocumentoRead(BaseModel):
    id_documento: int
    id_historial: int
    tipo_documento: str
    url_archivo: str
    descripcion: Optional[str]
    fecha_subida: datetime

    class Config:
        from_attributes = True
