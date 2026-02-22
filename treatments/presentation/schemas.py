from pydantic import BaseModel, validator
from decimal import Decimal
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
    # ── Costo (opcional al crear, pero recomendado) ──────────────────
    costo_total: Optional[Decimal] = None
    notas_costo: Optional[str] = None  # Descripción del costo pactado

    @validator("costo_total")
    def validate_costo(cls, v):
        if v is not None:
            if v <= 0:
                raise ValueError("El costo total debe ser mayor a cero.")
            if v > Decimal("999_999_999.99"):
                raise ValueError("El costo total supera el límite permitido.")
            return round(v, 2)
        return v


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


# ── Resumen financiero embebido en respuestas ─────────────────────────────────
class ResumenFinancieroEmbedido(BaseModel):
    id_costo: int
    costo_total: float
    total_abonado: float
    saldo_pendiente: float
    estado_pago: str   # "Pendiente" | "Abono parcial" | "Pagado"
    cantidad_abonos: int

    class Config:
        from_attributes = True


class TratamientoResponse(TratamientoBase):
    sesiones_completadas: int = 0
    paciente_nombre: Optional[str] = None
    usuario_nombre: Optional[str] = None
    # Incluir resumen financiero si existe costo registrado
    financiero: Optional[ResumenFinancieroEmbedido] = None


class TratamientoDetallado(TratamientoBase):
    sesiones_completadas: int
    paciente_nombre: str
    usuario_nombre: str
    sesiones: List['SesionResponse'] = []
    # Incluir resumen financiero completo
    financiero: Optional[ResumenFinancieroEmbedido] = None

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
    tipo_cuerpo: Optional[str] = None


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
    tipo_cuerpo: Optional[str] = None


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
    tipo_cuerpo: Optional[str]
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


class PaginatedTratamientosResponse(BaseModel):
    """Response model for paginated treatments list"""
    data: List[TratamientoResponse]
    total: int
    page: int
    limit: int
    total_pages: int

    class Config:
        from_attributes = True


TratamientoDetallado.model_rebuild()
SesionResponse.model_rebuild()