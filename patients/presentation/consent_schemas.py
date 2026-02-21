"""
Schemas Pydantic para Consentimientos de Pacientes
"""
from pydantic import BaseModel, validator
from typing import Optional, List
from datetime import datetime

from security.InputValidator import InputValidator

# Tipos de consentimiento aceptados en el sistema
TIPOS_CONSENTIMIENTO_VALIDOS = [
    "Consentimiento General",
    "Consentimiento de Tratamiento",
    "Consentimiento de Procedimiento Estético",
    "Consentimiento de Fotografía",
    "Consentimiento de Datos Personales",
    "Otro",
]

# Tipos de archivo permitidos
TIPOS_ARCHIVO_PERMITIDOS = [
    "application/pdf",
    "image/jpeg",
    "image/jpg",
    "image/png",
    "image/webp",
]


class ConsentimientoCreate(BaseModel):
    """
    Schema para registrar un consentimiento.
    El frontend sube primero el archivo a Supabase Storage y envía la URL resultante.
    """
    id_paciente: int
    tipo_consentimiento: str
    url_archivo: str
    nombre_archivo: str
    tipo_archivo: Optional[str] = None
    observaciones: Optional[str] = None

    @validator("id_paciente")
    def validate_id_paciente(cls, v):
        if not isinstance(v, int) or v < 1:
            raise ValueError("ID de paciente inválido")
        return v

    @validator("tipo_consentimiento")
    def validate_tipo(cls, v):
        if not v:
            raise ValueError("El tipo de consentimiento es requerido")
        v = v.strip()
        if v not in TIPOS_CONSENTIMIENTO_VALIDOS:
            raise ValueError(
                f"Tipo inválido. Opciones: {', '.join(TIPOS_CONSENTIMIENTO_VALIDOS)}"
            )
        return v

    @validator("url_archivo")
    def validate_url(cls, v):
        if not v:
            raise ValueError("La URL del archivo es requerida")
        try:
            InputValidator.validate_path_traversal(v)
            InputValidator.validate_xss(v)
        except Exception:
            raise ValueError("URL contiene caracteres no permitidos")

        import re
        if not re.match(r"^(https?://|/|storage/)", v):
            raise ValueError("URL debe comenzar con https://, http://, / o storage/")
        if re.match(r"^(javascript|data|vbscript):", v, re.IGNORECASE):
            raise ValueError("Protocolo de URL no permitido")
        return InputValidator.sanitize_string(v, allow_html=False, max_length=500)

    @validator("nombre_archivo")
    def validate_nombre_archivo(cls, v):
        if not v:
            raise ValueError("El nombre del archivo es requerido")
        try:
            InputValidator.validate_xss(v)
            InputValidator.validate_path_traversal(v)
        except Exception:
            raise ValueError("Nombre de archivo contiene caracteres no permitidos")
        return InputValidator.sanitize_string(v, allow_html=False, max_length=255).strip()

    @validator("tipo_archivo")
    def validate_tipo_archivo(cls, v):
        if v and v not in TIPOS_ARCHIVO_PERMITIDOS:
            raise ValueError(
                f"Tipo de archivo no permitido. Permitidos: {', '.join(TIPOS_ARCHIVO_PERMITIDOS)}"
            )
        return v

    @validator("observaciones")
    def validate_observaciones(cls, v):
        if v:
            try:
                InputValidator.validate_xss(v)
                InputValidator.validate_sql_injection(v, strict=False)
            except Exception:
                raise ValueError("Las observaciones contienen caracteres no permitidos")
            v = InputValidator.sanitize_string(v, allow_html=False, max_length=1000)
            if len(v) > 1000:
                raise ValueError("Observaciones demasiado largas (máximo 1000 caracteres)")
        return v


class ConsentimientoUpdate(BaseModel):
    """Solo se permite actualizar las observaciones después de crear el registro."""
    observaciones: Optional[str] = None

    @validator("observaciones")
    def validate_observaciones(cls, v):
        if v:
            try:
                InputValidator.validate_xss(v)
                InputValidator.validate_sql_injection(v, strict=False)
            except Exception:
                raise ValueError("Las observaciones contienen caracteres no permitidos")
            v = InputValidator.sanitize_string(v, allow_html=False, max_length=1000)
        return v


class ConsentimientoRead(BaseModel):
    id_consentimiento: int
    id_paciente: int
    tipo_consentimiento: str
    url_archivo: str
    nombre_archivo: str
    tipo_archivo: Optional[str]
    observaciones: Optional[str]
    activo: bool
    fecha_subida: datetime
    subido_por: Optional[int]

    class Config:
        from_attributes = True


class ConsentimientoResumen(BaseModel):
    """Vista resumida para listar dentro del perfil de paciente."""
    id_consentimiento: int
    tipo_consentimiento: str
    nombre_archivo: str
    tipo_archivo: Optional[str]
    fecha_subida: datetime
    url_archivo: str

    class Config:
        from_attributes = True


class TiposConsentimientoResponse(BaseModel):
    tipos: List[str]