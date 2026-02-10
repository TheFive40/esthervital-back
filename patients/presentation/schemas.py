"""
Schemas seguros para Pacientes con validación completa
Protección contra XSS, SQL Injection, datos inválidos
"""

from pydantic import BaseModel, EmailStr, validator
from typing import Optional, List
from datetime import date, datetime

from security.InputValidator import InputValidator


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


    @validator('nombre', 'apellido')
    def validate_name(cls, v):
        """
        Validar y sanitizar nombres

        Protección contra:
        - XSS: <script>alert('hack')</script>
        - SQL Injection: Robert'); DROP TABLE pacientes;--
        - Caracteres no válidos
        """
        if not v:
            raise ValueError("Campo requerido")

        # Validar contra inyecciones
        try:
            InputValidator.validate_xss(v)
            InputValidator.validate_sql_injection(v)
        except Exception as e:
            raise ValueError(f"Entrada inválida detectada: {str(e)}")

        # Sanitizar
        v = InputValidator.sanitize_string(v, allow_html=False, max_length=100)

        # Validar longitud después de sanitizar
        if len(v) < 2:
            raise ValueError("Debe tener al menos 2 caracteres")
        if len(v) > 100:
            raise ValueError("Debe tener máximo 100 caracteres")

        # Validar solo letras, espacios y acentos
        import re
        if not re.match(r'^[a-zA-ZáéíóúñÁÉÍÓÚÑ\s]+$', v):
            raise ValueError("Solo se permiten letras y espacios")

        return v.strip()

    @validator('email')
    def validate_email_format(cls, v):
        """
        Validar formato de email

        Protección contra:
        - Emails malformados
        - XSS en email
        """
        if v:
            v = v.lower().strip()

            # Validar XSS
            try:
                InputValidator.validate_xss(v)
            except Exception:
                raise ValueError("Email contiene caracteres no permitidos")

            # Validar formato
            if not InputValidator.validate_email(v):
                raise ValueError("Formato de email inválido")

            # Longitud máxima
            if len(v) > 150:
                raise ValueError("Email demasiado largo")

        return v

    @validator('telefono')
    def validate_phone_format(cls, v):
        """
        Validar formato de teléfono colombiano

        Formatos aceptados:
        - 3001234567
        - 300 123 4567
        - 300-123-4567
        - +57 300 123 4567
        """
        if v:
            # Sanitizar
            v = InputValidator.sanitize_string(v, allow_html=False, max_length=20)

            # Limpiar formato
            import re
            clean = re.sub(r'[\s\-\(\)]', '', v)

            # Remover +57 si existe
            if clean.startswith('+57'):
                clean = clean[3:]
            elif clean.startswith('57'):
                clean = clean[2:]

            # Validar formato colombiano (10 dígitos, empieza con 3)
            if not re.match(r'^3\d{9}$', clean):
                raise ValueError(
                    "Teléfono inválido. Formato esperado: 300-123-4567 o 3001234567"
                )

            return clean
        return v

    @validator('direccion')
    def validate_address(cls, v):
        """
        Validar y sanitizar dirección

        Protección contra:
        - XSS: <script>...</script>
        - Path traversal: ../../../etc/passwd
        """
        if v:
            # Validar inyecciones
            try:
                InputValidator.validate_xss(v)
                InputValidator.validate_path_traversal(v)
            except Exception as e:
                raise ValueError(f"Dirección contiene caracteres no permitidos: {str(e)}")

            # Sanitizar
            v = InputValidator.sanitize_string(v, allow_html=False, max_length=200)

            # Validar longitud
            if len(v) > 200:
                raise ValueError("Dirección demasiado larga (máximo 200 caracteres)")

            if len(v) < 5:
                raise ValueError("Dirección demasiado corta (mínimo 5 caracteres)")

            return v.strip()
        return v

    @validator('ocupacion')
    def validate_occupation(cls, v):
        """Validar y sanitizar ocupación"""
        if v:
            # Validar XSS
            try:
                InputValidator.validate_xss(v)
            except Exception:
                raise ValueError("Ocupación contiene caracteres no permitidos")

            v = InputValidator.sanitize_string(v, allow_html=False, max_length=100)

            if len(v) > 100:
                raise ValueError("Ocupación demasiado larga (máximo 100 caracteres)")

            return v.strip()
        return v

    @validator('numero_identificacion')
    def validate_identification(cls, v):
        """
        Validar número de identificación

        Protección contra:
        - SQL Injection
        - XSS
        - Formatos inválidos
        """
        if not v:
            raise ValueError("Número de identificación requerido")

        # Validar inyecciones
        try:
            InputValidator.validate_sql_injection(v)
            InputValidator.validate_xss(v)
        except Exception as e:
            raise ValueError(f"Número de identificación inválido: {str(e)}")

        # Sanitizar
        v = InputValidator.sanitize_string(v, allow_html=False, max_length=20).strip()

        # Validar formato (solo números, letras y guiones)
        import re
        if not re.match(r'^[0-9A-Za-z-]+$', v):
            raise ValueError(
                "Número de identificación inválido (solo números, letras y guiones permitidos)"
            )

        # Validar longitud
        if len(v) < 5:
            raise ValueError("Número de identificación demasiado corto (mínimo 5 caracteres)")
        if len(v) > 20:
            raise ValueError("Número de identificación demasiado largo (máximo 20 caracteres)")

        return v

    @validator('tipo_identificacion')
    def validate_identification_type(cls, v):
        """
        Validar tipo de identificación

        Tipos válidos:
        - CC: Cédula de Ciudadanía
        - TI: Tarjeta de Identidad
        - CE: Cédula de Extranjería
        - PA: Pasaporte
        - RC: Registro Civil
        """
        if not v:
            raise ValueError("Tipo de identificación requerido")

        valid_types = ["CC", "TI", "CE", "PA", "RC"]
        v = v.upper().strip()

        if v not in valid_types:
            raise ValueError(
                f"Tipo de identificación inválido. Válidos: {', '.join(valid_types)}"
            )

        return v

    @validator('tipo_parto')
    def validate_birth_type(cls, v):
        """Validar tipo de parto"""
        if v:
            valid_types = ["Natural", "Cesárea", "N/A"]
            v = v.strip()

            if v not in valid_types:
                raise ValueError(
                    f"Tipo de parto inválido. Válidos: {', '.join(valid_types)}"
                )
        return v

    @validator('peso_kg')
    def validate_weight(cls, v):
        """
        Validar peso

        Rango válido: 20-300 kg
        """
        if v is not None:
            if not isinstance(v, (int, float)):
                raise ValueError("Peso debe ser un número")

            if v < 20 or v > 300:
                raise ValueError("Peso fuera de rango válido (20-300 kg)")

            # Redondear a 2 decimales
            v = round(float(v), 2)

        return v

    @validator('numero_hijos')
    def validate_children(cls, v):
        """
        Validar número de hijos

        Rango válido: 0-20
        """
        if v is not None:
            if not isinstance(v, int):
                raise ValueError("Número de hijos debe ser un entero")

            if v < 0 or v > 20:
                raise ValueError("Número de hijos fuera de rango válido (0-20)")

        return v

    @validator('edad')
    def validate_age(cls, v, values):
        """
        Validar edad o calcularla automáticamente

        Si no se proporciona, se calcula desde fecha_nacimiento
        Rango válido: 0-120 años
        """
        if v is not None:
            if not isinstance(v, int):
                raise ValueError("Edad debe ser un entero")

            if v < 0 or v > 120:
                raise ValueError("Edad fuera de rango válido (0-120)")

        elif 'fecha_nacimiento' in values and values['fecha_nacimiento']:
            # Calcular edad automáticamente
            from datetime import date
            today = date.today()
            birth_date = values['fecha_nacimiento']

            v = today.year - birth_date.year - (
                    (today.month, today.day) < (birth_date.month, birth_date.day)
            )

            # Validar que la fecha de nacimiento no sea futura
            if v < 0:
                raise ValueError("Fecha de nacimiento no puede ser futura")

        return v

    @validator('fecha_nacimiento')
    def validate_birth_date(cls, v):
        """
        Validar fecha de nacimiento

        No puede ser futura ni muy antigua (>150 años)
        """
        if v:
            from datetime import date
            today = date.today()

            # No puede ser futura
            if v > today:
                raise ValueError("Fecha de nacimiento no puede ser futura")

            # No puede ser muy antigua (>150 años)
            age = today.year - v.year
            if age > 150:
                raise ValueError("Fecha de nacimiento no puede ser mayor a 150 años atrás")

        return v

    @validator('estado')
    def validate_status(cls, v):
        """Validar estado"""
        if v:
            valid_states = ["Activo", "Inactivo"]
            if v not in valid_states:
                raise ValueError(
                    f"Estado inválido. Válidos: {', '.join(valid_states)}"
                )
        return v or "Activo"


