from pydantic import BaseModel
from datetime import date, datetime
from typing import Optional, List

class TratamientoCreate(BaseModel):
    id_paciente: int
    id_usuario: int
    nombre_tratamiento: str
    tipo_tratamiento: str
    descripcion: Optional[str] = None
    sesiones_planificadas: int = 1
    estado: str = "Activo"
    fecha_inicio: date


class TratamientoUpdate(BaseModel):
    id_paciente: Optional[int] = None
    id_usuario: Optional[int] = None
    nombre_tratamiento: Optional[str] = None
    tipo_tratamiento: Optional[str] = None
    descripcion: Optional[str] = None
    sesiones_planificadas: Optional[int] = None
    estado: Optional[str] = None
    fecha_inicio: Optional[date] = None
    fecha_fin: Optional[date] = None


class TratamientoBase(BaseModel):
    id_tratamiento: int
    id_paciente: int
    id_usuario: int
    nombre_tratamiento: str
    tipo_tratamiento: str
    descripcion: Optional[str]
    sesiones_planificadas: int
    estado: str
    fecha_inicio: date
    fecha_fin: Optional[date]
    fecha_creacion: datetime

    class Config:
        from_attributes = True


class TratamientoResponse(TratamientoBase):
    # Información adicional calculada
    sesiones_completadas: int = 0
    paciente_nombre: Optional[str] = None
    usuario_nombre: Optional[str] = None


class TratamientoDetallado(TratamientoBase):
    sesiones_completadas: int
    paciente_nombre: str
    usuario_nombre: str
    sesiones: List['SesionResponse'] = []

    class Config:
        from_attributes = True


class SesionCreate(BaseModel):
    id_tratamiento: int
    numero_sesion: int
    fecha_sesion: datetime
    notas: Optional[str] = None
    estado: str = "Completada"
    abdomen_alto_cm: Optional[float] = None
    cintura_cm: Optional[float] = None
    abdomen_bajo_cm: Optional[float] = None
    cadera_cm: Optional[float] = None
    peso_kg: Optional[float] = None
    zonas_trabajadas: Optional[str] = None


class SesionUpdate(BaseModel):
    numero_sesion: Optional[int] = None
    fecha_sesion: Optional[datetime] = None
    notas: Optional[str] = None
    estado: Optional[str] = None
    abdomen_alto_cm: Optional[float] = None
    cintura_cm: Optional[float] = None
    abdomen_bajo_cm: Optional[float] = None
    cadera_cm: Optional[float] = None
    peso_kg: Optional[float] = None
    zonas_trabajadas: Optional[str] = None


class SesionResponse(BaseModel):
    id_sesion: int
    id_tratamiento: int
    numero_sesion: int
    fecha_sesion: datetime
    notas: Optional[str]
    estado: str
    abdomen_alto_cm: Optional[float]
    cintura_cm: Optional[float]
    abdomen_bajo_cm: Optional[float]
    cadera_cm: Optional[float]
    peso_kg: Optional[float]
    zonas_trabajadas: Optional[str]
    fecha_registro: datetime
    imagenes: List['ImagenResponse'] = []

    class Config:
        from_attributes = True


class ImagenCreate(BaseModel):
    id_sesion: int
    url_imagen: str
    descripcion: Optional[str] = None
    tipo_imagen: Optional[str] = None


class ImagenUpdate(BaseModel):
    url_imagen: Optional[str] = None
    descripcion: Optional[str] = None
    tipo_imagen: Optional[str] = None


class ImagenResponse(BaseModel):
    id_imagen: int
    id_sesion: int
    url_imagen: str
    descripcion: Optional[str]
    tipo_imagen: Optional[str]
    fecha_subida: datetime

    class Config:
        from_attributes = True


TratamientoDetallado.model_rebuild()
SesionResponse.model_rebuild()