class PacienteUpdate(BaseModel):
    """
    Schema para actualización (todos los campos opcionales)

    Aplica las mismas validaciones que PacienteCreate
    """
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

    # ✅ REUTILIZAR VALIDADORES de PacienteCreate
    _validate_name = validator('nombre', 'apellido', allow_reuse=True)(
        PacienteCreate.validate_name.__func__
    )
    _validate_email = validator('email', allow_reuse=True)(
        PacienteCreate.validate_email_format.__func__
    )
    _validate_phone = validator('telefono', allow_reuse=True)(
        PacienteCreate.validate_phone_format.__func__
    )
    _validate_address = validator('direccion', allow_reuse=True)(
        PacienteCreate.validate_address.__func__
    )
    _validate_occupation = validator('ocupacion', allow_reuse=True)(
        PacienteCreate.validate_occupation.__func__
    )
    _validate_identification = validator('numero_identificacion', allow_reuse=True)(
        PacienteCreate.validate_identification.__func__
    )
    _validate_identification_type = validator('tipo_identificacion', allow_reuse=True)(
        PacienteCreate.validate_identification_type.__func__
    )
    _validate_birth_type = validator('tipo_parto', allow_reuse=True)(
        PacienteCreate.validate_birth_type.__func__
    )
    _validate_weight = validator('peso_kg', allow_reuse=True)(
        PacienteCreate.validate_weight.__func__
    )
    _validate_children = validator('numero_hijos', allow_reuse=True)(
        PacienteCreate.validate_children.__func__
    )
    _validate_age = validator('edad', allow_reuse=True)(
        PacienteCreate.validate_age.__func__
    )
    _validate_birth_date = validator('fecha_nacimiento', allow_reuse=True)(
        PacienteCreate.validate_birth_date.__func__
    )
    _validate_status = validator('estado', allow_reuse=True)(
        PacienteCreate.validate_status.__func__
    )


class PacienteRead(BaseModel):
    """
    Schema para lectura (sin validación de entrada)
    Los datos ya están en la BD y fueron validados al insertar
    """
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